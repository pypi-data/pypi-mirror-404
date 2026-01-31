"""AI Remediation API - Generate and manage AI-powered fix plans"""

from typing import Optional, List, Dict, Any


class RemediationAPI:
    """
    AI-powered remediation generation and management.

    The remediation API generates context-aware fix plans using AI models
    (Claude, OpenAI, Vertex AI) that include root cause analysis, step-by-step
    instructions, code snippets (Terraform, CloudFormation, etc.), and rollback plans.

    Usage:
        client = Aribot(api_key)

        # Generate remediation for a policy violation
        plan = client.remediation.generate_for_policy(
            policy_id="policy-123",
            account_id=123
        )

        # View the AI-generated fix plan
        print(plan['root_cause_analysis'])
        print(plan['remediation_steps'])
        print(plan['code_snippets'])
    """

    def __init__(self, http):
        self._http = http

    def list(
        self,
        severity: str = None,
        platform: str = None,
        status: str = None,
        policy_id: str = None,
        account_id: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List remediation plans with filtering.

        Args:
            severity: Filter by severity (critical, high, medium, low)
            platform: Filter by cloud platform (aws, azure, gcp)
            status: Filter by status (pending, in_progress, completed, skipped)
            policy_id: Filter by policy UUID
            account_id: Filter by cloud account ID
            limit: Maximum results to return (default: 50)
            offset: Offset for pagination

        Returns:
            Paginated list of remediation plans

        Example:
            # List all critical pending remediations
            plans = client.remediation.list(
                severity="critical",
                status="pending",
                limit=20
            )
            for plan in plans['results']:
                print(f"[{plan['severity']}] {plan['policy_name']}")
        """
        params = {'limit': limit, 'offset': offset}

        if severity:
            params['severity'] = severity
        if platform:
            params['platform'] = platform
        if status:
            params['status'] = status
        if policy_id:
            params['policy_id'] = policy_id
        if account_id:
            params['account_id'] = account_id

        return self._http.get('/v2/compliances/remediation/', params=params)

    def get(self, remediation_id: int) -> Dict[str, Any]:
        """
        Get a specific remediation plan by ID.

        Args:
            remediation_id: Remediation plan ID

        Returns:
            Remediation plan with all details including:
            - root_cause_analysis: AI analysis of the root cause
            - remediation_steps: Step-by-step fix instructions
            - code_snippets: Infrastructure-as-code examples
            - rollback_plan: How to undo the fix if needed
            - success_criteria: How to verify the fix worked
        """
        return self._http.get(f'/v2/compliances/remediation/{remediation_id}/')

    def generate_for_policy(
        self,
        policy_id: str,
        account_id: int,
        resource_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate AI remediation plan for a specific policy violation.

        Uses AI to analyze the policy violation and generate a comprehensive
        remediation plan including root cause analysis, step-by-step instructions,
        code snippets, and rollback procedures.

        Args:
            policy_id: Policy UUID to remediate
            account_id: Cloud account ID where the violation exists
            resource_id: Specific resource ID (optional, for targeted remediation)
            context: Additional context for the AI (constraints, notes, etc.)

        Returns:
            AI-generated remediation plan with:
            - root_cause_analysis: Why the violation occurred
            - remediation_steps: List of steps to fix the issue
            - code_snippets: Terraform/CloudFormation/CLI commands
            - rollback_plan: How to undo the changes if needed
            - success_criteria: How to verify the fix was successful
            - estimated_effort: Time estimate for manual remediation
            - ai_provider: Which AI model generated the plan
            - generation_time_ms: Time taken to generate

        Example:
            plan = client.remediation.generate_for_policy(
                policy_id="s3-public-access",
                account_id=123,
                context={"environment": "production"}
            )
            print(f"Root Cause: {plan['root_cause_analysis']}")
            for step in plan['remediation_steps']:
                print(f"  - {step}")
        """
        data = {
            'policy_id': policy_id,
            'account_id': account_id
        }

        if resource_id:
            data['resource_id'] = resource_id
        if context:
            data['context'] = context

        return self._http.post('/v2/compliances/remediation/generate_for_policy/', json=data)

    def generate_for_scan_results(
        self,
        account_id: int,
        scan_id: int,
        policy_ids: List[str] = None,
        severity_filter: List[str] = None,
        max_plans: int = None
    ) -> Dict[str, Any]:
        """
        Batch generate remediation plans for scan results.

        Efficiently generates remediation plans for multiple violations found
        in a scan. Reuses existing plans where possible to save AI costs.

        Args:
            account_id: Cloud account ID
            scan_id: Scan ID to process
            policy_ids: Specific policy IDs to process (optional)
            severity_filter: Severity levels to include (e.g., ["critical", "high"])
            max_plans: Maximum number of plans to generate

        Returns:
            Batch generation result with:
            - generated: Count of newly generated plans
            - reused: Count of reused existing plans
            - total_plans: Total plans available
            - plans: List of remediation plan objects

        Example:
            result = client.remediation.generate_for_scan_results(
                account_id=123,
                scan_id=456,
                severity_filter=["critical", "high"],
                max_plans=20
            )
            print(f"Generated {result['generated']} new plans")
            print(f"Reused {result['reused']} existing plans")
        """
        data = {
            'account_id': account_id,
            'scan_id': scan_id
        }

        if policy_ids:
            data['policy_ids'] = policy_ids
        if severity_filter:
            data['severity_filter'] = severity_filter
        if max_plans:
            data['max_plans'] = max_plans

        return self._http.post('/v2/compliances/remediation/generate_for_scan_results/', json=data)

    def generate_for_violations(
        self,
        account_id: int,
        severity: str = None,
        category: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Generate remediation plans for violations by severity/category.

        Bulk generates remediation plans for all violations matching the
        specified criteria.

        Args:
            account_id: Cloud account ID
            severity: Severity level (critical, high, medium, low)
            category: Violation category (access_control, encryption, network, etc.)
            limit: Maximum violations to process

        Returns:
            Batch result with generated and reused plan counts

        Example:
            result = client.remediation.generate_for_violations(
                account_id=123,
                severity="critical",
                limit=10
            )
        """
        data = {'account_id': account_id}

        if severity:
            data['severity'] = severity
        if category:
            data['category'] = category
        if limit:
            data['limit'] = limit

        return self._http.post('/v2/compliances/remediation/generate_for_violations/', json=data)

    def mark_status(
        self,
        remediation_id: int,
        status: str,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Update the status of a remediation plan.

        Track progress through the remediation lifecycle by updating status.

        Args:
            remediation_id: Remediation plan ID
            status: New status (pending, in_progress, completed, skipped)
            notes: Optional notes about the status change

        Returns:
            Updated remediation plan

        Example:
            # Start working on a remediation
            client.remediation.mark_status(123, "in_progress")

            # After applying the fix
            client.remediation.mark_status(123, "completed",
                notes="Applied via Terraform")

            # Skip if not applicable
            client.remediation.mark_status(456, "skipped",
                notes="Resource was already deleted")
        """
        data = {'status': status}
        if notes:
            data['notes'] = notes

        return self._http.post(
            f'/v2/compliances/remediation/{remediation_id}/mark_status/',
            json=data
        )

    def regenerate(
        self,
        remediation_id: int,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Regenerate a remediation plan with fresh AI analysis.

        Use this when the original plan didn't work, infrastructure changed,
        or you need an alternative approach.

        Args:
            remediation_id: Remediation plan ID to regenerate
            context: Additional context for the AI (constraints, notes, etc.)

        Returns:
            New version of the remediation plan

        Example:
            # Regenerate with additional constraints
            new_plan = client.remediation.regenerate(
                remediation_id=123,
                context={
                    "note": "Previous fix didn't work",
                    "constraints": "Cannot modify network ACLs"
                }
            )
        """
        data = {}
        if context:
            data['context'] = context

        return self._http.post(
            f'/v2/compliances/remediation/{remediation_id}/regenerate/',
            json=data
        )

    def stats(self, account_id: int = None) -> Dict[str, Any]:
        """
        Get remediation statistics and metrics.

        Args:
            account_id: Filter by account (optional)

        Returns:
            Statistics including:
            - total: Total remediation plans
            - pending, in_progress, completed, skipped: Counts by status
            - completion_rate: Percentage completed
            - by_severity: Breakdown by severity level
            - by_platform: Breakdown by cloud platform
            - avg_generation_time_ms: Average AI generation time

        Example:
            stats = client.remediation.stats()
            print(f"Total: {stats['total']}")
            print(f"Completed: {stats['completed']} ({stats['completion_rate']}%)")
        """
        params = {}
        if account_id:
            params['account_id'] = account_id

        return self._http.get('/v2/compliances/remediation/stats/', params=params)

    def analytics_by_severity(self, account_id: int = None) -> Dict[str, Any]:
        """
        Get remediation analytics grouped by severity.

        Args:
            account_id: Filter by account (optional)

        Returns:
            Analytics with counts and completion rates by severity level
        """
        params = {}
        if account_id:
            params['account_id'] = account_id

        return self._http.get('/v2/compliances/remediation/analytics/by_severity/', params=params)

    def analytics_by_policy(self, account_id: int = None) -> Dict[str, Any]:
        """
        Get remediation analytics grouped by policy.

        Args:
            account_id: Filter by account (optional)

        Returns:
            Analytics with counts and completion rates by policy
        """
        params = {}
        if account_id:
            params['account_id'] = account_id

        return self._http.get('/v2/compliances/remediation/analytics/by_policy/', params=params)

    def violations_summary(self, account_id: int) -> Dict[str, Any]:
        """
        Get summary of violations that need remediation.

        Args:
            account_id: Cloud account ID

        Returns:
            Summary with violation counts by severity, platform, and category
        """
        return self._http.get(
            '/v2/compliances/remediation/violations_summary/',
            params={'account_id': account_id}
        )

    def for_standard(
        self,
        standard_id: str,
        account_id: int = None
    ) -> Dict[str, Any]:
        """
        Get remediations mapped to a compliance standard.

        Args:
            standard_id: Compliance standard ID (e.g., "CIS-AWS", "NIST-800-53")
            account_id: Filter by account (optional)

        Returns:
            Remediations grouped by standard controls

        Example:
            remediations = client.remediation.for_standard(
                standard_id="CIS-AWS",
                account_id=123
            )
        """
        params = {'standard_id': standard_id}
        if account_id:
            params['account_id'] = account_id

        return self._http.get('/v2/compliances/remediation/for_standard/', params=params)
