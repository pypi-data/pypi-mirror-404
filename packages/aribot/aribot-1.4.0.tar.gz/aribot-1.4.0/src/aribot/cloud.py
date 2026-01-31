"""Cloud Security API"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class CloudSecurityAPI:
    """
    Cloud security scanning for AWS, Azure, and GCP.

    Usage:
        client = Ayurak(api_key)
        scan = client.cloud.scan(project_id="aws-123456")
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def scan(
        self,
        project_id: str,
        provider: str = None,
        regions: List[str] = None,
        services: List[str] = None,
        compliance_standards: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run cloud security scan.

        Args:
            project_id: Cloud project/account ID
            provider: Cloud provider (aws, azure, gcp) - auto-detected if not specified
            regions: Specific regions to scan
            services: Specific services to scan (ec2, s3, iam, etc.)
            compliance_standards: Standards to check against

        Returns:
            Scan results with findings

        Example:
            scan = client.cloud.scan(
                project_id="123456789012",
                provider="aws",
                services=["iam", "s3", "ec2"],
                compliance_standards=["CIS-AWS"]
            )
            print(f"Found {scan['findings_count']} issues")
        """
        data = {'project_id': project_id}

        if provider:
            data['provider'] = provider
        if regions:
            data['regions'] = regions
        if services:
            data['services'] = services
        if compliance_standards:
            data['compliance_standards'] = compliance_standards

        return self._http.post('/v2/cloud-security/scans/', json=data)

    def get_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan details and results.

        Args:
            scan_id: Scan UUID

        Returns:
            Scan with findings and status
        """
        return self._http.get(f'/v2/cloud-security/scans/{scan_id}/')

    def list_scans(
        self,
        project_id: str = None,
        provider: str = None,
        status: str = None,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        List cloud security scans.

        Args:
            project_id: Filter by project
            provider: Filter by provider
            status: Filter by status
            page: Page number
            limit: Items per page

        Returns:
            Paginated list of scans
        """
        params = {'page': page, 'limit': limit}
        if project_id:
            params['project_id'] = project_id
        if provider:
            params['provider'] = provider
        if status:
            params['status'] = status

        return self._http.get('/v2/cloud-security/scans/', params=params)

    def get_findings(
        self,
        scan_id: str,
        severity: str = None,
        service: str = None,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get findings from a scan.

        Args:
            scan_id: Scan UUID
            severity: Filter by severity (critical, high, medium, low)
            service: Filter by service
            status: Filter by status (open, resolved, suppressed)

        Returns:
            List of security findings
        """
        params = {}
        if severity:
            params['severity'] = severity
        if service:
            params['service'] = service
        if status:
            params['status'] = status

        result = self._http.get(
            f'/v2/cloud-security/scans/{scan_id}/findings/',
            params=params
        )

        if isinstance(result, list):
            return result
        return result.get('results', result.get('findings', []))

    def connect_account(
        self,
        provider: str,
        credentials: Dict[str, str],
        name: str = None,
        regions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Connect a cloud account for scanning.

        Args:
            provider: Cloud provider (aws, azure, gcp)
            credentials: Provider-specific credentials
            name: Friendly name for the account
            regions: Regions to enable

        Returns:
            Connected account details

        Example (AWS):
            account = client.cloud.connect_account(
                provider="aws",
                credentials={
                    "role_arn": "arn:aws:iam::123456789012:role/AribotSecurityRole",
                    "external_id": "your-external-id"
                },
                name="Production AWS"
            )

        Example (GCP):
            account = client.cloud.connect_account(
                provider="gcp",
                credentials={
                    "service_account_key": "{ ... }",
                    "project_id": "my-project-123"
                }
            )
        """
        data = {
            'provider': provider,
            'credentials': credentials
        }
        if name:
            data['name'] = name
        if regions:
            data['regions'] = regions

        return self._http.post('/v2/cloud-security/accounts/', json=data)

    def list_accounts(
        self,
        provider: str = None
    ) -> List[Dict[str, Any]]:
        """
        List connected cloud accounts.

        Args:
            provider: Filter by provider

        Returns:
            List of connected accounts
        """
        params = {}
        if provider:
            params['provider'] = provider

        result = self._http.get('/v2/cloud-security/accounts/', params=params)

        if isinstance(result, list):
            return result
        return result.get('results', result.get('accounts', []))

    def delete_account(self, account_id: str) -> None:
        """
        Disconnect a cloud account.

        Args:
            account_id: Account UUID
        """
        self._http.delete(f'/v2/cloud-security/accounts/{account_id}/')

    def resolve_finding(
        self,
        finding_id: str,
        resolution: str,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Mark a finding as resolved.

        Args:
            finding_id: Finding UUID
            resolution: Resolution type (fixed, accepted, false_positive)
            notes: Resolution notes

        Returns:
            Updated finding
        """
        data = {'resolution': resolution}
        if notes:
            data['notes'] = notes

        return self._http.post(
            f'/v2/cloud-security/findings/{finding_id}/resolve/',
            json=data
        )

    def suppress_finding(
        self,
        finding_id: str,
        reason: str,
        duration_days: int = None
    ) -> Dict[str, Any]:
        """
        Suppress a finding.

        Args:
            finding_id: Finding UUID
            reason: Suppression reason
            duration_days: Auto-unsuppress after days (None = permanent)

        Returns:
            Updated finding
        """
        data = {'reason': reason}
        if duration_days:
            data['duration_days'] = duration_days

        return self._http.post(
            f'/v2/cloud-security/findings/{finding_id}/suppress/',
            json=data
        )

    def get_remediation(self, finding_id: str) -> Dict[str, Any]:
        """
        Get remediation steps for a finding.

        Args:
            finding_id: Finding UUID

        Returns:
            Remediation instructions with code examples
        """
        return self._http.get(
            f'/v2/cloud-security/findings/{finding_id}/remediation/'
        )

    def dashboard(
        self,
        project_id: str = None,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get cloud security dashboard.

        Args:
            project_id: Filter by project
            period: Time period (day, week, month, quarter)

        Returns:
            Dashboard with metrics, trends, and top issues
        """
        params = {'period': period}
        if project_id:
            params['project_id'] = project_id

        return self._http.get('/v2/cloud-security/dashboard/', params=params)
