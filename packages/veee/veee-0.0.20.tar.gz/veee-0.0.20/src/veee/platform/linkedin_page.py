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
from typing import List
from urllib.parse import urlencode
from veee.platform.integration import Integration


class LinkedinPage(Integration):
    """
    LinkedIn Page (Organization) Platform

    Posts to LinkedIn Company Pages. Uses the Posts API (rest/posts) with
    organization URN as author. Requires w_organization_social scope.
    """

    VERSION = "0.0.1"
    TYPE = "linkedin_page"

    # LinkedIn API version (YYYYMM format)
    LINKEDIN_VERSION = "202502"

    def __init__(self, config: dict):
        """
        Initialize the LinkedIn Page platform

        Args:
            config (dict): The configuration
        """
        self._client_id = config.get("client_id")
        self._client_secret = config.get("client_secret")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope",
            "openid profile email w_organization_social r_organization_social",
        )
        self._api_url = config.get("api_url", "https://api.linkedin.com/rest")
        self._oauth_url = config.get("oauth_url", "https://www.linkedin.com/oauth/v2")

    def _headers(self, access_token: str) -> dict:
        """Build common API headers"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": self.LINKEDIN_VERSION,
        }

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL

        Args:
            data (dict): The data (e.g. state) for the OAuth redirect URL

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
            data (dict): The data containing the authorization code

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
            dict: The user info (id, name, picture, username)
        """
        userinfo_response = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        return {
            "id": user_info.get("sub"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture", ""),
            "username": user_info.get("preferred_username", ""),
        }

    def get_organizations(self, access_token: str) -> List[dict]:
        """
        Get organizations (Company Pages) the user can post to.

        Fetches organizations where the user has ADMINISTRATOR, CONTENT_ADMIN,
        or DIRECT_SPONSORED_CONTENT_POSTER role.

        Args:
            access_token (str): The access token

        Returns:
            List[dict]: List of organization dicts with 'urn' and 'id' keys
        """
        headers = self._headers(access_token)
        seen_urns = set()
        organizations = []

        # Fetch orgs for each posting role
        for role in (
            "ADMINISTRATOR",
            "CONTENT_ADMIN",
            "DIRECT_SPONSORED_CONTENT_POSTER",
        ):
            params = {
                "q": "roleAssignee",
                "role": role,
                "state": "APPROVED",
            }
            try:
                response = requests.get(
                    f"{self._api_url}/organizationAcls",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException:
                continue

            for elem in data.get("elements", []):
                urn = elem.get("organizationTarget") or elem.get("organization")
                if not urn or urn in seen_urns:
                    continue
                seen_urns.add(urn)
                # Extract numeric ID from urn:li:organization:123456
                org_id = urn.split(":")[-1] if ":" in urn else urn
                organizations.append({"urn": urn, "id": org_id})

        return organizations

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The new access tokens
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

    def _upload_image(
        self, access_token: str, image_path: str, organization_urn: str
    ) -> str:
        """
        Upload an image to LinkedIn and return the image URN.

        Uses the Images API (initializeUpload) for organization-owned images.

        Args:
            access_token (str): The access token
            image_path (str): Path to image file or URL
            organization_urn (str): Organization URN (e.g. urn:li:organization:123)

        Returns:
            str: The image URN (urn:li:image:{id})
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

        # Initialize upload
        init_response = requests.post(
            f"{self._api_url}/images?action=initializeUpload",
            headers=self._headers(access_token),
            json={"initializeUploadRequest": {"owner": organization_urn}},
        )
        init_response.raise_for_status()
        init_result = init_response.json()
        upload_url = init_result["value"]["uploadUrl"]
        image_urn = init_result["value"]["image"]

        # Upload the image
        upload_response = requests.put(
            upload_url,
            headers={"Content-Type": content_type},
            data=image_data,
        )
        upload_response.raise_for_status()
        return image_urn

    def post(self, access_token: str, message: dict) -> dict:
        """
        Post to a LinkedIn Company Page

        Args:
            access_token (str): The access token
            message (dict): The message to post
                - organization_urn: The organization URN (required)
                - text: Post text
                - visibility: PUBLIC or CONNECTIONS (default PUBLIC)
                - image_paths: Optional list of image URLs/paths (1 = single,
                  2-20 = multi-image via MultiImage API)
                - image_alt_texts: Optional list of alt text per image (for
                  accessibility; used with multi-image)

        Returns:
            dict: Response with post ID (from x-restli-id header)
        """
        organization_urn = message.get("organization_urn")
        if not organization_urn:
            raise ValueError("organization_urn is required for LinkedIn Page posts")

        text = message.get("text", "")
        visibility = message.get("visibility", "PUBLIC").upper()
        if visibility not in ("PUBLIC", "CONNECTIONS", "LOGGED_IN"):
            visibility = "PUBLIC"

        image_paths = message.get("image_paths", []) or []
        image_alt_texts = message.get("image_alt_texts", []) or []
        if len(image_paths) > 20:
            raise ValueError(
                "LinkedIn MultiImage API supports maximum 20 images per post"
            )
        asset_urns = []
        for path in image_paths:
            asset_urns.append(self._upload_image(access_token, path, organization_urn))

        post_data = {
            "author": organization_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        if asset_urns:
            if len(asset_urns) >= 2:
                # MultiImage API: 2–20 images
                post_data["content"] = {
                    "multiImage": {
                        "images": [
                            {
                                "id": urn,
                                "altText": image_alt_texts[i]
                                if i < len(image_alt_texts)
                                else "",
                            }
                            for i, urn in enumerate(asset_urns)
                        ]
                    }
                }
            else:
                # Single image
                post_data["content"] = {"media": {"id": asset_urns[0]}}

        response = requests.post(
            f"{self._api_url}/posts",
            headers=self._headers(access_token),
            json=post_data,
        )

        response.raise_for_status()
        post_id = response.headers.get("x-restli-id", "")
        return {"id": post_id}

    def get_account_analytics(self, access_token: str, options: dict = {}) -> list:
        """
        Get the account analytics (not implemented)

        Args:
            access_token (str): The access token
            options (dict): Options for analytics query

        Returns:
            list: Empty list
        """
        return []

    def get_post_analytics(
        self, access_token: str, post_id: str, options: dict = {}
    ) -> list:
        """
        Get the post analytics (not implemented)

        Args:
            access_token (str): The access token
            post_id (str): The post ID
            options (dict): Options for analytics query

        Returns:
            list: Empty list
        """
        return []

    def version(self) -> str:
        return self.VERSION

    def get_type(self) -> str:
        return self.TYPE
