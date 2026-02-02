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

import requests
from urllib.parse import urlencode
from veee.platform.integration import Integration


class Threads(Integration):
    """
    Threads Platform (Meta's Threads)
    Note: Threads API is still evolving, this is a basic implementation
    """

    VERSION = "0.0.1"
    TYPE = "threads"

    def __init__(self, config: dict):
        """
        Initialize the Threads platform

        Args:
            config (dict): The configuration
        """
        self._app_id = config.get("app_id")
        self._app_secret = config.get("app_secret_key")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "threads_basic,threads_content_publish",
        )
        self._api_version = config.get("api_version", "v18.0")
        self._api_url = f"https://graph.threads.net/{self._api_version}"

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL

        Args:
            data (dict): The data to be used to generate the OAuth redirect URL

        Returns:
            str: The OAuth redirect URL
        """
        state = data.get("state", "")

        params = {
            "client_id": self._app_id,
            "redirect_uri": self._app_redirect_uri,
            "scope": self._app_scope,
            "response_type": "code",
            "state": state,
        }

        return f"https://www.threads.net/oauth/authorize?{urlencode(params)}"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens (access_token, refresh_token, expires_in)

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: The access tokens
        """
        code = data.get("code", "")

        token_params = {
            "client_id": self._app_id,
            "client_secret": self._app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self._app_redirect_uri,
            "code": code,
        }

        response = requests.get(
            f"{self._api_url}/oauth/access_token",
            params=token_params,
        )
        response.raise_for_status()
        token_info = response.json()

        return {
            "access_token": token_info.get("access_token"),
            "refresh_token": token_info.get(
                "access_token"
            ),  # Threads may use same token
            "expires_in": token_info.get("expires_in", 5184000),
            "token_type": "bearer",
        }

    def get_user_info(self, access_token: str) -> dict:
        """
        Get the user info

        Args:
            access_token (str): The access token

        Returns:
            dict: The user info
        """
        response = requests.get(
            f"{self._api_url}/me",
            params={
                "fields": "id,username",
                "access_token": access_token,
            },
        )
        response.raise_for_status()
        user_info = response.json()
        return {
            "id": user_info.get("id"),
            "username": user_info.get("username", ""),
            "name": user_info.get("username", ""),
        }

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
        """
        # Threads token refresh may vary - this is a placeholder
        return {
            "access_token": refresh_token,
            "refresh_token": refresh_token,
            "expires_in": 5184000,
            "token_type": "bearer",
        }

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post to Threads

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "text": "Thread text",
                    "media_type": "TEXT" or "CAROUSEL"
                }

        Returns:
            dict: The response from Threads
        """
        # Get user's Threads ID
        user_response = requests.get(
            f"{self._api_url}/me",
            params={"access_token": access_token},
        )
        user_response.raise_for_status()
        user_id = user_response.json().get("id")

        post_data = {
            "media_type": message.get("media_type", "TEXT"),
            "text": message.get("text", ""),
        }

        # Create thread
        create_response = requests.post(
            f"{self._api_url}/{user_id}/threads",
            params={"access_token": access_token},
            json=post_data,
        )
        create_response.raise_for_status()
        thread_id = create_response.json().get("id")

        # Publish thread
        publish_response = requests.post(
            f"{self._api_url}/{thread_id}/publish",
            params={"access_token": access_token},
        )
        publish_response.raise_for_status()
        return publish_response.json()

    def get_account_analytics(self, access_token: str, options: dict = {}) -> list:
        """
        Get the account analytics of the integration

        Args:
            access_token (str): The access token
            options (dict, optional): Options dictionary for analytics query

        Returns:
            list: The account analytics
        """
        pass

    def get_post_analytics(
        self, access_token: str, post_id: str, options: dict = {}
    ) -> list:
        """
        Get the post analytics of the integration

        Args:
            access_token (str): The access token
            post_id (str): The post ID
            options (dict, optional): Options dictionary for analytics query

        Returns:
            list: The post analytics
        """
        pass

    def version(self) -> str:
        return self.VERSION

    def get_type(self) -> str:
        return self.TYPE
