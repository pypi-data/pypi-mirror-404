"""
IssueBadge Python SDK - Digital Badge & Certificate Generator

Official Python SDK for Issue Badge API. Create, issue, and manage
digital certificates and badges programmatically.

Features:
    - Generate digital badges and certificates
    - Bulk certificate generation via API
    - Custom metadata and fields support
    - Image upload support (Base64)
    - Expiration date management
    - Idempotent operations

Example:
    >>> from issuebadge import IssueBadge
    >>> client = IssueBadge('YOUR_API_TOKEN')
    >>> result = client.issue_badge({
    ...     'badge_id': 'abc123',
    ...     'name': 'John Doe',
    ...     'email': 'john@example.com'
    ... })
    >>> print(result['publicUrl'])

Author: Issue Badge
Contact: support@issuebadge.com
License: MIT
Documentation: https://issuebadge.com/h/developer
"""

__version__ = "1.0.1"
__author__ = "Issue Badge"
__email__ = "support@issuebadge.com"
__license__ = "MIT"

import requests
import json
from typing import Optional, Dict, Any, List


class IssueBadge:
    """
    IssueBadge API Client - Digital Badge & Certificate Generator

    A Python client for the Issue Badge API that enables you to create,
    issue, and manage digital certificates and badges programmatically.

    Use cases:
        - Training and course completion certificates
        - Employee recognition badges
        - Event and webinar certificates
        - Academic achievements
        - Professional certifications
        - Bulk certificate generation

    Attributes:
        api_token: Your Issue Badge API token
        api_url: Base URL for the API (default: https://app.issuebadge.com)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = IssueBadge('YOUR_API_TOKEN')
        >>> result = client.issue_badge({
        ...     'badge_id': 'abc123',
        ...     'name': 'John Doe',
        ...     'email': 'john@example.com',
        ...     'idempotency_key': 'unique_key_12345'
        ... })
        >>> print(f"Certificate URL: {result['publicUrl']}")
    """

    def __init__(
        self,
        api_token: str,
        api_url: str = "https://app.issuebadge.com",
        timeout: int = 30
    ):
        """
        Initialize the IssueBadge SDK client.

        Args:
            api_token: Your API token from Issue Badge dashboard
            api_url: API base URL (default: https://app.issuebadge.com)
            timeout: Request timeout in seconds (default: 30)

        Example:
            >>> client = IssueBadge('YOUR_API_TOKEN')
            >>> # With custom timeout
            >>> client = IssueBadge('YOUR_API_TOKEN', timeout=60)
        """
        self.api_token = api_token
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def validate_key(self) -> Dict[str, Any]:
        """
        Validate your API key.

        Verifies that your API credentials are valid and returns
        account information.

        Returns:
            dict: Response containing validation status and account info

        Raises:
            Exception: If API key is invalid or request fails

        Example:
            >>> result = client.validate_key()
            >>> if result.get('valid'):
            ...     print("API key is valid!")
        """
        return self._request('POST', '/api/v1/validate-key')

    def create_badge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new badge/certificate template.

        Creates a reusable template that can be used to issue
        certificates to recipients.

        Args:
            data: Badge template data including name, description, etc.

        Returns:
            dict: Created badge template data with badge_id

        Raises:
            Exception: On API failure

        Example:
            >>> result = client.create_badge({
            ...     'name': 'Python Certification',
            ...     'description': 'Certificate for Python developers'
            ... })
            >>> badge_id = result['badge_id']
        """
        return self._request('POST', '/api/v1/badge/create', data)

    def get_all_badges(self) -> Dict[str, Any]:
        """
        Get all badge/certificate templates.

        Retrieves a list of all badge templates in your account.

        Returns:
            dict: Response containing list of badge templates

        Raises:
            Exception: On API failure

        Example:
            >>> badges = client.get_all_badges()
            >>> for badge in badges.get('data', []):
            ...     print(f"{badge['name']}: {badge['badge_id']}")
        """
        return self._request('GET', '/api/v1/badge/getall')

    def issue_badge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Issue a badge/certificate to a recipient.

        Issues a certificate using the specified badge template to
        a recipient. Supports custom fields, expiration dates, and
        image uploads.

        Args:
            data: Issue data including:
                - badge_id (str): The badge template ID
                - name (str): Recipient's full name
                - email (str): Recipient's email address
                - idempotency_key (str, optional): Unique key for idempotent requests
                - expire_date (str, optional): Expiration date (YYYY-MM-DD)
                - metadata (dict, optional): Custom fields for the certificate

        Returns:
            dict: Response with publicUrl and certificate details

        Raises:
            Exception: On API failure

        Example:
            >>> # Basic certificate issuance
            >>> result = client.issue_badge({
            ...     'badge_id': 'abc123',
            ...     'name': 'John Doe',
            ...     'email': 'john@example.com',
            ...     'idempotency_key': 'unique_key_12345'
            ... })
            >>> print(f"Certificate: {result['publicUrl']}")

            >>> # With expiration and custom fields
            >>> result = client.issue_badge({
            ...     'badge_id': 'abc123',
            ...     'name': 'Jane Smith',
            ...     'email': 'jane@example.com',
            ...     'expire_date': '2026-12-31',
            ...     'metadata': {
            ...         'course': 'Advanced Python',
            ...         'score': 95
            ...     }
            ... })
        """
        return self._request('POST', '/api/v1/issue/create', data)

    def issue_badge_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Issue a badge/certificate via GET request (webhook style).

        Alternative method for issuing certificates using query parameters.
        Useful for webhook integrations and simple automation.

        Args:
            params: Query parameters including badge_id, name, email, etc.

        Returns:
            dict: Response with publicUrl and certificate details

        Raises:
            Exception: On API failure

        Example:
            >>> result = client.issue_badge_get({
            ...     'badge_id': 'abc123',
            ...     'name': 'John Doe',
            ...     'email': 'john@example.com'
            ... })
        """
        return self._request('GET', '/api/v1/issue/create', params=params)

    def issue_badges_bulk(self, badge_id: str, recipients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Issue certificates to multiple recipients (bulk generation).

        Convenience method for issuing the same badge template to
        multiple recipients in a single call.

        Args:
            badge_id: The badge template ID to use
            recipients: List of recipient data, each containing:
                - name (str): Recipient's full name
                - email (str): Recipient's email address
                - idempotency_key (str, optional): Unique key
                - metadata (dict, optional): Custom fields

        Returns:
            list: List of results for each recipient

        Example:
            >>> recipients = [
            ...     {'name': 'John Doe', 'email': 'john@example.com'},
            ...     {'name': 'Jane Smith', 'email': 'jane@example.com'},
            ...     {'name': 'Bob Wilson', 'email': 'bob@example.com'}
            ... ]
            >>> results = client.issue_badges_bulk('abc123', recipients)
            >>> for result in results:
            ...     print(f"Issued: {result['publicUrl']}")
        """
        results = []
        for recipient in recipients:
            data = {'badge_id': badge_id, **recipient}
            try:
                result = self.issue_badge(data)
                results.append({'success': True, **result})
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'recipient': recipient
                })
        return results

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to the API.

        Internal method for handling API requests.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data (for POST)
            params: Query parameters (for GET)

        Returns:
            dict: Parsed JSON response

        Raises:
            Exception: On request failure or API error
        """
        url = self.api_url + endpoint

        try:
            if method == 'POST':
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=self.timeout
                )
            elif method == 'GET':
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
            else:
                raise Exception(f'Unsupported HTTP method: {method}')

            # Parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError:
                raise Exception(f'Invalid JSON response: {response.text}')

            # Check for HTTP errors
            if response.status_code >= 400:
                message = result.get('message', 'API request failed')
                raise Exception(f'{message} (HTTP {response.status_code})')

            return result

        except requests.exceptions.Timeout:
            raise Exception(f'Request timeout after {self.timeout} seconds')
        except requests.exceptions.RequestException as e:
            raise Exception(f'Request error: {str(e)}')
