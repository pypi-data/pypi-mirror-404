"""Digital Twin API for cloud resource mapping and live status"""

from typing import Optional, List, Dict, Any

from .http import HttpClient


class DigitalTwinAPI:
    """
    Digital Twin API for cloud resource mapping and live status.

    Usage:
        client = Aribot(api_key)
        providers = client.digital_twin.get_providers()
        status = client.digital_twin.get_diagram_component_status(diagram_id)
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def get_providers(self) -> List[Dict[str, Any]]:
        """
        Get available cloud providers (AWS, Azure, GCP).

        Returns:
            List of cloud providers with their status
        """
        result = self._http.get('/v2/threat-modeling/digital-twin/providers/')
        if isinstance(result, list):
            return result
        return result.get('results', [])

    def get_resources(
        self,
        provider: str = None,
        resource_type: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get available cloud resources.

        Args:
            provider: Filter by provider (aws, azure, gcp)
            resource_type: Filter by resource type
            limit: Maximum results

        Returns:
            List of cloud resources
        """
        params = {}
        if provider:
            params['provider'] = provider
        if resource_type:
            params['resource_type'] = resource_type
        if limit:
            params['limit'] = limit

        result = self._http.get('/v2/threat-modeling/digital-twin/available-resources/', params=params)
        if isinstance(result, list):
            return result
        return result.get('results', [])

    def get_diagram_component_status(self, diagram_id: str) -> Dict[str, Any]:
        """
        Get component cloud status for a diagram.

        Args:
            diagram_id: Diagram UUID

        Returns:
            Component status with compliance and security scores
        """
        return self._http.get(f'/v2/threat-modeling/digital-twin/diagram/{diagram_id}/component-status/')

    def map_component(
        self,
        diagram_id: str,
        component_id: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """
        Map a component to a cloud resource.

        Args:
            diagram_id: Diagram UUID
            component_id: Component UUID
            resource_id: Cloud resource ID

        Returns:
            Mapping result
        """
        return self._http.post(
            f'/v2/threat-modeling/digital-twin/diagram/{diagram_id}/map-component/',
            json={
                'component_id': component_id,
                'resource_id': resource_id
            }
        )

    def unmap_component(self, diagram_id: str, component_id: str) -> None:
        """
        Unmap a component from cloud resource.

        Args:
            diagram_id: Diagram UUID
            component_id: Component UUID
        """
        self._http.delete(f'/v2/threat-modeling/digital-twin/diagram/{diagram_id}/component/{component_id}/')

    def sync_diagram_status(self, diagram_id: str) -> Dict[str, Any]:
        """
        Sync diagram cloud status.

        Args:
            diagram_id: Diagram UUID

        Returns:
            Updated status
        """
        return self._http.post(f'/v2/threat-modeling/digital-twin/diagram/{diagram_id}/sync/', json={})

    def get_component_status(self, component_id: str) -> Dict[str, Any]:
        """
        Get single component cloud status.

        Args:
            component_id: Component UUID

        Returns:
            Component cloud status
        """
        return self._http.get(f'/v2/threat-modeling/digital-twin/component-status/{component_id}/')

    def get_health(self) -> Dict[str, Any]:
        """
        Get digital twin health status.

        Returns:
            Health status
        """
        return self._http.get('/v2/threat-modeling/digital-twin/health/')

    def get_analytics(self) -> Dict[str, Any]:
        """
        Get digital twin analytics.

        Returns:
            Analytics data
        """
        return self._http.get('/v2/threat-modeling/digital-twin/analytics/')

    def sync_resources(self, provider_id: str) -> Dict[str, Any]:
        """
        Sync resources from a cloud provider.

        Args:
            provider_id: Provider UUID

        Returns:
            Sync result with resources found
        """
        return self._http.post(
            '/v2/threat-modeling/digital-twin/sync/',
            json={'provider_id': provider_id}
        )

    def discover_resources(self, provider_id: str) -> Dict[str, Any]:
        """
        Discover new resources from a cloud provider.

        Args:
            provider_id: Provider UUID

        Returns:
            Discovery result with new resources count
        """
        return self._http.post(
            '/v2/threat-modeling/digital-twin/discover/',
            json={'provider_id': provider_id}
        )
