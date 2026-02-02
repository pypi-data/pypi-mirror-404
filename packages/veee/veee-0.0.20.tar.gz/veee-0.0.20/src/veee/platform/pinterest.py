# Copyright 2025 Clivern
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode
from veee.platform.integration import Integration


@dataclass
class PinterestPost:
    """
    Pinterest Post Message
    """

    title: str
    description: str
    link: str
    alt_text: str
    board_id: str
    media_source: dict

    def as_dict(self):
        """
        Convert the Pinterest Post to a dictionary

        Returns:
            dict: The Pinterest Post as a dictionary
        """
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "alt_text": self.alt_text,
            "board_id": self.board_id,
            "media_source": self.media_source,
        }


class Pinterest(Integration):
    """
    Pinterest Platform
    """

    VERSION = "0.0.1"
    TYPE = "pinterest"

    def __init__(self, config: dict):
        """
        Initialize the Pinterest platform

        Args:
            config (dict): The configuration
        """
        self._app_id = config.get("app_id")
        self._app_secret = config.get("app_secret_key")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "boards:read,pins:read,pins:write,user_accounts:read,boards:write",
        )
        self._response_type = config.get("response_type", "code")
        self._api_url = config.get("api_url", "https://api.pinterest.com/v5")
        self._api_oauth_url = config.get(
            "api_oauth_url", "https://www.pinterest.com/oauth/"
        )

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL

        Args:
            data (dict): The data to be used to generate the OAuth redirect URL

        Returns:
            str: The OAuth redirect URL
        """
        params = {
            "client_id": self._app_id,
            "redirect_uri": self._app_redirect_uri,
            "response_type": self._response_type,
            "scope": self._app_scope,
            "state": data.get("state", ""),
        }

        return f"{self._api_oauth_url}?{urlencode(params)}"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens (access_token, refresh_token, expires_in)

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: The access tokens
                {
                    "access_token": "{access_token_string_with_'pina'_prefix}",
                    "refresh_token": "{refresh_token_string_with_'pinr'_prefix}",
                    "response_type": "authorization_code",
                    "token_type": "bearer",
                    "expires_in": 2592000,
                    "refresh_token_expires_in": 31536000,
                    "scope": "boards:read boards:write pins:read"
                }
        """
        code = data.get("code", "")

        response = requests.post(
            f"{self._api_url}/oauth/token",
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{self._app_id}:{self._app_secret}'.encode('utf-8')).decode('utf-8')}"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._app_redirect_uri,
                "continuous_refresh": "true",
            },
        )

        return response.json()

    def get_user_info(self, access_token: str) -> dict:
        """
        Get the user info

        Args:
            access_token (str): The access token

        Returns:
            dict: The user info
                {
                    'profile_image': 'https://s.pinimg.com/images/user/default_600.png',
                    'id': '945474652929812773',
                    'follower_count': 0,
                    'pin_count': 3,
                    'username': 'timan0396',
                    'website_url': 'http://timan.io',
                    ....
                }
        """
        response = requests.get(
            f"{self._api_url}/user_account",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
                {
                    "access_token": "{access_token_string_with_'pina'_prefix}",
                    "refresh_token": "{refresh_token_string_with_'pinr'_prefix}",
                    "response_type": "authorization_code",
                    "token_type": "bearer",
                    "expires_in": 2592000,
                    "refresh_token_expires_in": 31536000,
                    "scope": "boards:read boards:write pins:read"
                }
        """
        response = requests.post(
            f"{self._api_url}/oauth/token",
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{self._app_id}:{self._app_secret}'.encode('utf-8')).decode('utf-8')}"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": self._app_scope,
            },
        )
        return response.json()

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post a message to the integration

        Args:
            access_token (str): The access token
            message (dict): The message to be posted

        Returns:
            dict: The response from the integration
        """
        response = requests.post(
            f"{self._api_url}/pins",
            headers={"Authorization": f"Bearer {access_token}"},
            json=message,
        )

        return response.json()

    def get_pinterest_boards(self, access_token: str) -> list:
        """
        Get the pinterest boards

        Args:
            access_token (str): The access token

        Returns:
            list: The pinterest boards
            {
                'items': [
                    {
                        'id': '945474584211504364',
                        'owner': {'username': 'timan0396'},
                        'name': 'Girls',
                        'description': '',
                        ....
                    }
                ],
           }
        """
        response = requests.get(
            f"{self._api_url}/boards",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    def get_account_analytics(self, access_token: str, options: dict = {}) -> list:
        """
        Get the account analytics of the integration

        Args:
            access_token (str): The access token
            options (dict, optional): Options dictionary containing:
                - start_date (str): Start date in YYYY-MM-DD format. Defaults to 30 days ago.
                - end_date (str): End date in YYYY-MM-DD format. Defaults to today.
                - metric_types (str): Comma-separated list of metric types (e.g., "IMPRESSION,OUTBOUND_CLICK,SAVE").
                                    Defaults to all available metrics.

        Returns:
            list: The account analytics data (full API response, wrapped in list if dict)
        """
        params = {
            "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if options.get("start_date") is None
            else options.get("start_date"),
            "end_date": datetime.now().strftime("%Y-%m-%d")
            if options.get("end_date") is None
            else options.get("end_date"),
        }

        metric_types = options.get("metric_types")
        if metric_types:
            params["metric_types"] = metric_types

        response = requests.get(
            f"{self._api_url}/user_account/analytics",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )

        return response.json()

    def get_post_analytics(
        self, access_token: str, post_id: str, options: dict = {}
    ) -> list:
        """
        Get the post analytics of the integration

        Args:
            access_token (str): The access token
            post_id (str): The pin/post ID
            options (dict, optional): Options dictionary containing:
                - start_date (str): Start date in YYYY-MM-DD format. Defaults to 30 days ago.
                - end_date (str): End date in YYYY-MM-DD format. Defaults to today.
                - metric_types (str): Comma-separated list of metric types
                                    (e.g., "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK").
                                    Defaults to "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK".
                - app_types (str): Filter by app/device type. Options: ALL, MOBILE, TABLET, WEB. Defaults to ALL.
                - split_field (str): How to split the data. Options: NO_SPLIT, APP_TYPE. Defaults to NO_SPLIT.

        Returns:
            list: The post analytics data
        """
        params = {
            "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if options.get("start_date") is None
            else options.get("start_date"),
            "end_date": datetime.now().strftime("%Y-%m-%d")
            if options.get("end_date") is None
            else options.get("end_date"),
            "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK"
            if options.get("metric_types") is None
            else options.get("metric_types"),
        }

        app_types = options.get("app_types")
        if app_types:
            params["app_types"] = app_types

        split_field = options.get("split_field")
        if split_field:
            params["split_field"] = split_field

        response = requests.get(
            f"{self._api_url}/pins/{post_id}/analytics",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )

        return response.json()

    def version(self) -> str:
        return self.VERSION

    def get_type(self) -> str:
        return self.TYPE
