from langchain_core.runnables import RunnableConfig


def get_config_param(config: RunnableConfig, param_name: str) -> str:
    """
    Extract a required parameter from the agent's RunnableConfig.
    """
    value = config.get("configurable", {}).get(param_name)
    if value is None:
        raise ValueError(f"{param_name} needs to be provided to tool")
    return str(value)