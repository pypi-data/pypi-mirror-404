"""
Aribot Security Platform SDK by Aristiun & Ayurak

Threat modeling, compliance, and cloud security APIs.

Usage:
    from aribot import Aribot

    client = Aribot(api_key="your_api_key")

    # Upload and analyze diagram
    result = client.threat_modeling.analyze_diagram("architecture.png")

    # Run compliance scan
    scan = client.compliance.scan(diagram_id, standards=["ISO27001", "SOC2"])

    # Cloud security scan
    findings = client.cloud.scan(project_id)
"""

from .client import Aribot
from .exceptions import (
    AribotError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)
from .redteam import RedTeamAPI
from .digital_twin import DigitalTwinAPI
from .economics import EconomicsAPI
from .ai import AIAPI
from .sbom import SBOMAPI
from .dashboard import DashboardAPI
from .finops import FinOpsAPI
from .marketplace import MarketplaceAPI
from .api_keys import APIKeysAPI

__version__ = "1.4.0"
__all__ = [
    "Aribot",
    "AribotError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "RedTeamAPI",
    "DigitalTwinAPI",
    "EconomicsAPI",
    "AIAPI",
    "SBOMAPI",
    "DashboardAPI",
    "FinOpsAPI",
    "MarketplaceAPI",
    "APIKeysAPI"
]
