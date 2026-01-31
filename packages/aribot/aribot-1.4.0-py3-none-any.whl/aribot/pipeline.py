"""Pipeline Security API"""

import time
from typing import Optional, List, Dict, Any

from .http import HttpClient


class PipelineAPI:
    """
    CI/CD pipeline security scanning.

    Usage:
        client = Ayurak(api_key)
        scan = client.pipeline.scan(project_id, commit_sha="abc123")
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def create_project(
        self,
        name: str,
        repository_url: str = None,
        default_branch: str = "main",
        scan_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pipeline project.

        Args:
            name: Project name
            repository_url: Git repository URL
            default_branch: Default branch to scan
            scan_types: Enabled scan types (sast, sca, secrets, iac)

        Returns:
            Created project

        Example:
            project = client.pipeline.create_project(
                name="my-api",
                repository_url="https://github.com/org/my-api",
                scan_types=["sast", "sca", "secrets"]
            )
        """
        data = {
            'name': name,
            'default_branch': default_branch
        }
        if repository_url:
            data['repository_url'] = repository_url
        if scan_types:
            data['scan_types'] = scan_types

        return self._http.post('/v1/pipeline/projects/', json=data)

    def list_projects(
        self,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        List pipeline projects.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of projects
        """
        params = {'page': page, 'limit': limit}
        return self._http.get('/v1/pipeline/projects/', params=params)

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project details.

        Args:
            project_id: Project UUID

        Returns:
            Project with configuration and stats
        """
        return self._http.get(f'/v1/pipeline/projects/{project_id}/')

    def delete_project(self, project_id: str) -> None:
        """
        Delete a pipeline project.

        Args:
            project_id: Project UUID
        """
        self._http.delete(f'/v1/pipeline/projects/{project_id}/')

    def scan(
        self,
        project_id: str,
        commit_sha: str = None,
        branch: str = None,
        scan_types: List[str] = None,
        fail_on_severity: str = None,
        wait: bool = False,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Run pipeline security scan.

        Args:
            project_id: Project UUID
            commit_sha: Git commit SHA
            branch: Git branch
            scan_types: Types to run (sast, sca, secrets, iac)
            fail_on_severity: Fail if findings at this severity or higher
            wait: Wait for scan to complete
            timeout: Max seconds to wait

        Returns:
            Scan results

        Example:
            result = client.pipeline.scan(
                project_id,
                commit_sha="abc123def456",
                scan_types=["sast", "secrets"],
                fail_on_severity="high"
            )
            if result['status'] == 'failed':
                print(f"Security gate failed: {result['summary']}")
        """
        data = {'project_id': project_id}

        if commit_sha:
            data['commit_sha'] = commit_sha
        if branch:
            data['branch'] = branch
        if scan_types:
            data['scan_types'] = scan_types
        if fail_on_severity:
            data['fail_on_severity'] = fail_on_severity

        result = self._http.post('/v1/pipeline/scans/', json=data)

        if not wait:
            return result

        scan_id = result.get('scan_id')
        if not scan_id:
            return result

        return self._wait_for_scan(scan_id, timeout)

    def _wait_for_scan(self, scan_id: str, timeout: int) -> Dict[str, Any]:
        """Poll until scan completes"""
        start = time.time()

        while time.time() - start < timeout:
            scan = self.get_scan(scan_id)
            status = scan.get('status', '')

            if status in ['completed', 'passed', 'failed']:
                return scan
            elif status == 'error':
                raise Exception(f"Scan error: {scan.get('error', 'Unknown error')}")

            time.sleep(5)

        raise TimeoutError(f"Scan did not complete within {timeout} seconds")

    def get_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan details and results.

        Args:
            scan_id: Scan UUID

        Returns:
            Scan with findings and status
        """
        return self._http.get(f'/v1/pipeline/scans/{scan_id}/')

    def list_scans(
        self,
        project_id: str = None,
        status: str = None,
        branch: str = None,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        List pipeline scans.

        Args:
            project_id: Filter by project
            status: Filter by status
            branch: Filter by branch
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of scans
        """
        params = {'page': page, 'limit': limit}
        if project_id:
            params['project_id'] = project_id
        if status:
            params['status'] = status
        if branch:
            params['branch'] = branch

        return self._http.get('/v1/pipeline/scans/', params=params)

    def get_findings(
        self,
        scan_id: str,
        scan_type: str = None,
        severity: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get findings from a scan.

        Args:
            scan_id: Scan UUID
            scan_type: Filter by type (sast, sca, secrets, iac)
            severity: Filter by severity

        Returns:
            List of findings
        """
        params = {}
        if scan_type:
            params['type'] = scan_type
        if severity:
            params['severity'] = severity

        result = self._http.get(
            f'/v1/pipeline/scans/{scan_id}/findings/',
            params=params
        )

        if isinstance(result, list):
            return result
        return result.get('results', result.get('findings', []))

    def get_sast_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Get SAST (static analysis) findings.

        Args:
            scan_id: Scan UUID

        Returns:
            List of code vulnerabilities
        """
        return self.get_findings(scan_id, scan_type='sast')

    def get_sca_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Get SCA (dependency) findings.

        Args:
            scan_id: Scan UUID

        Returns:
            List of vulnerable dependencies
        """
        return self.get_findings(scan_id, scan_type='sca')

    def get_secrets_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Get secrets detection findings.

        Args:
            scan_id: Scan UUID

        Returns:
            List of detected secrets/credentials
        """
        return self.get_findings(scan_id, scan_type='secrets')

    def configure_gates(
        self,
        project_id: str,
        gates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Configure security gates for a project.

        Args:
            project_id: Project UUID
            gates: Gate configuration

        Returns:
            Updated project configuration

        Example:
            client.pipeline.configure_gates(
                project_id,
                gates={
                    "fail_on_critical": True,
                    "fail_on_high": True,
                    "max_high_findings": 5,
                    "block_secrets": True,
                    "required_scan_types": ["sast", "secrets"]
                }
            )
        """
        return self._http.patch(
            f'/v1/pipeline/projects/{project_id}/gates/',
            json=gates
        )

    def add_baseline(
        self,
        project_id: str,
        scan_id: str
    ) -> Dict[str, Any]:
        """
        Set scan as baseline (suppress existing findings).

        Args:
            project_id: Project UUID
            scan_id: Scan to use as baseline

        Returns:
            Updated project
        """
        data = {'baseline_scan_id': scan_id}
        return self._http.post(
            f'/v1/pipeline/projects/{project_id}/baseline/',
            json=data
        )

    def suppress_finding(
        self,
        finding_id: str,
        reason: str,
        expires_at: str = None
    ) -> Dict[str, Any]:
        """
        Suppress a finding.

        Args:
            finding_id: Finding UUID
            reason: Suppression reason
            expires_at: Expiration date (ISO format)

        Returns:
            Updated finding
        """
        data = {'reason': reason}
        if expires_at:
            data['expires_at'] = expires_at

        return self._http.post(
            f'/v1/pipeline/findings/{finding_id}/suppress/',
            json=data
        )

    def dashboard(
        self,
        project_id: str = None,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get pipeline security dashboard.

        Args:
            project_id: Filter by project
            period: Time period

        Returns:
            Dashboard with metrics and trends
        """
        params = {'period': period}
        if project_id:
            params['project_id'] = project_id

        return self._http.get('/v1/pipeline/dashboard/', params=params)
