#!/usr/bin/env python3
"""Add an observe-only 4-mode FBS scaffold to Open5GS v2.8 MME.

Run from the root of the Git working tree on Windows or Linux:
    py setup_fbs_bidding_modes.py

The script is idempotent and intentionally does NOT inject NAS rejects.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path.cwd()
MME = ROOT / "src" / "mme"
APP = MME / "app-init.c"
EMM = MME / "emm-sm.c"
LAB = ROOT / "lab"

HEADER = '''/* FBS experiment selection (observe-only scaffold). */
#ifndef FBS_LAB_SCENARIO_H
#define FBS_LAB_SCENARIO_H

#include <stdlib.h>
#include <string.h>

typedef enum {
    FBS_LAB_NORMAL,
    FBS_LAB_ATTACH_REJECT,
    FBS_LAB_TAU_REJECT,
    FBS_LAB_SERVICE_REJECT,
    FBS_LAB_INVALID
} fbs_lab_mode_t;

static inline fbs_lab_mode_t fbs_lab_mode(void)
{
    const char *value = getenv("FBS_LAB_MODE");

    if (!value || !*value || strcmp(value, "normal") == 0)
        return FBS_LAB_NORMAL;
    if (strcmp(value, "attach_reject") == 0)
        return FBS_LAB_ATTACH_REJECT;
    if (strcmp(value, "tau_reject") == 0)
        return FBS_LAB_TAU_REJECT;
    if (strcmp(value, "service_reject") == 0)
        return FBS_LAB_SERVICE_REJECT;
    return FBS_LAB_INVALID;
}

static inline const char *fbs_lab_mode_name(fbs_lab_mode_t mode)
{
    switch (mode) {
    case FBS_LAB_NORMAL: return "normal";
    case FBS_LAB_ATTACH_REJECT: return "attach_reject";
    case FBS_LAB_TAU_REJECT: return "tau_reject";
    case FBS_LAB_SERVICE_REJECT: return "service_reject";
    default: return "INVALID";
    }
}

#endif /* FBS_LAB_SCENARIO_H */
'''

README = '''# FBS bidding-down scenario scaffold (observe-only)

This folder provides a **mode selector and NAS-request event logging only**.
It does **not** inject NAS Attach/TAU/Service Reject messages, and does not
change existing Open5GS EMM behavior. Use only in an authorized shielded lab.

Supported `FBS_LAB_MODE` values:

- `normal` (default)
- `attach_reject` (observes `Attach Request`)
- `tau_reject` (observes `Tracking Area Update Request`)
- `service_reject` (observes `Service Request`)

Each mode starts the same MME binary. Invalid mode names cause startup to fail.
To configure the lab's systemd service, copy `scenario.env.example` to
`scenario.env` on the test machine and point the service's
`EnvironmentFile` directive at the copy. Restart the service after edits.

The observations are added to select paths in `src/mme/emm-sm.c`; they are
not a complete protocol trace. Compare with NAS PCAP for verification.
'''

IGNORE = '''# Private site-specific inputs and runtime output
/mme.yaml
/mme.log
/scenario.env
'''


def replace_once(text: str, old: str, new: str, file: Path, count: int = 1) -> str:
    if new in text:
        print(f"[skip] {file.name}: already patched")
        return text
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"{file}: expected {count} occurrences of {old!r}, found {actual}; no changes written")
    return text.replace(old, new)


def read_file(file: Path):
    raw = file.read_bytes()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("utf-8").replace("\r\n", "\n"), eol


def put_file(file: Path, text: str, eol: str):
    file.write_bytes(text.replace("\n", eol).encode("utf-8"))


def main():
    if not APP.is_file() or not EMM.is_file() or not (ROOT / ".git").exists():
        sys.exit("ERROR: run this script from the Open5GS git repository root (the folder containing src/mme).")
    if not (ROOT / "src" / "mme" / "meson.build").exists():
        sys.exit("ERROR: expected Open5GS src/mme/meson.build")

    app, app_eol = read_file(APP)
    emm, emm_eol = read_file(EMM)

    app = replace_once(app,
        '#include "ogs-app.h"\n',
        '#include "ogs-app.h"\n#include "lab-scenario.h"\n', APP)
    app = replace_once(app,
        '    int rv;\n\n    ogs_sctp_init',
        '    int rv;\n'
        '    fbs_lab_mode_t mode = fbs_lab_mode();\n\n'
        '    if (mode == FBS_LAB_INVALID) {\n'
        '        ogs_error("[FBS] Invalid FBS_LAB_MODE; expected normal, attach_reject, tau_reject, or service_reject");\n'
        '        return OGS_ERROR;\n'
        '    }\n'
        '    ogs_info("[FBS] mode=%s; observe-only (no NAS reject override)",\n'
        '            fbs_lab_mode_name(mode));\n\n'
        '    ogs_sctp_init', APP)
    emm = replace_once(emm,
        '#include "mme-sm.h"\n',
        '#include "mme-sm.h"\n#include "lab-scenario.h"\n', EMM)
    # Observe established request-dispatch paths; do not modify control flow.
    observations = [
        ('ogs_info("[%s] Attach request", mme_ue->imsi_bcd);', 'FBS_LAB_ATTACH_REJECT', 'AttachRequest'),
        ('ogs_info("[%s] Tracking area update request", mme_ue->imsi_bcd);', 'FBS_LAB_TAU_REJECT', 'TAURequest'),
        ('ogs_info("[%s] Service request", mme_ue->imsi_bcd);', 'FBS_LAB_SERVICE_REJECT', 'ServiceRequest'),
    ]
    for original, mode, event in observations:
        amended = original + ('\n            if (fbs_lab_mode() == %s)\n'
                              '                ogs_info("[FBS] observed=%s; observe-only");' % (mode, event))
        emm = replace_once(emm, original, amended, EMM)

    LAB.mkdir(exist_ok=True)
    put_file(APP, app, app_eol)
    put_file(EMM, emm, emm_eol)
    (MME / "lab-scenario.h").write_text(HEADER, encoding="utf-8", newline="\n")
    (LAB / "README.md").write_text(README, encoding="utf-8", newline="\n")
    (LAB / ".gitignore").write_text(IGNORE, encoding="utf-8", newline="\n")
    (LAB / "scenario.env.example").write_text("FBS_LAB_MODE=normal\n", encoding="utf-8", newline="\n")
    print("[ok] FBS observe-only mode selector and request logging installed.")
    print("[next] Review: git diff -- src/mme/app-init.c src/mme/emm-sm.c")
    print("[next] Commit + push on Windows; pull + ninja -C build -j4 on PC6.")


if __name__ == "__main__":
    main()
