"""TCC (Toutiao Config Center) API client."""

from typing import Any
import requests

from dtsdance.bytecloud import ByteCloudClient
from dtsdance.tcc_open import TCCError


class TCCInnerClient:
    """Client for TCC OpenAPI."""

    def __init__(self, bytecloud_client: ByteCloudClient) -> None:
        self.bytecloud_client = bytecloud_client

    def list_configs(
        self,
        site: str,
        ns_name: str,
        region: str,
        dir: str,
        conf_name: str,
    ) -> list[dict[str, Any]]:
        """
        List TCC configurations.
        """
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v3/tcc/bcc/config/list_v2"

        payload = {
            "ns_name": ns_name,
            "region": region,
            "dir_path": dir,
            "keyword": conf_name,
            "env": "prod",
            "scope": "all",
            "condition": "name",
            "pn": 1,
            "rn": 100,
        }

        try:
            response = requests.post(url, headers=self.bytecloud_client.build_request_headers(site), json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Check for errors in response
            base_resp = result.get("base_resp", {})
            if base_resp.get("error_code", 0) != 0:
                raise TCCError(f"TCC API error: {base_resp.get('error_message', 'Unknown error')}")

            return result.get("data", [])

        except requests.RequestException as e:
            raise TCCError(f"Failed to get TCC config: {str(e)}") from e
