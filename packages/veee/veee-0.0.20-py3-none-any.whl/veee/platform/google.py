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


class Google(Integration):
    """
    Google Platform (for YouTube and Google services)
    """

    VERSION = "0.0.1"
    TYPE = "google"

    def __init__(self, config: dict):
        """
        Initialize the Google platform

        Args:
            config (dict): The configuration
        """
        self._client_id = config.get("client_id") or config.get("app_id")
        self._client_secret = config.get("client_secret") or config.get(
            "app_secret_key"
        )
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "https://www.googleapis.com/auth/userinfo.profile "
            "https://www.googleapis.com/auth/userinfo.email "
            "https://www.googleapis.com/auth/youtube.upload "
            "https://www.googleapis.com/auth/youtube",
        )
        self._api_url = "https://www.googleapis.com"
        self._oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self._token_url = "https://oauth2.googleapis.com/token"

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
            "client_id": self._client_id,
            "redirect_uri": self._app_redirect_uri,
            "response_type": "code",
            "scope": self._app_scope,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }

        return f"{self._oauth_url}?{urlencode(params)}"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens (access_token, refresh_token, expires_in)

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: The access tokens
        """
        code = data.get("code", "")

        token_data = {
            "code": code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._app_redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(
            self._token_url,
            data=token_data,
        )
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token: str) -> dict:
        """
        Get the user info

        Args:
            access_token (str): The access token

        Returns:
            dict: The user info
        """
        response = requests.get(
            f"{self._api_url}/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        user_info = response.json()
        return {
            "id": user_info.get("id"),
            "name": user_info.get("name"),
            "email": user_info.get("email"),
            "picture": user_info.get("picture", ""),
        }

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
        """
        token_data = {
            "refresh_token": refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
        }

        response = requests.post(
            self._token_url,
            data=token_data,
        )
        response.raise_for_status()
        return response.json()

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post to YouTube (create a video)

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "title": "Video title",
                    "description": "Video description",
                    "video_file": "path/to/video.mp4" (optional, requires file upload)
                }

        Returns:
            dict: The response from YouTube
        """
        # Note: YouTube video upload requires multipart/form-data with actual file
        # This is a simplified version that returns an error if no file is provided
        if not message.get("video_file"):
            return {
                "error": "YouTube video upload requires a video file",
                "message": "Use YouTube Data API v3 to upload videos with actual file content",
            }

        # For actual implementation, you would use googleapiclient
        # This is a placeholder that shows the expected structure
        return {
            "error": "Full YouTube upload requires googleapiclient library",
            "hint": "Install google-api-python-client and use YouTube Data API v3",
        }

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
