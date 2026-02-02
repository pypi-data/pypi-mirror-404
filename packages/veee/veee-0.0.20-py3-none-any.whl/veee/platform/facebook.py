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


class Facebook(Integration):
    """
    Facebook Platform
    """

    VERSION = "0.0.1"
    TYPE = "facebook"

    def __init__(self, config: dict):
        """
        Initialize the Facebook platform

        Args:
            config (dict): The configuration
        """
        self._app_id = config.get("app_id")
        self._app_secret = config.get("app_secret_key")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "pages_show_list,pages_manage_posts,pages_read_engagement,business_management",
        )
        self._api_url = config.get("api_url", "https://graph.facebook.com/v20.0")

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
            "state": state,
            "scope": self._app_scope,
        }

        return f"{self._api_url}/dialog/oauth?{urlencode(params)}"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens (access_token, refresh_token, expires_in)

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: The access tokens
        """
        code = data.get("code", "")

        # Exchange code for short-lived access token
        token_params = {
            "client_id": self._app_id,
            "redirect_uri": self._app_redirect_uri,
            "client_secret": self._app_secret,
            "code": code,
        }

        token_response = requests.get(
            f"{self._api_url}/oauth/access_token",
            params=token_params,
        )
        token_response.raise_for_status()
        short_token_info = token_response.json()
        short_access_token = short_token_info.get("access_token")

        # Exchange short-lived token for long-lived token
        long_token_params = {
            "grant_type": "fb_exchange_token",
            "client_id": self._app_id,
            "client_secret": self._app_secret,
            "fb_exchange_token": short_access_token,
        }

        long_token_response = requests.get(
            f"{self._api_url}/oauth/access_token",
            params=long_token_params,
        )
        long_token_response.raise_for_status()
        long_token_info = long_token_response.json()

        return {
            "access_token": long_token_info.get("access_token"),
            "refresh_token": long_token_info.get(
                "access_token"
            ),  # Facebook uses same token
            "expires_in": long_token_info.get("expires_in", 5184000),
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
                "fields": "id,name,picture",
                "access_token": access_token,
            },
        )
        response.raise_for_status()
        user_info = response.json()

        picture_url = ""
        if user_info.get("picture") and user_info["picture"].get("data"):
            picture_url = user_info["picture"]["data"].get("url", "")

        return {
            "id": user_info.get("id"),
            "name": user_info.get("name"),
            "picture": picture_url,
            "username": user_info.get("name", "").lower().replace(" ", "."),
        }

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens (Facebook uses same token for refresh)

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
        """
        # Facebook long-lived tokens can be refreshed by exchanging again
        return {
            "access_token": refresh_token,
            "refresh_token": refresh_token,
            "expires_in": 5184000,
            "token_type": "bearer",
        }

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post a message to Facebook Page

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "page_id": "page_id",
                    "message": "Post text",
                    "link": "https://example.com" (optional)
                }

        Returns:
            dict: The response from Facebook
        """
        page_id = message.get("page_id")
        if not page_id:
            raise ValueError("page_id is required in message")

        post_data = {
            "message": message.get("message", ""),
            "access_token": access_token,
        }

        if message.get("link"):
            post_data["link"] = message["link"]

        response = requests.post(
            f"{self._api_url}/{page_id}/feed",
            data=post_data,
        )
        response.raise_for_status()
        return response.json()

    def get_pages(self, access_token: str) -> dict:
        """
        Get user's Facebook pages

        Args:
            access_token (str): The access token

        Returns:
            dict: The pages list
        """
        response = requests.get(
            f"{self._api_url}/me/accounts",
            params={
                "access_token": access_token,
                "fields": "id,name,access_token",
            },
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
