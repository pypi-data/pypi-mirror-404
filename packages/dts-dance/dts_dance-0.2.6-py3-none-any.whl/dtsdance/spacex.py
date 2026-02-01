from typing import Any, NamedTuple
from .bytecloud import ByteCloudClient
import requests
from loguru import logger


class GatewayInfo(NamedTuple):
    mgr_name: str
    ctrl_name: str
    gateway_endpoint: str
    auth_user: str
    auth_password: str
    root_secret_key: str
    gw_meta_db: str


class SpaceXClient:
    """
    SpaceX 通知服务客户端，用于发送飞书消息
    """

    def __init__(self, bytecloud_client: ByteCloudClient):
        """
        初始化 SpaceX 通知客户端
        """
        self.bytecloud_client = bytecloud_client

    def list_mgr(self, site: str) -> list[Any]:
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint_bytedts_spacex}/bytedts/v1/queryServerMeta"

        try:
            response = requests.post(url, headers=self.bytecloud_client.build_request_headers(site))
            response.raise_for_status()

            result = response.json()
            return result.get("data", [])

        except Exception as e:
            logger.warning(f"do quest queryServerMeta exception: {e}")
            raise

    def register_resource(self, site: str, payload: dict[str, Any]) -> bool:
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint_bytedts_spacex}/resource/v1/registerResource"
        try:
            response = requests.post(url, json=payload, headers=self.bytecloud_client.build_request_headers(site))
            # print(f"response status code: {response.status_code}, response text: {response.text}")

            response.raise_for_status()

            result = response.json()
            return result.get("message", "") == "ok"

        except Exception as e:
            logger.warning(f"do quest registerResource exception: {e}")
            raise

    def list_resources(self, site: str, payload: dict[str, Any]) -> list[str]:
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint_bytedts_spacex}/resource/v1/listResource"
        try:
            response = requests.post(url, json=payload, headers=self.bytecloud_client.build_request_headers(site))
            # print(f"response status code: {response.status_code}, response text: {response.text}")

            response.raise_for_status()

            result = response.json()
            if not result.get("message", "") == "ok":
                return []

            items = result.get("data", {}).get("items", [])
            return [item["name"] for item in items]
        except Exception as e:
            logger.warning(f"do quest listResource exception: {e}")
            raise

    def register_gateway(self, site: str, gateway_info: GatewayInfo) -> bool:
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint_bytedts_spacex}/bytedts/v1/registryGateway"
        payload = {
            "region": gateway_info.mgr_name,
            "server_region": gateway_info.mgr_name,
            "cluster_region": gateway_info.ctrl_name,
            "cluster_name": gateway_info.ctrl_name,
            "server_domain": gateway_info.gateway_endpoint,
            "frontend_user": gateway_info.auth_user,
            "gateway_user": gateway_info.auth_user,
            "root_secret_key": gateway_info.root_secret_key,
            "gateway_password": gateway_info.auth_password,
            "frontend_password": gateway_info.auth_password,
            "gw_meta_db": gateway_info.gw_meta_db,
            "gateway_type": "psm",
            "runtime_psm": "bytedts.dflow.rownott",
            "tao_service_name": "inf.bytedts.agent",
            "tao_service_node_id": 1071,
            "unified_tao_service": 1,
        }
        try:
            response = requests.post(url, json=payload, headers=self.bytecloud_client.build_request_headers(site))
            response.raise_for_status()

            result = response.json()
            return result.get("message", "") == "ok"

        except Exception as e:
            logger.warning(f"do quest registryGateway exception: {e}")
            raise

    def gateway_operation(self, site: str, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint_bytedts_spacex}/bytedts/v1/{operation}"
        try:
            response = requests.post(url, json=payload, headers=self.bytecloud_client.build_request_headers(site))
            # print(f"response status code: {response.status_code}, response text: {response.text}")

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"do quest gateway_operation exception: {e}")
            raise
