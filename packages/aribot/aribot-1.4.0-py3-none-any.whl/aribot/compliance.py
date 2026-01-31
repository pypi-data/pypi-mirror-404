"""Compliance API"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class ComplianceAPI:
    """
    Compliance scanning and reporting.

    Usage:
        client = Ayurak(api_key)
        result = client.compliance.scan(diagram_id, standards=["ISO27001"])
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def scan(
        self,
        diagram_id: str,
        standards: List[str] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Run compliance scan on a diagram.

        Args:
            diagram_id: Diagram UUID
            standards: Standards to check (ISO27001, SOC2, GDPR, HIPAA, PCI-DSS, NIST)
            include_recommendations: Include remediation recommendations

        Returns:
            Compliance scan results with gaps and recommendations

        Example:
            result = client.compliance.scan(
                diagram_id,
                standards=["ISO27001", "SOC2"],
                include_recommendations=True
            )
            print(f"Compliance score: {result['overall_score']}%")
        """
        data = {
            'include_recommendations': include_recommendations
        }
        if standards:
            data['standards'] = standards

        return self._http.post(
            f'/v2/compliances/diagram-compliance/{diagram_id}/scan/',
            json=data
        )

    def get_report(
        self,
        diagram_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Get compliance report for a diagram.

        Args:
            diagram_id: Diagram UUID
            format: Report format (json, pdf, html)

        Returns:
            Compliance report with detailed findings
        """
        params = {'format': format}
        return self._http.get(
            f'/v2/compliances/diagram-compliance/{diagram_id}/report/',
            params=params
        )

    def list_standards(self) -> List[Dict[str, Any]]:
        """
        List available compliance standards.

        Returns:
            List of standards with controls and requirements
        """
        result = self._http.get('/v2/compliances/standards/')

        if isinstance(result, list):
            return result
        return result.get('results', result.get('standards', []))

    def get_standard(self, standard_id: str) -> Dict[str, Any]:
        """
        Get details of a compliance standard.

        Args:
            standard_id: Standard identifier (e.g., "ISO27001", "SOC2")

        Returns:
            Standard with controls and requirements
        """
        return self._http.get(f'/v2/compliances/standards/{standard_id}/')

    def list_controls(
        self,
        standard_id: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        List controls for a compliance standard.

        Args:
            standard_id: Standard identifier
            category: Filter by control category

        Returns:
            List of controls with requirements
        """
        params = {}
        if category:
            params['category'] = category

        result = self._http.get(
            f'/v2/compliances/standards/{standard_id}/controls/',
            params=params
        )

        if isinstance(result, list):
            return result
        return result.get('results', result.get('controls', []))

    def get_gaps(
        self,
        diagram_id: str,
        standard_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get compliance gaps for a diagram.

        Args:
            diagram_id: Diagram UUID
            standard_id: Filter by standard

        Returns:
            List of compliance gaps with severity and recommendations
        """
        params = {}
        if standard_id:
            params['standard'] = standard_id

        result = self._http.get(
            f'/v2/compliances/diagram-compliance/{diagram_id}/gaps/',
            params=params
        )

        if isinstance(result, list):
            return result
        return result.get('results', result.get('gaps', []))

    def add_custom_standard(
        self,
        name: str,
        description: str,
        controls: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a custom compliance standard.

        Args:
            name: Standard name
            description: Standard description
            controls: List of controls with requirements

        Returns:
            Created standard

        Example:
            standard = client.compliance.add_custom_standard(
                name="Internal Security Policy",
                description="Company security requirements",
                controls=[
                    {
                        "id": "ISP-001",
                        "name": "Data Encryption",
                        "description": "All data must be encrypted at rest",
                        "severity": "high"
                    }
                ]
            )
        """
        data = {
            'name': name,
            'description': description,
            'controls': controls
        }

        return self._http.post('/v2/compliances/standards/', json=data)

    def dashboard(
        self,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get compliance dashboard metrics.

        Args:
            period: Time period (day, week, month, quarter)

        Returns:
            Dashboard with compliance scores, trends, and gaps
        """
        params = {'period': period}
        return self._http.get('/v2/compliances/dashboard/', params=params)
