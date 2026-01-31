"""Marketplace API - Templates, categories, and featured content"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class MarketplaceAPI:
    """
    Marketplace for templates, categories, and featured content.

    Usage:
        client = Aribot(api_key)
        templates = client.marketplace.get_templates()
        featured = client.marketplace.get_featured()
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_templates(
        self,
        category: str = None,
        search: str = None,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        List marketplace templates.

        Args:
            category: Filter by category
            search: Search in name/description
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of templates

        Example:
            templates = client.marketplace.get_templates(category="cloud")
            for t in templates.get('results', []):
                print(f"{t['name']}: {t['description']}")
        """
        params = {'page': page, 'limit': limit}
        if category:
            params['category'] = category
        if search:
            params['search'] = search

        return self._http.get('/v2/marketplace/templates/', params=params)

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        List marketplace categories.

        Returns:
            List of categories with template counts
        """
        result = self._http.get('/v2/marketplace/categories/')

        if isinstance(result, list):
            return result
        return result.get('results', result.get('categories', []))

    def get_featured(self) -> Dict[str, Any]:
        """
        Get featured marketplace content.

        Returns:
            Featured templates, collections, and highlights
        """
        return self._http.get('/v2/marketplace/featured/')
