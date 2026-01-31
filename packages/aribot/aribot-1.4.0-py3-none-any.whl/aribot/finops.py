"""FinOps API - Cost optimization and recommendations"""

from typing import Optional, Dict, Any

from .http import HttpClient


class FinOpsAPI:
    """
    FinOps cost optimization, cost tracking, and recommendations.

    Usage:
        client = Aribot(api_key)
        recs = client.finops.get_recommendations()
        costs = client.finops.get_costs()
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_recommendations(
        self,
        category: str = None
    ) -> Dict[str, Any]:
        """
        Get cost optimization recommendations.

        Args:
            category: Filter by category (compute, storage, network, etc.)

        Returns:
            Recommendations with estimated savings

        Example:
            recs = client.finops.get_recommendations(category="compute")
            for r in recs.get('recommendations', []):
                print(f"{r['title']}: save ${r['estimated_savings']}/mo")
        """
        params = {}
        if category:
            params['category'] = category

        return self._http.get('/v2/finops/recommendations/', params=params)

    def get_costs(
        self,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get cost breakdown.

        Args:
            period: Time period (day, week, month, quarter)

        Returns:
            Cost breakdown by service, account, and category
        """
        params = {'period': period}
        return self._http.get('/v2/finops/costs/', params=params)

    def get_optimization(self) -> Dict[str, Any]:
        """
        Get optimization status and opportunities.

        Returns:
            Optimization metrics with potential savings and action items
        """
        return self._http.get('/v2/finops/optimization/')
