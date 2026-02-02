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
from veee.platform.facebook import Facebook


class Instagram(Facebook):
    """
    Instagram Platform (extends Facebook since Instagram uses Facebook OAuth)
    """

    VERSION = "0.0.1"
    TYPE = "instagram"

    def __init__(self, config: dict):
        """
        Initialize the Instagram platform

        Args:
            config (dict): The configuration
        """
        super().__init__(config)
        # Instagram requires additional scopes
        self._app_scope = config.get(
            "app_scope",
            "instagram_basic,pages_show_list,pages_read_engagement,business_management,instagram_content_publish,instagram_manage_comments,instagram_manage_insights",
        )

    def get_instagram_account(self, access_token: str, page_id: str) -> dict:
        """
        Get Instagram Business Account ID from Facebook Page

        Args:
            access_token (str): Facebook access token
            page_id (str): Facebook page ID

        Returns:
            dict: Instagram account information
        """
        response = requests.get(
            f"{self._api_url}/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": access_token,
            },
        )
        response.raise_for_status()
        return response.json()

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post to Instagram

        Args:
            access_token (str): The access token
            message (dict): The message to be posted
                {
                    "instagram_account_id": "instagram_account_id",
                    "image_url": "https://example.com/image.jpg",
                    "caption": "Post caption"
                }

        Returns:
            dict: The response from Instagram
        """
        instagram_account_id = message.get("instagram_account_id")
        if not instagram_account_id:
            raise ValueError("instagram_account_id is required in message")

        # Create media container
        media_data = {
            "image_url": message.get("image_url"),
            "caption": message.get("caption", ""),
            "access_token": access_token,
        }

        # Step 1: Create media container
        container_response = requests.post(
            f"{self._api_url}/{instagram_account_id}/media",
            data=media_data,
        )
        container_response.raise_for_status()
        container_info = container_response.json()
        creation_id = container_info.get("id")

        # Step 2: Publish the media container
        publish_data = {
            "creation_id": creation_id,
            "access_token": access_token,
        }

        publish_response = requests.post(
            f"{self._api_url}/{instagram_account_id}/media_publish",
            data=publish_data,
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

    def get_type(self) -> str:
        return self.TYPE
