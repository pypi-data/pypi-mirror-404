from datetime import datetime, timedelta
import threading
import json
from loguru import logger
from typing import Any
from requests_toolbelt import MultipartEncoder

import requests

URL_FEISHU_OPEN_API: str = "https://fsopen.bytedance.net/open-apis"


class FeishuBase:
    """飞书基础类，传入机器人认证信息，支持自动token续期管理"""

    def __init__(self, bot_app_id: str, bot_app_secret: str):
        """
        初始化飞书基础类
        """
        self.tenant_access_token: str | None = None
        self.token_expire_time: datetime | None = None
        self._token_lock = threading.Lock()

        self.bot_app_id = bot_app_id
        self.bot_app_secret = bot_app_secret

    def _get_tenant_access_token(self) -> str:
        """
        获取tenant_access_token

        Returns:
            tenant_access_token字符串

        Raises:
            Exception: 获取token失败时抛出异常
        """
        url = f"{URL_FEISHU_OPEN_API}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.bot_app_id, "app_secret": self.bot_app_secret}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"获取tenant_access_token失败: {result.get('msg')}")

            token = result.get("tenant_access_token")
            expire_in = result.get("expire", 7200)  # 默认2小时过期

            # 设置过期时间，提前5分钟刷新
            self.token_expire_time = datetime.now() + timedelta(seconds=expire_in - 300)

            logger.info(f"成功获取tenant_access_token，过期时间: {self.token_expire_time}")
            return token

        except requests.RequestException as e:
            logger.warning(f"请求tenant_access_token失败: {e}")
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            logger.warning(f"获取tenant_access_token失败: {e}")
            raise

    def get_access_token(self) -> str:
        """
        获取有效的access token，自动处理续期

        Returns:
            有效的tenant_access_token
        """
        with self._token_lock:
            # 检查token是否存在或已过期
            if self.tenant_access_token is None or self.token_expire_time is None or datetime.now() >= self.token_expire_time:

                logger.info("Token不存在或已过期，重新获取")
                self.tenant_access_token = self._get_tenant_access_token()

            return self.tenant_access_token

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发起API请求的通用方法

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            Response对象
        """
        url = f"{URL_FEISHU_OPEN_API}{endpoint}"

        # 获取有效token
        token = self.get_access_token()
        # logger.debug(f"使用token: {token} 发送请求: {method} {url}")

        # 设置认证头
        headers = kwargs.get("headers", {"Content-Type": "application/json"})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        response: requests.Response | None = None
        try:
            response = requests.request(method, url, **kwargs)
            # logger.debug(f"response_json: {response.json()}")
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            error_detail = response.json() if response is not None else "无响应"
            logger.warning(f"API请求失败: {method} {url}, error: {e}, response_json: {error_detail}")
            raise

    def upload_image(self, image_path: str) -> str | None:
        """
        上传图片到飞书

        Args:
            image_path: 图片文件路径
            image_type: 图片类型，默认为'message'

        Returns:
            image_key

        """
        if not image_path:
            raise ValueError("必须提供image_path")

        file_obj = None
        try:
            # 准备文件
            file_obj = open(image_path, "rb")
            file_name = image_path.split("/")[-1]

            # 构建表单数据
            form = {"image_type": "message", "image": (file_name, file_obj, "image/png")}
            multi_form = MultipartEncoder(form)
            headers = {"Content-Type": multi_form.content_type}
            response = self.make_request("POST", "/im/v1/images", headers=headers, data=multi_form)
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"上传图片失败: {result.get('msg')}")

            logger.info(f"图片上传成功，image_key: {result.get('data', {}).get('image_key')}")
            logger.debug(f"上传响应logid: {response.headers.get('X-Tt-Logid')}")

            return result.get("data", {}).get("image_key")

        except Exception as e:
            logger.warning(f"上传图片失败: {e}")
            return None
        finally:
            # 如果是通过路径打开的文件，需要关闭
            if image_path and file_obj and hasattr(file_obj, "close"):
                file_obj.close()

    def send_text_message(self, receive_id: str, text: str, receive_id_type: str) -> dict[str, Any]:
        """
        发送文本消息

        Args:
            receive_id: 接收者ID（群聊ID、用户ID等）
            text: 消息文本内容
            receive_id_type: 接收者ID类型，可选值：open_id, user_id, union_id, email, chat_id

        Returns:
            发送结果
        """
        content = json.dumps({"text": text}, ensure_ascii=False)
        return self.send_message(receive_id, "text", content, receive_id_type)

    def send_image_message(self, receive_id: str, image_key: str, receive_id_type: str) -> dict[str, Any]:
        """
        发送图片消息

        Args:
            receive_id: 接收者ID
            image_key: 图片key（通过upload_image获取）
            receive_id_type: 接收者ID类型

        Returns:
            发送结果
        """
        content = json.dumps({"image_key": image_key}, ensure_ascii=False)
        return self.send_message(receive_id, "image", content, receive_id_type)

    def send_card_message(self, receive_id: str, header: dict, elements: list, receive_id_type: str) -> dict[str, Any]:
        """
        发送卡片消息

        Args:
            receive_id: 接收者ID
            header: 卡片消息的头部内容（符合飞书卡片规范的JSON）
            elements: 卡片消息的主体元素列表
            receive_id_type: 接收者ID类型

        Returns:
            发送结果
        """
        card_content = {"schema": "2.0", "config": {"update_multi": True}, "body": {"direction": "vertical", "elements": elements}, "header": header}
        content = json.dumps(card_content, ensure_ascii=False)
        return self.send_message(receive_id, "interactive", content, receive_id_type)

    def send_message(self, receive_id: str, msg_type: str, content: str, receive_id_type: str = "chat_id") -> dict[str, Any]:
        """
        发送消息的通用方法

        Args:
            receive_id: 接收者ID
            msg_type: 消息类型（text, image, card等）
            content: 消息内容
            receive_id_type: 接收者ID类型

        Returns:
            发送结果

        Raises:
            Exception: 发送失败
        """
        payload = {"receive_id": receive_id, "msg_type": msg_type, "content": content}
        params = {"receive_id_type": receive_id_type}

        try:
            response = self.make_request("POST", "/im/v1/messages", json=payload, params=params)
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"请求失败: {result.get('msg')}")

            logger.info(f"消息发送成功，message_id: {result.get('data', {}).get('message_id')}")
            logger.debug(f"发送响应logid: {response.headers.get('X-Tt-Logid')}")

            return result.get("data", {})

        except Exception as e:
            logger.warning(f"发送消息失败: {e}")
            raise

    def reply_message(self, message_id: str, msg_type: str, content: str) -> dict[str, Any]:
        """
        回复某条消息

        Args:
            message_id: 消息ID
            msg_type: 消息类型（text, image, card等）
            content: 消息内容

        Returns:
            回复结果

        Raises:
            Exception: 回复失败
        """
        payload = {"reply_in_thread": False, "msg_type": msg_type, "content": content}

        try:
            response = self.make_request("POST", f"/im/v1/messages/{message_id}/reply", json=payload)
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"请求失败: {result.get('msg')}")

            logger.info(f"消息回复成功，message_id: {result.get('data', {}).get('message_id')}")
            logger.debug(f"发送响应logid: {response.headers.get('X-Tt-Logid')}")

            return result.get("data", {})

        except Exception as e:
            logger.warning(f"回复消息失败: {e}")
            raise

    def batch_get_user_ids(self, emails: list[str]) -> dict[str, None | str]:
        """
        批量获取用户ID

        Args:
            emails: 用户邮箱列表

        Returns:
            批量获取结果（email -> user_id 的字典映射）

        Raises:
            Exception: 获取失败
        """
        payload = {"emails": emails, "include_resigned": False}

        try:
            response = self.make_request("POST", "/contact/v3/users/batch_get_id?user_id_type=user_id", json=payload)
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"请求失败: {result.get('msg')}")

            user_dict = {user.get("email"): user.get("user_id", None) for user in result.get("data", {}).get("user_list", []) if user.get("email")}

            logger.debug(f"发送响应logid: {response.headers.get('X-Tt-Logid')}")

            return user_dict
        except Exception as e:
            logger.warning(f"批量获取用户ID失败: {e}")
            raise

    def batch_get_all_user_ids(self, emails: list[str]) -> dict[str, None | str]:
        """
        批量获取所有用户ID，自动分批处理（每批最多50个）

        Args:
            emails: 用户邮箱列表

        Returns:
            所有用户ID字典（email -> user_id 的映射）

        Raises:
            Exception: 获取失败
        """
        if not emails:
            return {}

        all_user_dict = {}
        batch_size = 50

        # 分批处理
        for i in range(0, len(emails), batch_size):
            batch_emails = emails[i : i + batch_size]
            logger.info(f"正在获取第 {i // batch_size + 1} 批用户ID，数量: {len(batch_emails)}")

            try:
                batch_user_dict = self.batch_get_user_ids(batch_emails)
                all_user_dict.update(batch_user_dict)
            except Exception as e:
                logger.error(f"获取第 {i // batch_size + 1} 批用户ID失败: {e}")
                # 继续处理下一批，不中断整个流程
                continue

        logger.info(f"共获取到 {len(all_user_dict)} 个用户ID")
        return all_user_dict
