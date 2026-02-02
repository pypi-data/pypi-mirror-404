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
from dataclasses import dataclass
from typing import List
from urllib.parse import urlencode
from veee.platform.integration import Integration


@dataclass
class LinkedinPost:
    """
    Linkedin Post Message
    """

    text: str
    visibility: str
    image_paths: List[str]

    def as_dict(self):
        """
        Convert the Linkedin Post to a dictionary

        Returns:
            dict: The Linkedin Post as a dictionary
        """
        return {
            "text": self.text,
            "visibility": self.visibility.upper(),
            "image_paths": self.image_paths,
        }


class Linkedin(Integration):
    """
    LinkedIn Platform
    """

    VERSION = "0.0.1"
    TYPE = "linkedin"

    def __init__(self, config: dict):
        """
        Initialize the LinkedIn platform

        Args:
            config (dict): The configuration
        """
        self._client_id = config.get("client_id")
        self._client_secret = config.get("client_secret")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "openid profile email w_member_social",
        )
        self._api_url = config.get("api_url", "https://api.linkedin.com/v2")
        self._oauth_url = config.get("oauth_url", "https://www.linkedin.com/oauth/v2")

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
            "state": state,
            "scope": self._app_scope,
        }

        return f"{self._oauth_url}/authorization?{urlencode(params)}"

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
            f"{self._oauth_url}/accessToken",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
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
        userinfo_response = requests.get(
            f"{self._api_url}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        username = ""
        profile_response = requests.get(
            f"{self._api_url}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_response.ok:
            username = profile_response.json().get("vanityName", "")

        return {
            "id": user_info.get("sub"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture", ""),
            "username": username,
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
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        response = requests.post(
            f"{self._oauth_url}/accessToken",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=token_data,
        )

        response.raise_for_status()
        return response.json()

    def _upload_image(self, access_token: str, image_path: str, profile_id: str) -> str:
        """
        Upload an image to LinkedIn and return the asset URN

        Args:
            access_token (str): The access token
            image_path (str): Path to the image file or URL to the image
            profile_id (str): The LinkedIn profile ID

        Returns:
            str: The asset URN (urn:li:image:{id})
        """
        if image_path.startswith(("http://", "https://")):
            response = requests.get(image_path)
            response.raise_for_status()
            image_data = response.content
            content_type = response.headers.get("Content-Type", "image/jpeg")
        else:
            with open(image_path, "rb") as f:
                image_data = f.read()
            if image_path.lower().endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif image_path.lower().endswith(".png"):
                content_type = "image/png"
            elif image_path.lower().endswith(".gif"):
                content_type = "image/gif"
            else:
                content_type = "image/jpeg"

        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{profile_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        register_response = requests.post(
            f"{self._api_url}/assets?action=registerUpload",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=register_data,
        )

        register_response.raise_for_status()
        register_result = register_response.json()
        upload_url = register_result["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn = register_result["value"]["asset"]

        upload_response = requests.put(
            upload_url,
            headers={"Content-Type": content_type},
            data=image_data,
        )
        upload_response.raise_for_status()
        return asset_urn

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post to LinkedIn

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "text": "Post text",
                    "visibility": "PUBLIC" or "CONNECTIONS",
                    "image_paths": ["/path/to/image1.jpg", "https://example.com/image2.jpg"] (optional, supports multiple images)
                }

        Returns:
            dict: The response from LinkedIn
        """
        user_info = self.get_user_info(access_token)
        profile_id = user_info.get("id")
        if not profile_id:
            raise ValueError("Could not resolve member id from userinfo")
        author_urn = f"urn:li:person:{profile_id}"

        share_content = {
            "shareCommentary": {
                "text": message.get("text", ""),
            },
        }

        image_paths = message.get("image_paths", []) or []
        asset_urns = []
        for image_path in image_paths:
            asset_urns.append(self._upload_image(access_token, image_path, profile_id))

        if asset_urns:
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "media": asset_urn,
                }
                for asset_urn in asset_urns
            ]
        else:
            share_content["shareMediaCategory"] = "NONE"

        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": message.get(
                    "visibility", "PUBLIC"
                ),
            },
        }

        response = requests.post(
            f"{self._api_url}/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
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
