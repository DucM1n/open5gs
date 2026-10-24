# FBS bidding-down scenario scaffold (observe-only)

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
