import collections
from typing import Any
from loguru import logger

from dtsdance.ddutil import make_request, output_curl
from .bytecloud import ByteCloudClient


class TaskNotFound(Exception):
    pass


class DFlowNotFound(Exception):
    pass


class DFlowClient:

    def __init__(self, bytecloud_client: ByteCloudClient) -> None:
        self.bytecloud_client = bytecloud_client

    def get_task_info(self, site: str, task_id: str, vregion: str | None = None) -> dict[str, Any]:
        """
        获取 DFlow 任务信息

        Args:
            site: 站点名称
            task_id: DFlow 任务 ID

        Returns:
            dict[str, Any]: DFlow 任务信息，包含 create_time 等字段
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/bytedts/api/bytedts/v3/DescribeTaskInfo"

        # 构建请求数据
        payload = {"id": int(task_id)}

        response_data = make_request("POST", url, self.bytecloud_client.build_request_headers(site, vregion), payload)

        message = response_data.get("message")
        # logger.debug(f"get_task_info {site} {task_id}, message: {message}")

        if message == "task not exists":
            raise TaskNotFound(f"获取 DFlow 任务信息失败，站点: {site}, 任务 ID: {task_id} 不存在")

        try:
            task = response_data.get("data", {}).get("task", {})
            # 提取核心信息
            filtered_data = {
                "task_id": task.get("id", ""),
                "status": task.get("status", ""),
                "desc": task.get("desc", ""),
                "create_time": task.get("create_time", 0),
            }

            return filtered_data

        except (KeyError, AttributeError, Exception) as e:
            raise Exception(f"无法从响应中提取 DFlow 任务信息数据: {str(e)}")

    def get_dflow_info(self, site: str, dflow_id: str, vregion: str | None = None) -> dict[str, Any]:
        """
        获取 DFlow 进程信息

        Args:
            site: 站点名称
            dflow_id: DFlow 进程 ID

        Returns:
            dict[str, Any]: DFlow 进程信息，包含 create_time 等字段
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/bytedts/api/bytedts/v3/DescribeDFlowDetail"

        # 构建请求数据
        payload = {"dflow_id": int(dflow_id)}

        response_data = make_request("POST", url, self.bytecloud_client.build_request_headers(site, vregion), payload)

        message = response_data.get("message", "")
        # logger.debug(f"get_dflow_info {site} {dflow_id}, message: {message}")

        if "dflow not found" in message:
            raise DFlowNotFound(f"获取 DFlow 进程信息失败，站点: {site}, 进程 ID: {dflow_id} 不存在")

        try:
            dflow = response_data.get("data", {}).get("dflow", {})
            # 提取核心信息
            filtered_data = {
                "dflow_id": dflow.get("id", ""),
                "task_id": dflow.get("task_id", ""),
                "app": dflow.get("app", ""),
                "schedule_plan_name": dflow.get("schedule_plan_name", ""),
                "running_state.healthy_status": dflow.get("running_state", {}).get("healthy_status", ""),
            }

            return filtered_data

        except (KeyError, AttributeError, Exception) as e:
            raise Exception(f"无法从响应中提取 DFlow 进程信息数据: {str(e)}")

    def generate_task_url(self, site: str, task_id: str) -> str:
        """
        获取 DFlow 任务详情页面的 URL

        Args:
            site: 站点名称
            task_id: DFlow 任务 ID

        Returns:
            str: DFlow 任务详情页面的 URL
        """
        # 根据环境生成对应的 scope 参数
        site_info = self.bytecloud_client.get_site_config(site)
        return f"{site_info.endpoint}/bytedts/datasync/detail/{task_id}"

    def init_resources(self, site: str, ctrl_env: str) -> bool:
        """
        初始化 CTRL 环境资源

        Args:
            site: 站点名称
            ctrl_env: 控制环境

        Returns:
            bool: CTRL 环境资源初始化结果
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/bytedts/api/bytedts/v3/InitSystemResource"

        # 构建请求数据
        payload = {"ctrl_env": ctrl_env}

        response_data = make_request("POST", url, self.bytecloud_client.build_request_headers(site, None), payload)

        message = response_data.get("message")
        logger.info(f"int_resources {site} {ctrl_env}, message: {message}")

        return message == "ok"

    def list_resources(self, site: str, ctrl_env: str, vregion: str | None = None) -> list[str]:
        """
        列举 CTRL 环境资源列表，连同 agent 列表

        Args:
            site: 站点名称
            ctrl_env: 控制环境
            vregion: 虚拟区域
        Returns:
            list[str]: CTRL 环境资源列表
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/bytedts/api/bytedts/v3/DescribeResources"

        # 构建请求数据
        headers = self.bytecloud_client.build_request_headers(site, vregion)
        payload = {"offset": 0, "limit": 10, "ctrl_env": ctrl_env}
        response_data = make_request("POST", url, headers, payload)

        # curl_cmd = output_curl(url, headers, payload)
        # print(f"Equivalent curl:\n{curl_cmd}")
        
        try:
            data = response_data.get("data", {})
            items = data.get("items", [])
            return [item["name"] for item in items]
        except (KeyError, AttributeError, Exception) as e:
            raise Exception(f"无法从响应中提取 CTRL 环境资源列表数据: {str(e)}")

    def get_all_ctrl_envs(self, site: str) -> dict[str, list[str]]:
        """获取所有可用的控制环境列表，返回以domain为键，ctrl_env列表为值的字典"""
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/bytedts/api/bytedts/v3/DescribeRegions"
        resp_json = make_request("POST", url, self.bytecloud_client.build_request_headers(site, None), {})
        if resp_json["code"] != 0:
            raise Exception(resp_json["message"])

        # print(f"Fetched regions info: {json.dumps(resp_json["data"], ensure_ascii=False, indent=2)}")

        # 提取所有控制环境列表，格式为以domain为键，ctrl_env列表为值的字典
        all_ctrl_envs_by_domain = collections.defaultdict(list[str])

        # 从ops_platform_region中提取ctrl_env_list
        if "bytedts_env" in resp_json["data"]:
            for bytedts_env in resp_json["data"]["bytedts_env"]:
                if "ctrl_env_list" in bytedts_env and "domain" in bytedts_env:
                    env = bytedts_env["env"]
                    region = bytedts_env["include_region"][0] if bytedts_env["include_region"] else "Unknown"
                    env_region_key = env + "|" + region
                    for ctrl_env_item in bytedts_env["ctrl_env_list"]:
                        if "ctrl_env" in ctrl_env_item:
                            ctrl_env = ctrl_env_item["ctrl_env"]
                            # 将ctrl_env添加到domain对应的列表中
                            all_ctrl_envs_by_domain[env_region_key].append(ctrl_env)

        return dict(all_ctrl_envs_by_domain)
