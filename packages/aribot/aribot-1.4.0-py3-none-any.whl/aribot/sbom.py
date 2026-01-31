"""SBOM API - Software Bill of Materials document management"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class SBOMAPI:
    """
    SBOM document management and vulnerability scanning.

    Usage:
        client = Aribot(api_key)
        documents = client.sbom.list_documents()
        vulns = client.sbom.get_vulnerabilities(document_id)
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def list_documents(
        self,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        List SBOM documents.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of SBOM documents
        """
        params = {'page': page, 'limit': limit}
        return self._http.get('/v2/sbom/documents/', params=params)

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get SBOM document details.

        Args:
            document_id: Document UUID

        Returns:
            SBOM document with components and metadata
        """
        return self._http.get(f'/v2/sbom/documents/{document_id}/')

    def get_vulnerabilities(
        self,
        document_id: str,
        severity: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get vulnerabilities for an SBOM document.

        Args:
            document_id: Document UUID
            severity: Filter by severity (critical, high, medium, low)

        Returns:
            List of vulnerabilities with CVE details and remediation

        Example:
            vulns = client.sbom.get_vulnerabilities(
                document_id,
                severity="critical"
            )
            for v in vulns:
                print(f"[{v['severity']}] {v['cve_id']}: {v['title']}")
        """
        params = {}
        if severity:
            params['severity'] = severity

        result = self._http.get(
            f'/v2/sbom/documents/{document_id}/vulnerabilities/',
            params=params
        )

        if isinstance(result, list):
            return result
        return result.get('results', result.get('vulnerabilities', []))
