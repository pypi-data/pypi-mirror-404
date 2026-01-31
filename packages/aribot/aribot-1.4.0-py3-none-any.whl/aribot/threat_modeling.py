"""Threat Modeling API"""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, BinaryIO

from .http import HttpClient


class ThreatModelingAPI:
    """
    Threat modeling operations.

    Usage:
        client = Ayurak(api_key)
        result = client.threat_modeling.analyze_diagram("arch.png")
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def analyze_diagram(
        self,
        file: Union[str, Path, BinaryIO],
        filename: str = None,
        analysis_depth: str = "comprehensive",
        wait: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Upload and analyze a diagram for threats.

        Args:
            file: Path to file or file-like object
            filename: Override filename
            analysis_depth: "basic", "comprehensive", or "detailed"
            wait: Wait for analysis to complete
            timeout: Max seconds to wait

        Returns:
            Diagram analysis results with threats

        Example:
            result = client.threat_modeling.analyze_diagram(
                "architecture.png",
                analysis_depth="comprehensive"
            )
            print(f"Found {result['threat_count']} threats")
        """
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            filename = filename or file_path.name
            with open(file_path, 'rb') as f:
                return self._upload_and_analyze(f, filename, analysis_depth, wait, timeout)
        else:
            filename = filename or 'diagram'
            return self._upload_and_analyze(file, filename, analysis_depth, wait, timeout)

    def _upload_and_analyze(
        self,
        file: BinaryIO,
        filename: str,
        analysis_depth: str,
        wait: bool,
        timeout: int
    ) -> Dict[str, Any]:
        """Upload file and optionally wait for analysis"""
        files = {'file': (filename, file)}
        data = {
            'filename': filename,
            'analysis_depth': analysis_depth
        }

        result = self._http.post(
            '/v2/threat-modeling/diagrams/upload-and-analyze/',
            data=data,
            files=files
        )

        if not wait:
            return result

        diagram_id = result.get('diagram_id')
        if not diagram_id:
            return result

        return self._wait_for_analysis(diagram_id, timeout)

    def _wait_for_analysis(self, diagram_id: str, timeout: int) -> Dict[str, Any]:
        """Poll until analysis completes"""
        start = time.time()

        while time.time() - start < timeout:
            diagram = self.get(diagram_id)
            status = diagram.get('status', '')

            if status in ['completed', 'analyzed', 'done']:
                return diagram
            elif status in ['failed', 'error']:
                raise Exception(f"Analysis failed: {diagram.get('error', 'Unknown error')}")

            time.sleep(5)

        raise TimeoutError(f"Analysis did not complete within {timeout} seconds")

    def list(
        self,
        page: int = 1,
        limit: int = 25,
        status: str = None,
        search: str = None
    ) -> Dict[str, Any]:
        """
        List diagrams.

        Args:
            page: Page number
            limit: Items per page (max 100)
            status: Filter by status
            search: Search in name/description

        Returns:
            Paginated list of diagrams
        """
        params = {'page': page, 'limit': limit}
        if status:
            params['status'] = status
        if search:
            params['search'] = search

        return self._http.get('/v1/tm/diagrams/', params=params)

    def get(self, diagram_id: str) -> Dict[str, Any]:
        """
        Get diagram details.

        Args:
            diagram_id: Diagram UUID

        Returns:
            Diagram with components and metadata
        """
        return self._http.get(f'/v1/tm/diagrams/{diagram_id}/')

    def get_threats(self, diagram_id: str) -> List[Dict[str, Any]]:
        """
        Get threats for a diagram.

        Args:
            diagram_id: Diagram UUID

        Returns:
            List of threats with severity, CVSS, mitigations
        """
        result = self._http.get(f'/v1/tm/diagrams/{diagram_id}/threats/')

        if isinstance(result, list):
            return result
        return result.get('results', result.get('threats', []))

    def get_components(self, diagram_id: str) -> List[Dict[str, Any]]:
        """
        Get components detected in diagram.

        Args:
            diagram_id: Diagram UUID

        Returns:
            List of components with types and connections
        """
        result = self._http.get(f'/v1/tm/diagrams/{diagram_id}/components/')

        if isinstance(result, list):
            return result
        return result.get('results', result.get('components', []))

    def analyze_with_ai(
        self,
        diagram_id: str,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run AI-powered analysis on diagram.

        Args:
            diagram_id: Diagram UUID
            analysis_types: Types of analysis to run

        Returns:
            AI analysis results
        """
        data = {}
        if analysis_types:
            data['analysis_types'] = analysis_types

        return self._http.post(
            f'/v2/threat-modeling/diagrams/{diagram_id}/analyze-with-ai/',
            json=data
        )

    def delete(self, diagram_id: str) -> None:
        """
        Delete a diagram.

        Args:
            diagram_id: Diagram UUID
        """
        self._http.delete(f'/v1/tm/diagrams/{diagram_id}/')

    def dashboard(
        self,
        period: str = "month",
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """
        Get threat modeling dashboard.

        Args:
            period: "day", "week", "month", "quarter"
            include_trends: Include trend data

        Returns:
            Dashboard with metrics, trends, compliance status
        """
        params = {
            'period': period,
            'include_trends': str(include_trends).lower()
        }

        return self._http.get('/v1/tm/dashboard/', params=params)
