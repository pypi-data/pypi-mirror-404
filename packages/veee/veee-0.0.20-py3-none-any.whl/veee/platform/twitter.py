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

import secrets
import hashlib
import base64
import requests
from dataclasses import dataclass
from typing import List
from urllib.parse import urlencode
from veee.platform.integration import Integration


@dataclass
class TwitterPost:
    """
    Twitter Post Message
    """

    text: str
    media_paths: List[str]

    def as_dict(self):
        """
        Convert the Twitter Post to a dictionary

        Returns:
            dict: The Twitter Post as a dictionary
        """
        return {
            "text": self.text,
            "media_paths": self.media_paths,
        }


class Twitter(Integration):
    """
    Twitter/X Platform
    """

    VERSION = "0.0.1"
    TYPE = "twitter"

    def __init__(self, config: dict):
        """
        Initialize the Twitter platform

        Args:
            config (dict): The configuration
        """
        self._client_id = config.get("client_id")
        self._client_secret = config.get("client_secret")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "tweet.read tweet.write users.read offline.access media.write",
        )
        self._api_url = config.get("api_url", "https://api.x.com/2")
        self._upload_api_url = config.get(
            "upload_api_url", "https://api.x.com/2/media/upload"
        )

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL

        Args:
            data (dict): The data to be used to generate the OAuth redirect URL

        Returns:
            str: The OAuth redirect URL
        """
        state = data.get("state", "")
        code_verifier = data.get("code_verifier") or secrets.token_urlsafe(32)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._app_redirect_uri,
            "scope": self._app_scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        return f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"

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

        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()

        token_data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "redirect_uri": self._app_redirect_uri,
            "code_verifier": code_verifier,
        }

        response = requests.post(
            f"{self._api_url}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
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
            f"{self._api_url}/users/me",
            params={"user.fields": "id,name,username,profile_image_url"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        user_data = response.json().get("data", {})
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "username": user_data.get("username"),
            "picture": user_data.get("profile_image_url", ""),
        }

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
        """
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()

        token_data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": self._client_id,
        }

        response = requests.post(
            f"{self._api_url}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
            data=token_data,
        )
        response.raise_for_status()
        return response.json()

    def _upload_media(self, access_token: str, media_path: str = None) -> str:
        """
        Upload media (image) to Twitter using API v2

        Args:
            access_token (str): The OAuth 2.0 access token
            media_path (str, optional): Path to the image file or URL to the image

        Returns:
            str: The media_id from Twitter
        """
        if media_path.startswith(("http://", "https://")):
            response = requests.get(media_path)
            response.raise_for_status()
            media_data = response.content
            content_type = response.headers.get("Content-Type", "image/png")
        else:
            with open(media_path, "rb") as f:
                media_data = f.read()
            if media_path.lower().endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif media_path.lower().endswith(".gif"):
                content_type = "image/gif"
            elif media_path.lower().endswith(".webp"):
                content_type = "image/webp"
            else:
                content_type = "image/png"

        payload = {
            "media": base64.b64encode(media_data).decode("utf-8"),
            "media_category": "tweet_image",
            "media_type": content_type,
        }

        response = requests.post(
            f"{self._upload_api_url}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        response.raise_for_status()
        result = response.json()

        if "errors" in result and result["errors"]:
            error = result["errors"][0]
            raise Exception(
                f"Media upload error: {error.get('title', 'Unknown error')} - "
                f"{error.get('detail', 'No details')}"
            )

        if "data" not in result or "id" not in result["data"]:
            raise Exception("Invalid response format: missing data.id")

        return str(result["data"]["id"])

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post a tweet

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "text": "Tweet text",
                    "image_path": ["/path/to/image.jpg", "https://example.com/image.jpg"] (optional),
                }

        Returns:
            dict: The response from Twitter
        """
        data = {
            "text": message.get("text", ""),
        }

        media_ids = []
        media_paths = message.get("media_paths", []) or []
        for media_path in media_paths:
            media_ids.append(self._upload_media(access_token, media_path=media_path))

        if len(media_ids) > 0:
            data["media"] = {"media_ids": media_ids}

        response = requests.post(
            f"{self._api_url}/tweets",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=data,
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
