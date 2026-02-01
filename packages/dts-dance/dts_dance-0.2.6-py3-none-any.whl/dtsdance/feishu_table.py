from datetime import datetime
import threading
from typing import Callable, Any
from loguru import logger
import requests

from .feishu_base import FeishuBase

URL_FEISHU_OPEN_API: str = "https://fsopen.bytedance.net/open-apis"


class FeishuTable:
    """飞书表格类，支持自动token续期管理"""

    def __init__(self, feishu_base: FeishuBase, table_app_token: str, table_id: str):
        """
        初始化飞书表格
        """
        self.tenant_access_token: str | None = None
        self.token_expire_time: datetime | None = None
        self._token_lock = threading.Lock()

        self.feishu_base = feishu_base
        self.table_app_token = table_app_token
        self.table_id = table_id

    def get_app_table_record_id(self, table_view_id: str, task_id: str) -> str | None:
        """
        根据任务ID查询飞书多维表格记录，返回记录ID
        """
        # 构建请求体
        payload = {
            "view_id": table_view_id,
            "filter": {"conditions": [{"field_name": "任务id", "operator": "is", "value": [task_id]}], "conjunction": "and"},
        }

        try:
            endpoint = f"/bitable/v1/apps/{self.table_app_token}/tables/{self.table_id}/records/search"
            response = self.feishu_base.make_request("POST", endpoint, json=payload)
            result = response.json()
            if result.get("code") != 0:
                logger.warning(f"get_app_table_record_id {task_id} 失败: {result}")
                return None

            # 提取记录数据
            data = result.get("data", {})
            items = data.get("items", [])
            if not items:
                logger.warning(f"get_app_table_record_id {task_id} 失败: items为空")
                return None

            # 返回第一个匹配记录的record_id
            record_id = items[0].get("record_id")
            logger.info(f"成功查询到任务ID {task_id} 对应的记录ID: {record_id}")

            return record_id

        except Exception as e:
            logger.warning(f"查询 {task_id} 表格记录失败: {e}")
            return None

    def update_app_table_record(self, record_id: str, fields: dict[str, Any]) -> bool:
        """
        更新飞书多维表格记录

        Args:
            record_id: 记录ID
            fields: 要更新的字段，格式为 {"字段名": "字段值"}

        Returns:
            是否更新成功
        """
        # 构建请求体
        payload = {"fields": fields}

        try:
            endpoint = f"/bitable/v1/apps/{self.table_app_token}/tables/{self.table_id}/records/{record_id}"
            response = self.feishu_base.make_request("PUT", endpoint, json=payload)
            result = response.json()
            if result.get("code") != 0:
                logger.warning(f"更新表格记录失败: {result.get('msg')}")
                return False

            # logger.debug(f"成功更新记录ID {record_id}，字段: {fields}")
            return True

        except Exception as e:
            logger.warning(f"更新表格记录失败: {e}")
            return False

    def fetch_records(self, table_view_id: str, field_names: list[str], page_size: int = 100, page_token: str | None = None) -> dict[str, Any]:
        """
        获取表格记录

        Args:
            page_size: 每页记录数，最大500
            page_token: 分页标记

        Returns:
            API响应数据
        """
        endpoint = f"/bitable/v1/apps/{self.table_app_token}/tables/{self.table_id}/records/search"
        params = {"page_size": page_size, "user_id_type": "open_id"}
        if page_token:
            params["page_token"] = page_token

        payload = {"field_names": field_names, "view_id": table_view_id}

        try:
            response = self.feishu_base.make_request("POST", endpoint, json=payload, params=params)
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"API请求失败: {result.get('msg')}")

            return result.get("data", {})

        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            raise

    def parse_record(self, record: dict[str, Any], field_names: list[str] | None = None) -> dict[str, str]:
        """
        解析单条记录，动态提取指定字段

        Args:
            record: 飞书表格记录
            field_names: 需要解析的字段名列表，如果为None则解析所有字段

        Returns:
            解析后的记录信息，包含record_id和指定的字段
        """
        fields = record.get("fields", {})
        result = {"record_id": record.get("record_id", "")}

        # 如果没有指定字段名，则解析所有字段
        target_fields = field_names if field_names else list(fields.keys())

        # 动态解析每个字段
        for field_name in target_fields:
            field_value = fields.get(field_name, [])

            # 处理文本类型字段（列表格式）
            if field_value and isinstance(field_value, list) and len(field_value) > 0:
                # 如果是字典且包含text字段
                if isinstance(field_value[0], dict) and "text" in field_value[0]:
                    result[field_name] = field_value[0].get("text", "")
                else:
                    # 其他类型直接取第一个元素
                    result[field_name] = str(field_value[0])
            else:
                # 空值或非列表类型
                result[field_name] = field_value

        return result

    def loop_all(
        self, table_view_id: str, field_names: list[str], callback: Callable[[dict[str, str]], None] | None = None, limit: int | None = None
    ):
        """
        遍历视图中的所有记录

        Args:
            callback: 可选的回调函数，对每条记录进行处理
            limit: 可选的记录处理限制数量
        """
        logger.info("开始获取飞书多维表格数据...")

        page_count = 0
        total_count = 0
        processed_count = 0
        page_token = None

        while True:
            page_count += 1
            logger.info(f"正在获取第 {page_count} 页数据...")

            try:
                data = self.fetch_records(table_view_id, field_names, page_size=200, page_token=page_token)
                items = data.get("items", [])
                size = len(items)
                total_count += size
                page_token = data.get("page_token")
                logger.info(f"第 {page_count} 页获取到 {size} 条记录，next page_token: {page_token}")

                # 处理每条记录
                for item in items:
                    logger.info(f"正在处理第 {processed_count + 1} 条数据...")
                    # 检查是否达到处理限制
                    if limit and processed_count >= limit:
                        logger.info(f"已达到处理限制 {limit}，停止处理")
                        break

                    try:
                        parsed_record = self.parse_record(item)
                        processed_count += 1

                        # 如果提供了回调函数，则调用它
                        if callback:
                            callback(parsed_record)
                        else:
                            # 默认行为：打印记录信息
                            logger.info(f"任务ID: {parsed_record['task_id']}")

                    except Exception as e:
                        logger.error(f"处理记录失败: {e}, 记录: {item}")
                        continue

                # 如果达到处理限制，退出外层循环
                if limit and processed_count >= limit:
                    break

                # 检查是否还有更多数据
                if not data.get("has_more", False) or not page_token:
                    break

            except Exception as e:
                logger.error(f"获取第 {page_count} 页数据失败: {e}")
                break

        logger.info(f"总共获取到 {total_count} 条记录，成功处理 {processed_count} 条")
        logger.info("数据遍历完成")

    def fetch_all(self, table_view_id: str, field_names: list[str], limit: int | None = None) -> list[dict[str, str]]:
        """
        抓取视图中的所有记录

        Args:
            limit: 可选的记录处理限制数量
        """
        logger.info("开始获取飞书多维表格数据...")

        page_count = 0
        total_count = 0
        processed_count = 0
        page_token = None

        records: list[dict[str, str]] = []
        while True:
            page_count += 1
            logger.info(f"正在获取第 {page_count} 页数据...")

            try:
                data = self.fetch_records(table_view_id, field_names, page_size=200, page_token=page_token)
                items = data.get("items", [])
                size = len(items)
                total_count += size
                page_token = data.get("page_token")
                logger.info(f"第 {page_count} 页获取到 {size} 条记录，next page_token: {page_token}")

                # 处理每条记录
                for item in items:
                    logger.info(f"正在处理第 {processed_count + 1} 条数据...")
                    # 检查是否达到处理限制
                    if limit and processed_count >= limit:
                        logger.info(f"已达到处理限制 {limit}，停止处理")
                        break

                    try:
                        parsed_record = self.parse_record(item)
                        processed_count += 1

                        logger.info(f"任务ID: {parsed_record['task_id']}")
                        records.append(parsed_record)

                    except Exception as e:
                        logger.error(f"处理记录失败: {e}, 记录: {item}")
                        continue

                # 如果达到处理限制，退出外层循环
                if limit and processed_count >= limit:
                    break

                # 检查是否还有更多数据
                if not data.get("has_more", False) or not page_token:
                    break

            except Exception as e:
                logger.error(f"获取第 {page_count} 页数据失败: {e}")
                break

        logger.info(f"总共获取到 {total_count} 条记录，成功处理 {processed_count} 条")
        logger.info("数据遍历完成")
        return records
