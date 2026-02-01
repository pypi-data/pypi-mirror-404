"""TCC (Toutiao Config Center) API client."""

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class TCCConfigItem:
    """Single TCC configuration item."""

    conf_name: str
    value: str
    description: str
    data_type: str


class TCCError(Exception):
    pass


class TCCItemNotFound(Exception):
    pass


class TCCClient:
    """Client for TCC OpenAPI."""

    def __init__(self, svc_account: str, svc_secret: str, endpoint: str):
        self.svc_account = svc_account
        self.svc_secret = svc_secret
        self.endpoint = endpoint

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.svc_secret}",
        }

    def publish_config(
        self,
        ns_name: str,
        region: str,
        dir: str,
        conf_name: str,
        value: str,
        description: str,
        data_type: str,
    ) -> dict[str, Any]:
        """
        Create or update TCC configuration.

        Returns:
            Response data containing config_id and deployment_id

        Raises:
            TCCError: If API call fails
        """
        url = f"{self.endpoint}/api/v1/tcc_v3_openapi/bcc/open/config/update"

        payload = {
            "ns_name": ns_name,
            "dir": dir,
            "conf_name": conf_name,
            "value": str(value),
            "data_type": data_type,
            "region": region,
            "description": description,
            "operator": self.svc_account,
            "update_strategy": "modify_and_deploy",
            "auto_create": "auto_create_dir_config",  # 自动创建还未存在的目录和配置
        }

        try:
            # print(f"writing tcc config, payload: {payload}")
            response = requests.post(url, headers=self._build_headers(), json=payload, timeout=30)
            if response.status_code != 200:
                raise TCCError(f"TCC API request failed with status {response.status_code}\n" f"Response: {response.text}")

            result = response.json()

            # Check for errors in response
            base_resp = result.get("base_resp", {})
            if base_resp.get("error_code", 0) != 0:
                raise TCCError(f"TCC API error: {base_resp.get('error_message', 'Unknown error')}")

            return result.get("data", {})

        except requests.RequestException as e:
            raise TCCError(f"Failed to create TCC config: {str(e)}") from e

    def _list(
        self,
        ns_name: str,
        region: str,
        dir: str,
        page: int = 1,
        page_size: int = 100,
        with_value: bool = True,
    ) -> dict[str, Any]:
        """
        List TCC configurations.

        Args:
            ns_name: Namespace name
            region: Region (default: "China-BOE")
            dir: Directory path (default: "/default")
            page: Page number (default: 1)
            page_size: Page size (default: 100)

        Returns:
            Configuration data

        Raises:
            TCCError: If API call fails
        """
        url = f"{self.endpoint}/api/v1/tcc_v3_openapi/bcc/open/config/list"

        params = {
            "ns_name": ns_name,
            "dir": dir,
            "region": region,
            "with_value": with_value,
            "page": page,
            "page_size": page_size,
        }

        try:
            response = requests.post(url, headers=self._build_headers(), params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Check for errors in response
            base_resp = result.get("base_resp", {})
            if base_resp.get("error_code", 0) != 0:
                raise TCCError(f"TCC API error: {base_resp.get('error_message', 'Unknown error')}")

            return result

        except requests.RequestException as e:
            raise TCCError(f"Failed to get TCC config: {str(e)}") from e

    def list_all(
        self,
        ns_name: str,
        region: str,
        dir: str,
        with_value: bool = True,
    ) -> list[dict[str, Any]]:
        """
        List all TCC configurations across all pages.

        Args:
            ns_name: Namespace name
            region: Region (default: "China-BOE")
            dir: Directory path (default: "/default")

        Returns:
            List of all configuration items

        Raises:
            TCCError: If API call fails
        """
        all_items = []
        page = 1
        page_size = 100

        while True:
            result = self._list(region=region, ns_name=ns_name, dir=dir, page=page, page_size=page_size, with_value=with_value)

            # Extract items from current page
            data = result.get("data", {})
            items = data.get("items", [])
            all_items.extend(items)

            # Check if there are more pages
            page_info = result.get("page_info", {})
            total_page = page_info.get("total_page", 1)

            if page >= total_page:
                break

            page += 1

        return all_items

    def list_all_names(
        self,
        ns_name: str,
        region: str,
        dir: str,
    ) -> list[str]:
        items = self.list_all(ns_name, region, dir, False)
        return [item.get("conf_name", "") for item in items]

    def get_config(
        self,
        ns_name: str,
        region: str,
        dir: str,
        conf_name: str,
    ) -> dict[str, Any]:
        """
        Get TCC configuration.

        Args:
            ns_name: Namespace name
            region: Region (default: "China-BOE")
            conf_name: Configuration name
            dir: Directory path (default: "/default")

        Returns:
            Configuration data

        Raises:
            TCCError: If API call fails
        """
        url = f"{self.endpoint}/api/v1/tcc_v3_openapi/bcc/open/config/get"

        params = {
            "ns_name": ns_name,
            "dir": dir,
            "region": region,
            "conf_name": conf_name,
        }

        try:
            response = requests.get(url, headers=self._build_headers(), params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Check for errors in response
            base_resp = result.get("base_resp", {})
            if base_resp.get("error_code", 0) != 0:
                error_message = base_resp.get("error_message", "Unknown error")
                if "reason:RESOURCE_NOT_FOUND" in error_message:
                    raise TCCItemNotFound(f"TCC Item not found error: {error_message}")

                raise TCCError(f"TCC API error: {error_message}")

            return result.get("data", {})

        except requests.RequestException as e:
            raise TCCError(f"Failed to get TCC config: {str(e)}") from e
