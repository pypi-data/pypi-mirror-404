"""Economics API for cost analysis and market intelligence"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class EconomicsAPI:
    """
    Economics API for cost analysis and market intelligence.

    Usage:
        client = Aribot(api_key)
        dashboard = client.economics.get_dashboard()
        cost = client.economics.get_diagram_cost_analysis(diagram_id)
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_dashboard(self, period: str = 'month') -> Dict[str, Any]:
        """
        Get economics dashboard with cost metrics.

        Args:
            period: Time period (day, week, month, quarter, year)

        Returns:
            Dashboard with cost metrics and ROI
        """
        params = {'period': period}
        return self._http.get('/v2/threat-modeling/economics/dashboard/', params=params)

    def get_diagram_cost_analysis(self, diagram_id: str) -> Dict[str, Any]:
        """
        Get cost analysis for a diagram.

        Args:
            diagram_id: Diagram UUID

        Returns:
            Cost analysis with breakdown by component
        """
        return self._http.get(f'/v2/threat-modeling/diagrams/{diagram_id}/cost-analysis/')

    def get_component_cost(self, component_id: str) -> Dict[str, Any]:
        """
        Get component cost intelligence.

        Args:
            component_id: Component UUID

        Returns:
            Component cost details
        """
        return self._http.get(f'/v2/threat-modeling/components/{component_id}/cost-intelligence/')

    def get_economic_intelligence(self) -> Dict[str, Any]:
        """
        Get economic intelligence dashboard (pricing, market trends).

        Returns:
            Economic intelligence data
        """
        return self._http.get('/v2/threat-modeling/economic-intelligence/pricing/')

    def get_market_intelligence(self) -> Dict[str, Any]:
        """
        Get market intelligence data.

        Returns:
            Market trends and competitive analysis
        """
        return self._http.get('/v2/threat-modeling/market-intelligence/')

    def calculate_roi(
        self,
        investment: float,
        risks_addressed: List[str],
        timeframe_days: int = 365
    ) -> Dict[str, Any]:
        """
        Calculate ROI for security investments.

        Args:
            investment: Investment amount
            risks_addressed: List of risk IDs addressed
            timeframe_days: Calculation timeframe in days

        Returns:
            ROI calculation result
        """
        return self._http.post(
            '/v2/threat-modeling/economics/calculate-roi/',
            json={
                'investment': investment,
                'risks_addressed': risks_addressed,
                'timeframe_days': timeframe_days
            }
        )
