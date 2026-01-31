"""API Keys API - API key management"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class APIKeysAPI:
    """
    API key management - list, create, and revoke keys.

    Usage:
        client = Aribot(api_key)
        keys = client.api_keys.list()
        client.api_keys.revoke(key_id)
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        """
        List API keys.

        Returns:
            List of API keys with metadata (keys are partially masked)
        """
        result = self._http.get('/v2/api-keys/')

        if isinstance(result, list):
            return result
        return result.get('results', result.get('keys', []))

    def revoke(self, key_id: str) -> Dict[str, Any]:
        """
        Revoke an API key.

        Args:
            key_id: API key ID to revoke

        Returns:
            Confirmation of revocation

        Example:
            client.api_keys.revoke("key-abc123")
        """
        return self._http.post(f'/v2/api-keys/{key_id}/revoke/')
