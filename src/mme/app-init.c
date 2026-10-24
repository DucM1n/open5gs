/*
 * Copyright (C) 2019 by Sukchan Lee <acetcom@gmail.com>
 *
 * This file is part of Open5GS.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include "ogs-sctp.h"
#include "ogs-app.h"
#include "lab-scenario.h"

int app_initialize(const char *const argv[])
{
    int rv;
    fbs_lab_mode_t mode = fbs_lab_mode();

    if (mode == FBS_LAB_INVALID) {
        ogs_error("[FBS] Invalid FBS_LAB_MODE; expected normal, attach_reject, tau_reject, or service_reject");
        return OGS_ERROR;
    }
    ogs_info("[FBS] mode=%s; observe-only (no NAS reject override)",
            fbs_lab_mode_name(mode));

    ogs_sctp_init(ogs_app()->usrsctp.udp_port);
    rv = mme_initialize();
    if (rv != OGS_OK) {
        ogs_error("Failed to initialize MME");
        return rv;
    }
    ogs_info("MME initialize...done");

    return OGS_OK;
}

void app_terminate(void)
{
    mme_terminate();
    ogs_sctp_final();
    ogs_info("MME terminate...done");
}

