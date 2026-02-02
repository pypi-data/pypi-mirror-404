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
from veee.platform.integration import Integration


class Bluesky(Integration):
    """
    Bluesky Platform
    Note: Bluesky uses ATProto protocol, not OAuth 2.0
    This is a simplified implementation
    """

    VERSION = "0.0.1"
    TYPE = "bluesky"

    def __init__(self, config: dict):
        """
        Initialize the Bluesky platform

        Args:
            config (dict): The configuration
        """
        self._service_domain = config.get("service_domain", "bsky.social")
        self._api_url = f"https://{self._service_domain}/xrpc"
        self._username = config.get("username")
        self._password = config.get("password") or config.get("app_secret_key")

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL
        Note: Bluesky doesn't use OAuth, this returns a placeholder

        Args:
            data (dict): The data to be used to generate the OAuth redirect URL

        Returns:
            str: Placeholder URL
        """
        return f"https://{self._service_domain}/oauth/authorize"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens
        Note: Bluesky uses session-based auth, not OAuth tokens

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: Session information
        """
        if not self._username or not self._password:
            raise ValueError("username and password are required for Bluesky")

        # Create session
        session_data = {
            "identifier": self._username,
            "password": self._password,
        }

        response = requests.post(
            f"{self._api_url}/com.atproto.server.createSession",
            json=session_data,
        )
        response.raise_for_status()
        session_info = response.json()

        return {
            "access_token": session_info.get("accessJwt"),
            "refresh_token": session_info.get("refreshJwt"),
            "expires_in": 86400,  # 24 hours
            "token_type": "Bearer",
            "did": session_info.get("did"),
        }

    def get_user_info(self, access_token: str) -> dict:
        """
        Get the user info

        Args:
            access_token (str): The access token (JWT)

        Returns:
            dict: The user info
        """
        response = requests.get(
            f"{self._api_url}/com.atproto.identity.resolveHandle",
            params={"handle": self._username},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        did = response.json().get("did")

        profile_response = requests.get(
            f"{self._api_url}/app.bsky.actor.getProfile",
            params={"actor": self._username},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_response.raise_for_status()
        profile = profile_response.json()

        return {
            "id": did,
            "name": profile.get("displayName", ""),
            "username": profile.get("handle", ""),
            "picture": profile.get("avatar", ""),
        }

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token (JWT)

        Returns:
            dict: The access tokens
        """
        response = requests.post(
            f"{self._api_url}/com.atproto.server.refreshSession",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        response.raise_for_status()
        session_info = response.json()

        return {
            "access_token": session_info.get("accessJwt"),
            "refresh_token": session_info.get("refreshJwt"),
            "expires_in": 86400,
            "token_type": "Bearer",
        }

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post to Bluesky

        Args:
            access_token (str): The access token (JWT)
            message (dict): The message to be posted
                {
                    "text": "Post text",
                    "langs": ["en"] (optional)
                }

        Returns:
            dict: The response from Bluesky
        """
        # Get user's DID
        user_info = self.get_user_info(access_token)
        did = user_info.get("id")

        post_data = {
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": {
                "text": message.get("text", ""),
                "createdAt": message.get("created_at") or self._get_timestamp(),
                "langs": message.get("langs", ["en"]),
            },
        }

        response = requests.post(
            f"{self._api_url}/com.atproto.repo.createRecord",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=post_data,
        )
        response.raise_for_status()
        return response.json()

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

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
