/* FBS experiment selection (observe-only scaffold). */
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

static inline int fbs_lab_target_matches(const char *imsi)
{
    const char *enabled = getenv("FBS_LAB_REJECT_ENABLED");
    const char *target = getenv("FBS_LAB_TARGET_IMSI");

    if (!enabled || strcmp(enabled, "1") != 0)
        return 0;

    if (!imsi || !target || strlen(target) != 15)
        return 0;

    return strcmp(imsi, target) == 0;
}

#endif /* FBS_LAB_SCENARIO_H */
