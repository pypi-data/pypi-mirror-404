class AgentBootstrapError(Exception):
    """Base exception for agent bootstrap-related errors."""


class AgentNotBootstrapped(AgentBootstrapError):
    """Raised when an operation requires a bootstrapped agent, but the agent is not bootstrapped."""


class AgentAlreadyBootstrapped(AgentBootstrapError):
    """Raised when attempting to bootstrap an already bootstrapped agent."""
