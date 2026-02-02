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

from abc import ABC, abstractmethod


class Integration(ABC):
    """Integration Base Class"""

    @abstractmethod
    def get_oauth_redirect_url(self, data: dict) -> str:
        """Get the OAuth redirect URL"""
        pass

    @abstractmethod
    def get_access_tokens(self, data: dict) -> dict:
        """Get the access tokens (access_token, refresh_token, expires_in)"""
        pass

    @abstractmethod
    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """Rotate the access tokens (access_token, refresh_token, expires_in)"""
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> dict:
        """Get the user info"""
        pass

    @abstractmethod
    def post(self, access_token: str, message: dict) -> dict:
        """Post a message to the integration"""
        pass

    @abstractmethod
    def get_account_analytics(self, access_token: str, options: dict = {}) -> list:
        """Get the account analytics of the integration"""
        pass

    @abstractmethod
    def get_post_analytics(
        self, access_token: str, post_id: str, options: dict = {}
    ) -> list:
        """Get the post analytics of the integration"""
        pass

    @abstractmethod
    def version(self) -> str:
        """Get the version of the integration"""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """Get the type of the integration"""
        pass
