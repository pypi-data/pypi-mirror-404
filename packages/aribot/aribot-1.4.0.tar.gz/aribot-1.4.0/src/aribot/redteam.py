"""Red Team API for attack simulation and threat intelligence"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class RedTeamAPI:
    """
    Red Team API for attack simulation and threat intelligence.

    Usage:
        client = Aribot(api_key)
        methodologies = client.redteam.get_methodologies()
        simulations = client.redteam.get_simulations()
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_methodologies(self) -> List[Dict[str, Any]]:
        """
        Get available red team methodologies (STRIDE, PASTA, MITRE ATT&CK, etc.)

        Returns:
            List of methodologies with their details
        """
        result = self._http.get('/v2/threat-modeling/threat-engine/red-team/methodologies/')
        return result.get('methodologies', [])

    def get_simulations(
        self,
        diagram_id: str = None,
        status: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get red team simulations (attack path simulations).

        Args:
            diagram_id: Filter by diagram
            status: Filter by status
            limit: Maximum results

        Returns:
            List of simulations
        """
        params = {}
        if diagram_id:
            params['diagram_id'] = diagram_id
        if status:
            params['status'] = status
        if limit:
            params['limit'] = limit

        result = self._http.get('/v2/threat-modeling/threat-engine/red-team/simulations/', params=params)
        return result.get('simulations', [])

    def get_intelligence(self) -> Dict[str, Any]:
        """
        Get threat intelligence summary.

        Returns:
            Threat intelligence metrics
        """
        return self._http.get('/v2/threat-modeling/threat-engine/threat-intelligence/')

    def generate_attack_paths(
        self,
        diagram_id: str,
        depth: str = 'comprehensive',
        include_remediations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate attack paths for a diagram.

        Args:
            diagram_id: Diagram UUID
            depth: Analysis depth (basic, comprehensive, detailed)
            include_remediations: Include remediation suggestions

        Returns:
            Simulation result with attack paths
        """
        return self._http.post(
            f'/v2/threat-modeling/diagrams/{diagram_id}/generate-attack-paths/',
            json={
                'depth': depth,
                'include_remediations': include_remediations
            }
        )

    def get_attack_paths(self, diagram_id: str) -> List[Dict[str, Any]]:
        """
        Get attack paths for a diagram.

        Args:
            diagram_id: Diagram UUID

        Returns:
            List of attack paths
        """
        result = self._http.get(f'/v2/threat-modeling/diagrams/{diagram_id}/attack-paths/')
        return result.get('attack_paths', [])

    def get_security_requirements(
        self,
        diagram_id: str,
        priority: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get security requirements for a diagram.

        Args:
            diagram_id: Diagram UUID
            priority: Filter by priority (high, medium, low)

        Returns:
            List of security requirements
        """
        params = {}
        if priority:
            params['priority'] = priority

        result = self._http.get(
            f'/v2/threat-modeling/threat-engine/security-requirements/',
            params={'diagram_id': diagram_id, **params}
        )
        return result.get('requirements', result.get('results', []))
