from agent_squad.types import AgentSquadConfig


def get_config() -> AgentSquadConfig:
    return AgentSquadConfig(
        USE_DEFAULT_AGENT_IF_NONE_IDENTIFIED=True,
        LOG_CLASSIFIER_OUTPUT=True,
        LOG_EXECUTION_TIMES=True,
        NO_SELECTED_AGENT_MESSAGE="No agent was selected.",
        GENERAL_ROUTING_ERROR_MSG_MESSAGE="Something went wrong.",
        MAX_MESSAGE_PAIRS_PER_AGENT=10
    )
