"""AI API - Usage, quota, models, and analysis"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class AIAPI:
    """
    AI usage, quota, models, and analysis.

    Usage:
        client = Aribot(api_key)
        usage = client.ai.get_usage()
        quota = client.ai.get_quota()
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_usage(self) -> Dict[str, Any]:
        """
        Get AI usage statistics.

        Returns:
            Usage stats including calls, tokens, and costs
        """
        return self._http.get('/v2/ai/usage/')

    def get_quota(self) -> Dict[str, Any]:
        """
        Get AI quota and limits.

        Returns:
            Quota details with remaining allowances
        """
        return self._http.get('/v2/ai/quota/')

    def get_models(self) -> List[Dict[str, Any]]:
        """
        List available AI models.

        Returns:
            List of AI models with capabilities and pricing
        """
        result = self._http.get('/v2/ai/models/')

        if isinstance(result, list):
            return result
        return result.get('results', result.get('models', []))

    def configure(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure AI settings.

        Args:
            settings: Configuration options (e.g., preferred model, cost limits)

        Returns:
            Updated AI configuration

        Example:
            client.ai.configure({
                "preferred_model": "gpt-4",
                "cost_limit_daily": 50.0
            })
        """
        return self._http.post('/v2/ai/configure/', json=settings)

    def analyze(
        self,
        content: str,
        analysis_type: str = "general",
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run AI analysis on content.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (general, threat, compliance, code)
            options: Additional analysis options

        Returns:
            AI analysis results

        Example:
            result = client.ai.analyze(
                content="S3 bucket with public access",
                analysis_type="threat"
            )
        """
        data = {
            'content': content,
            'analysis_type': analysis_type
        }
        if options:
            data['options'] = options

        return self._http.post('/v2/ai/analyze/', json=data)

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get AI processing queue status.

        Returns:
            Queue status with pending, processing, and completed counts
        """
        return self._http.get('/v2/ai/queue-status/')
