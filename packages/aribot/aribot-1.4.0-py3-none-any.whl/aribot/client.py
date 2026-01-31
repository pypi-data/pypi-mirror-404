"""Aribot API Client - by Aristiun & Ayurak"""

from typing import Optional

from .http import HttpClient
from .threat_modeling import ThreatModelingAPI
from .compliance import ComplianceAPI
from .cloud import CloudSecurityAPI
from .pipeline import PipelineAPI
from .redteam import RedTeamAPI
from .digital_twin import DigitalTwinAPI
from .economics import EconomicsAPI
from .ai import AIAPI
from .sbom import SBOMAPI
from .dashboard import DashboardAPI
from .finops import FinOpsAPI
from .marketplace import MarketplaceAPI
from .api_keys import APIKeysAPI


class Aribot:
    """
    Aribot Security Platform client by Aristiun & Ayurak.

    Provides access to threat modeling, compliance scanning,
    cloud security, and pipeline security APIs.

    Usage:
        from aribot import Aribot

        client = Aribot(api_key="your_api_key")

        # Threat modeling
        result = client.threat_modeling.analyze_diagram("architecture.png")
        threats = client.threat_modeling.get_threats(result['diagram_id'])

        # Compliance scanning
        compliance = client.compliance.scan(diagram_id, standards=["ISO27001"])

        # Cloud security
        scan = client.cloud.scan(project_id="aws-123456")

        # Pipeline security
        result = client.pipeline.scan(project_id, commit_sha="abc123")
    """

    DEFAULT_BASE_URL = "https://api.aribot.ayurak.com/aribot-api"

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: int = 30
    ):
        """
        Initialize Aribot client.

        Args:
            api_key: Your Aribot API key
            base_url: API base URL (default: production)
            timeout: Request timeout in seconds
        """
        self._http = HttpClient(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout
        )

        self.threat_modeling = ThreatModelingAPI(self._http)
        self.compliance = ComplianceAPI(self._http)
        self.cloud = CloudSecurityAPI(self._http)
        self.pipeline = PipelineAPI(self._http)
        self.redteam = RedTeamAPI(self._http)
        self.digital_twin = DigitalTwinAPI(self._http)
        self.economics = EconomicsAPI(self._http)
        self.ai = AIAPI(self._http)
        self.sbom = SBOMAPI(self._http)
        self.dashboard = DashboardAPI(self._http)
        self.finops = FinOpsAPI(self._http)
        self.marketplace = MarketplaceAPI(self._http)
        self.api_keys = APIKeysAPI(self._http)

    @property
    def api_key(self) -> str:
        """Get the current API key"""
        return self._http.api_key

    @property
    def base_url(self) -> str:
        """Get the current base URL"""
        return self._http.base_url

    def health(self) -> dict:
        """
        Check API health status.

        Returns:
            Health status with version info
        """
        return self._http.get('/health/')

    def me(self) -> dict:
        """
        Get current user/organization info.

        Returns:
            User profile with subscription details
        """
        return self._http.get('/v1/users/me/')

    def usage(self, period: str = "month") -> dict:
        """
        Get API usage statistics.

        Args:
            period: Time period (day, week, month)

        Returns:
            Usage stats with limits and remaining quota
        """
        return self._http.get('/v1/usage/', params={'period': period})
