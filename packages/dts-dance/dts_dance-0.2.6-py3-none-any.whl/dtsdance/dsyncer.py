from dtsdance.ddutil import make_request
from .bytecloud import ByteCloudClient
from typing import Any, NamedTuple, Tuple, cast, Optional
from loguru import logger
import re
from datetime import datetime

DSyncer_Task_Detail_URL = "{endpoint}/dsyncer/tasks/all?task_id_list={task_id}"
DSyncer_Backlog_Dashboard_URL = "https://grafana.sretools.bytedance.net/d/b1cad70c-8ce3-490c-be48-fbcab32c7a2e/dsyncer-backlog?orgId=1&from=now-1h&to=now&timezone=browser&refresh=1m"
DSyncer_N8N_OPT_URL = "https://n8n.sretools.bytedance.net/webhook/Xt73CZPpKjMu?opt={opt}&env={env}&task_id={task_id}"


class DSyncerEnvInfo(NamedTuple):
    name: str
    token: str


class DSyncerClient:

    def __init__(self, envs: dict[str, DSyncerEnvInfo], bytecloud_client: ByteCloudClient) -> None:
        self.envs = envs
        self.bytecloud_client = bytecloud_client

    def _build_headers(self, site: str, secret_api: bool = False) -> dict[str, str]:
        """
        构建请求头

        Args:
            env: 环境名称
            include_auth: 是否包含 Authorization 头

        Returns:
            dict[str, str]: 请求头字典
        """
        jwt_token = self.bytecloud_client.get_jwt_token(site)
        headers = {"X-Jwt-Token": jwt_token}

        if secret_api:
            token = self.envs[site].token
            headers["Authorization"] = f"Token {token}"

        return headers

    def _acquire_task_info(self, site: str, task_id: str) -> dict[str, str]:
        """
        获取 DSyncer 任务信息

        Args:
            site: 站点名称
            task_id: DSyncer 任务 ID

        Returns:
            dict[str, str]: DSyncer 任务的 rocket_mq_connection 信息，只包含 cluster、topic 和 group 字段
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/dsyncer/openapi/taskinfo/{task_id}/"

        # 准备请求头
        headers = self._build_headers(site)

        return make_request("GET", url, headers)

    def get_dflow_task_info(self, site: str, task_id: str) -> tuple[str, str]:
        """
        获取迁移后的 DFlow 任务信息
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/dsyncer/openapi/taskinfo/{task_id}/migrate/"

        # 准备请求头
        headers = self._build_headers(site)

        json_data = make_request("GET", url, headers)

        message = json_data.get("message", "")
        logger.debug(f"get task migrate info {site} {task_id}, message: {message}")

        # 从消息中提取 DFlow 任务 URL 和 ID
        # 消息格式: "任务已迁移至ByteDTS平台，请前往[https://cloud.bytedance.net/bytedts/datasync/detail/93127366537986?scope=China-North&tabKey=DetailInfo]查看详情"

        # 提取完整的 URL
        url_pattern = r"\[(https://[^\]]+)\]"
        url_match = re.search(url_pattern, message)

        # 提取任务 ID
        id_pattern = r"/bytedts/datasync/detail/(\d+)"
        id_match = re.search(id_pattern, message)

        if url_match and id_match:
            dflow_task_url = url_match.group(1)
            dflow_task_id = id_match.group(1)
            logger.info(f"extracted dflow task_url: {dflow_task_url}, task_id: {dflow_task_id}")
            return (dflow_task_url, dflow_task_id)
        else:
            logger.warning(f"could not extract dflow task info from message: {message}")
            return ("", "")

    def generate_task_url(self, site: str, task_id: str) -> str:
        """
        获取 DSyncer 任务详情页面的 URL

        Args:
            env: 环境名称
            task_id: DSyncer 任务 ID

        Returns:
            str: DSyncer 任务详情页面的 URL
        """
        site_info = self.bytecloud_client.get_site_config(site)
        return DSyncer_Task_Detail_URL.format(endpoint=site_info.endpoint, task_id=task_id)

    def generate_task_grafana_url(self, task_id: str, change_time: str) -> str:
        """
        获取 DSyncer 任务的 Grafana 监控页面 URL
        """
        try:
            # 将 change_time 字符串转换为毫秒时间戳
            dt = datetime.strptime(change_time, "%Y-%m-%d %H:%M:%S")
            change_time_timestamp = int(dt.timestamp() * 1000)
        except ValueError as e:
            logger.warning(f"无法解析时间格式 '{change_time}': {e}，使用当前时间戳")
            change_time_timestamp = int(datetime.now().timestamp() * 1000)

        return f"{DSyncer_Backlog_Dashboard_URL}&var-change_time={change_time_timestamp}&var-task_id={task_id}"

    def get_task_info(self, env: str, task_id: str) -> dict[str, Any]:
        """
        获取 DSyncer 任务状态

        Args:
            env: 环境名称
            task_id: DSyncer 任务 ID

        Returns:
            dict[str, str]: DSyncer 任务状态
        """
        json_data = self._acquire_task_info(env, task_id)
        if json_data.get("code") == 400 and "message" in json_data:
            raise Exception(json_data.get("message", "未知错误"))

        logger.info(f"get_task_info success {env} {task_id}")

        try:
            data = cast(dict, json_data.get("data", {}))
            increment_task = cast(dict, data.get("increment_task", {}))
            rocket_mq_connection = cast(dict, increment_task.get("rocket_mq_connection", {}))
            filtered_data = {
                "task_id": data.get("task_id", ""),
                "status": data.get("status", ""),
                "desc": data.get("desc", ""),
                "scene": data.get("scene", ""),
                "psm": data.get("psm", ""),
                "increment_task_id": increment_task.get("task_id", ""),
                "mq_info": {
                    "cluster": rocket_mq_connection.get("cluster", ""),
                    "topic": rocket_mq_connection.get("topic", ""),
                    "group": rocket_mq_connection.get("group", ""),
                },
            }

            return filtered_data
        except (KeyError, AttributeError, Exception) as e:
            raise Exception(f"无法从响应中提取 DSyncer 任务状态数据: {str(e)}")

    def is_task_migrate_running(self, site: str, task_id: str) -> Tuple[bool, str]:
        """
        检查 DSyncer 任务是否正在迁移中

        Returns:
            bool: 如果任务正在迁移中，返回 True；否则返回 False
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/dsyncer/secret_api/task/migrate/check"

        # 准备请求头
        headers = self._build_headers(site, secret_api=True)

        payload = {"task_id": task_id}

        response_data = make_request("POST", url, headers, payload)

        message = response_data.get("message", "")
        logger.debug(f"get task migrate status {site} {task_id}, message: {message}")
        if "task migrate is running" in message:
            return True, ""
        else:
            return False, response_data.get("data", {}).get("msg", {})

    def migration_rollback(self, site: str, task_id: str) -> bool:
        """
        执行回滚
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/dsyncer/secret_api/task/rollback_migrate2dsyncer/"

        # 准备请求头
        headers = self._build_headers(site, secret_api=True)

        payload = {"task_id_list": [task_id]}

        response_data = make_request("POST", url, headers, payload)

        logger.debug(f"migration_mark_rollback return {site} {task_id}, json_data: {response_data}")
        success_task = response_data.get("data", {}).get("success_task", [])
        return task_id in success_task

    def migration_mark_success(self, site: str, task_id: str) -> bool:
        """
        标记迁移成功
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/dsyncer/secret_api/task/mark_migrate_success/"

        # 准备请求头
        headers = self._build_headers(site, secret_api=True)

        payload = {"task_id": task_id}

        response_data = make_request("POST", url, headers, payload)

        logger.debug(f"migration_mark_success return {site} {task_id}, json_data: {response_data}")
        success_task = response_data.get("data", {}).get("success_task", [])
        return task_id in success_task

    def migrate_task(self, site: str, task_id: str, app_parallel: int) -> Optional[str]:
        """
        迁移任务到DFlow

        Returns:
            Optional[str]: 错误信息，成功时返回None，失败时返回错误信息
        """
        # 构建 API URL
        site_info = self.bytecloud_client.get_site_config(site)
        url = f"{site_info.endpoint}/api/v1/dsyncer/secret_api/task/migrate2dflow/single"

        # 准备请求头
        headers = self._build_headers(site, secret_api=True)

        payload = {
            "task_id": task_id,
            "delay_threshold": "20s",
            "dsyncer_task_pause_threshold": "180s",
            "dflow_delay_threshold": "1m",
            "dflow_diff_threshold": 100,
            "check_minutes": 10,
            "enable_psm": True,
            "disable_check": True,
            "app_parallel": app_parallel,
        }

        response_data = make_request("POST", url, headers, payload)

        logger.debug(f"migrate_task return {site} {task_id}, json_data: {response_data}")
        message = response_data.get("message")
        if response_data.get("code") == 0 and message == "ok":
            err_message = None
        else:
            err_message = message

        return err_message
