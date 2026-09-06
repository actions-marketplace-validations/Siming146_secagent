"""SecAgent: Autonomous AI Security Agent for Open Source Ecosystems.

Powered by DeepSeek & LangGraph.
"""

__version__ = "0.1.0"
__author__ = "Open Source Security Agent Contributors"
__license__ = "Apache-2.0"

from secagent.config import Settings, get_settings
from secagent.state import AgentState, VulnerabilityCandidate, VerifiedVulnerability

__all__ = [
    "__version__",
    "Settings",
    "get_settings",
    "AgentState",
    "VulnerabilityCandidate",
    "VerifiedVulnerability",
]
