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
import hashlib
import requests
from urllib.parse import urlencode
from veee.platform.integration import Integration


class Tiktok(Integration):
    """
    TikTok Platform
    """

    VERSION = "0.0.1"
    TYPE = "tiktok"

    def __init__(self, config: dict):
        """
        Initialize the TikTok platform

        Args:
            config (dict): The configuration
        """
        self._client_key = config.get("client_key") or config.get("app_id")
        self._client_secret = config.get("client_secret") or config.get(
            "app_secret_key"
        )
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "user.info.basic,video.publish,video.upload,user.info.profile",
        )
        self._api_url = "https://open.tiktokapis.com/v2"

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL

        Args:
            data (dict): The data to be used to generate the OAuth redirect URL

        Returns:
            str: The OAuth redirect URL
        """
        import secrets

        state = data.get("state", "")
        code_verifier = data.get("code_verifier") or secrets.token_urlsafe(32)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        params = {
            "client_key": self._client_key,
            "response_type": "code",
            "scope": self._app_scope,
            "redirect_uri": self._app_redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens (access_token, refresh_token, expires_in)

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: The access tokens
        """
        code = data.get("code", "")
        code_verifier = data.get("code_verifier", "")

        token_data = {
            "client_key": self._client_key,
            "client_secret": self._client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self._app_redirect_uri,
            "code_verifier": code_verifier,
        }

        response = requests.post(
            f"{self._api_url}/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=token_data,
        )
        response.raise_for_status()
        token_info = response.json()

        if token_info.get("error"):
            raise ValueError(
                f"TikTok OAuth error: {token_info.get('error_description')}"
            )

        return {
            "access_token": token_info.get("access_token"),
            "refresh_token": token_info.get("refresh_token"),
            "expires_in": token_info.get("expires_in"),
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
            f"{self._api_url}/user/info/",
            params={"fields": "open_id,union_id,avatar_url,display_name"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        user_data = response.json().get("data", {}).get("user", {})
        return {
            "id": user_data.get("open_id"),
            "name": user_data.get("display_name", ""),
            "picture": user_data.get("avatar_url", ""),
            "username": user_data.get("display_name", "").lower().replace(" ", "_"),
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
            "client_key": self._client_key,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        response = requests.post(
            f"{self._api_url}/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=token_data,
        )
        response.raise_for_status()
        token_info = response.json()

        if token_info.get("error"):
            raise ValueError(
                f"TikTok refresh error: {token_info.get('error_description')}"
            )

        return {
            "access_token": token_info.get("access_token"),
            "refresh_token": token_info.get("refresh_token", refresh_token),
            "expires_in": token_info.get("expires_in"),
            "token_type": "bearer",
        }

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post a video to TikTok

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "video_url": "https://example.com/video.mp4",
                    "post_info": {
                        "title": "Video title",
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                        "video_cover_timestamp_ms": 1000
                    }
                }

        Returns:
            dict: The response from TikTok
        """
        post_data = {
            "post_info": message.get("post_info", {}),
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_url": message.get("video_url"),
            },
        }

        response = requests.post(
            f"{self._api_url}/video/publish/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=post_data,
        )
        response.raise_for_status()
        return response.json()

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
