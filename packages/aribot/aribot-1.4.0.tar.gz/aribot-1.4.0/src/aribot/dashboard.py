"""Dashboard API - Overview, recent activity, and risk summary"""

from typing import Optional, Dict, Any

from .http import HttpClient


class DashboardAPI:
    """
    Dashboard overview, recent activity, and risk summary.

    Usage:
        client = Aribot(api_key)
        overview = client.dashboard.get_overview()
        activity = client.dashboard.get_recent_activity()
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_overview(self) -> Dict[str, Any]:
        """
        Get dashboard overview with key metrics.

        Returns:
            Overview with threat counts, compliance scores, and summaries
        """
        return self._http.get('/v2/dashboard/overview/')

    def get_recent_activity(
        self,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get recent activity feed.

        Args:
            limit: Maximum number of activity items

        Returns:
            Recent activity items with timestamps and details

        Example:
            activity = client.dashboard.get_recent_activity(limit=10)
            for item in activity.get('items', []):
                print(f"{item['timestamp']}: {item['description']}")
        """
        params = {'limit': limit}
        return self._http.get('/v2/dashboard/recent/', params=params)

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get risk summary across all projects.

        Returns:
            Risk summary with scores, trends, and top risks
        """
        return self._http.get('/v2/dashboard/risk/')
