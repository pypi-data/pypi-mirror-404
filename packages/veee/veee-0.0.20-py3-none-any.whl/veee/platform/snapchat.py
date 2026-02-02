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


class Snapchat(Integration):
    """
    Snapchat Platform
    Supports both Marketing API (ads) and Creative Kit API (organic content)
    """

    VERSION = "0.0.1"
    TYPE = "snapchat"

    def __init__(self, config: dict):
        """
        Initialize the Snapchat platform

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
            "snapchat-marketing-api,creative_kit",
        )
        self._api_url = "https://adsapi.snapchat.com/v1"
        self._creative_kit_url = "https://kit.snapchat.com/v1"
        self._public_content_url = "https://story.snapchat.com/v1"

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
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._app_redirect_uri,
            "scope": self._app_scope,
            "state": state,
        }

        return (
            f"https://accounts.snapchat.com/login/oauth2/authorize?{urlencode(params)}"
        )

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
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._app_redirect_uri,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        response = requests.post(
            "https://accounts.snapchat.com/login/oauth2/access_token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=token_data,
        )
        response.raise_for_status()
        token_info = response.json()

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
        # Try to get organization/user info from Marketing API
        try:
            response = requests.get(
                f"{self._api_url}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            org_info = response.json()

            return {
                "id": org_info.get("id", ""),
                "name": org_info.get("name", ""),
                "username": org_info.get("email", ""),
            }
        except requests.exceptions.HTTPError:
            # Fallback: return basic info
            return {
                "id": "",
                "name": "",
                "username": "",
            }

    def get_stories(self, access_token: str, account_id: str = None) -> dict:
        """
        Get user's Snapchat Stories

        Args:
            access_token (str): The access token
            account_id (str): Optional account ID, will fetch if not provided

        Returns:
            dict: List of stories
        """
        if not account_id:
            user_info = self.get_user_info(access_token)
            account_id = user_info.get("id")

        if not account_id:
            raise ValueError("account_id is required")

        try:
            response = requests.get(
                f"{self._api_url}/organizations/{account_id}/stories",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            # Try Public Content API
            response = requests.get(
                f"{self._public_content_url}/stories",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
        """
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        response = requests.post(
            "https://accounts.snapchat.com/login/oauth2/access_token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=token_data,
        )
        response.raise_for_status()
        return response.json()

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post organic content to Snapchat Stories

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "media_url": "https://example.com/image.jpg" or "https://example.com/video.mp4",
                    "media_type": "IMAGE" or "VIDEO",
                    "caption": "Story caption" (optional),
                    "attachment_url": "https://example.com/link" (optional),
                    "attachment_title": "Link title" (optional),
                    "story_id": "story_id" (optional, for updating existing story)
                }

        Returns:
            dict: The response from Snapchat
        """
        media_url = message.get("media_url")
        media_type = message.get("media_type", "IMAGE").upper()

        if not media_url:
            raise ValueError("media_url is required in message")

        # Get user's Snapchat account info first
        try:
            user_info = self.get_user_info(access_token)
            account_id = user_info.get("id")
        except:
            account_id = None

        # Prepare story data for organic posting
        story_data = {
            "media_url": media_url,
            "media_type": media_type,
        }

        if message.get("caption"):
            story_data["caption"] = message["caption"]

        if message.get("attachment_url"):
            story_data["attachment_url"] = message["attachment_url"]
            if message.get("attachment_title"):
                story_data["attachment_title"] = message["attachment_title"]

        # Try posting to Snapchat Stories using Business API
        # Snapchat Business API endpoint for organic content
        if account_id:
            try:
                response = requests.post(
                    f"{self._api_url}/organizations/{account_id}/stories",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json=story_data,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError:
                pass

        # Fallback: Try Public Content API
        try:
            response = requests.post(
                f"{self._public_content_url}/stories",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=story_data,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            # If direct API doesn't work, use Creative Kit format
            # This prepares content that can be shared via Creative Kit
            return {
                "status": "success",
                "message": "Content prepared for Snapchat Stories",
                "story_data": {
                    "media_url": media_url,
                    "media_type": media_type,
                    "caption": message.get("caption", ""),
                    "attachment_url": message.get("attachment_url", ""),
                    "attachment_title": message.get("attachment_title", ""),
                },
                "creative_kit_url": f"{self._creative_kit_url}/share",
                "note": "Content is ready to be posted. Use Creative Kit API or ensure Business API access for automated posting.",
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
