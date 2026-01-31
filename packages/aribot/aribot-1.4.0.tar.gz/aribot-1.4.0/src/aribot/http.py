"""HTTP client for Aribot API - by Aristiun & Ayurak"""

import time
from typing import Optional, Dict, Any, BinaryIO
import requests

from .exceptions import (
    AribotError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)


class HttpClient:
    """HTTP client with retry logic and error handling"""

    DEFAULT_BASE_URL = "https://api.aribot.ayurak.com/aribot-api"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: int = None
    ):
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/')
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'User-Agent': 'aribot-python/1.4.0'
        })

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions"""
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {'raw': response.text}

        if response.status_code == 401:
            raise AuthenticationError(
                data.get('detail', 'Invalid API key'),
                status_code=401,
                response=data
            )

        if response.status_code == 403:
            raise AuthenticationError(
                data.get('detail', 'Access denied'),
                status_code=403,
                response=data
            )

        if response.status_code == 404:
            raise NotFoundError(
                data.get('detail', 'Resource not found'),
                status_code=404,
                response=data
            )

        if response.status_code == 422:
            raise ValidationError(
                data.get('detail', 'Validation error'),
                errors=data.get('errors', []),
                status_code=422,
                response=data
            )

        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            raise RateLimitError(
                data.get('detail', 'Rate limit exceeded'),
                retry_after=int(retry_after) if retry_after else None,
                status_code=429,
                response=data
            )

        if response.status_code >= 500:
            raise ServerError(
                data.get('detail', 'Server error'),
                status_code=response.status_code,
                response=data
            )

        if response.status_code >= 400:
            raise AribotError(
                data.get('detail', f'Request failed with status {response.status_code}'),
                status_code=response.status_code,
                response=data
            )

        return data

    def _request(
        self,
        method: str,
        path: str,
        params: Dict = None,
        json: Dict = None,
        data: Dict = None,
        files: Dict = None,
        retry: int = 0
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{path}"

        headers = {}
        if json is not None:
            headers['Content-Type'] = 'application/json'

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            return self._handle_response(response)

        except RateLimitError as e:
            if retry < self.MAX_RETRIES and e.retry_after:
                time.sleep(min(e.retry_after, 60))
                return self._request(method, path, params, json, data, files, retry + 1)
            raise

        except requests.exceptions.Timeout:
            if retry < self.MAX_RETRIES:
                time.sleep(2 ** retry)
                return self._request(method, path, params, json, data, files, retry + 1)
            raise AribotError('Request timed out')

        except requests.exceptions.ConnectionError:
            if retry < self.MAX_RETRIES:
                time.sleep(2 ** retry)
                return self._request(method, path, params, json, data, files, retry + 1)
            raise AribotError('Connection error')

    def get(self, path: str, params: Dict = None) -> Dict[str, Any]:
        return self._request('GET', path, params=params)

    def post(
        self,
        path: str,
        json: Dict = None,
        data: Dict = None,
        files: Dict = None
    ) -> Dict[str, Any]:
        return self._request('POST', path, json=json, data=data, files=files)

    def put(self, path: str, json: Dict = None) -> Dict[str, Any]:
        return self._request('PUT', path, json=json)

    def patch(self, path: str, json: Dict = None) -> Dict[str, Any]:
        return self._request('PATCH', path, json=json)

    def delete(self, path: str) -> Dict[str, Any]:
        return self._request('DELETE', path)
