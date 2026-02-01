# services/workflows/constants.py
from datetime import timedelta
from temporalio.common import RetryPolicy
# guardianhub/workflows/constants.py
from guardianhub.config.settings import settings
from guardianhub import get_logger
logger = get_logger(__name__)

# Rapid response for DB lookups
SHORT_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(seconds=60),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_attempts=5,  # Higher retries for transient DB flickers
    )
}

# Standard LLM reasoning and bundle assembly
MEDIUM_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(minutes=5),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(seconds=5),
        backoff_coefficient=2.0,
        maximum_attempts=3,
    )
}

# Heavy lifting: Agentic ReAct loops and complex audits
LONG_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(minutes=30),
    "heartbeat_timeout": timedelta(minutes=1),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(seconds=10),
        maximum_attempts=2,  # Fail fast if a 30-min audit hangs twice
    )
}

def get_activity_options(activity_name: str) -> dict:
    """Assigns timeouts based on the JSON configuration."""
    wf_config = settings.workflow_settings

    if activity_name in wf_config.short_activities:
        return SHORT_ACTIVITY_OPTIONS
    if activity_name in wf_config.medium_activities:
        return MEDIUM_ACTIVITY_OPTIONS
    if activity_name in wf_config.long_activities:
        return LONG_ACTIVITY_OPTIONS

    return SHORT_ACTIVITY_OPTIONS


# guardianhub/workflows/constants.py

def get_all_activities(activity_service_instance) -> list:
    activities = []
    mapping = settings.workflow_settings.activity_mapping
    cls = type(activity_service_instance)

    logger.info(f"🧬 [GET_ALL_ACTIVITIES] Final Forensic Scan: {cls.__name__}")

    for role_key, method_name in mapping.items():
        # 🟢 THE SECRET SAUCE: Look in the class's raw internal dictionary
        # This bypasses all Python 'lookup magic' and bound-method shadows
        raw_func_from_dict = cls.__dict__.get(method_name)

        logger.info(f"🕵️ [DICT_LOOKUP] Role: '{role_key}' | Method: '{method_name}' | Obj: {raw_func_from_dict}")

        if raw_func_from_dict:
            # Check if the decorator metadata is physically on the object in the dict
            if hasattr(raw_func_from_dict, "_defn"):
                # SUCCESS: We found the 'Blessing'.
                # Now get the bound version from the instance so 'self' is correct.
                bound_method = getattr(activity_service_instance, method_name)
                activities.append(bound_method)
                logger.info(f"✅ [VERIFIED] {method_name} is a blessed Temporal activity.")
            else:
                logger.warning(f"❌ [NAKED] {method_name} exists in dict but has no _defn attribute!")
        else:
            # Fallback for inherited methods (which don't show up in __dict__)
            inherited_func = getattr(cls, method_name, None)
            if inherited_func and hasattr(inherited_func, "_defn"):
                bound_method = getattr(activity_service_instance, method_name)
                activities.append(bound_method)
                logger.info(f"✅ [VERIFIED-INHERITED] {method_name} found via MRO.")
            else:
                logger.error(f"🚫 [NOT_FOUND] {method_name} is missing or undecorated.")

    return activities