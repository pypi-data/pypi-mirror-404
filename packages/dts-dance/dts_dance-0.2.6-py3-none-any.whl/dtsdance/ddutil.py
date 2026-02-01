from typing import Any, Optional
from loguru import logger
import requests
import json


def make_request(method: str, url: str, headers: dict[str, str], payload: Optional[dict] = None) -> dict[str, Any]:
    """
    发送 HTTP 请求的通用方法

    Args:
        method: HTTP 方法 (GET/POST)
        url: 请求 URL
        headers: 请求头
        payload: POST 请求的 JSON 数据

    Returns:
        dict[str, Any]: 解析后的 JSON 响应
    """
    response = None
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=payload, headers=headers)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")

        # 检查响应状态码
        # response.raise_for_status()

        # 解析 JSON 响应
        return response.json()

    except Exception as e:
        error_msg = f"make_request occur error, error: {e}"
        if response is not None:
            error_msg += f", response.text: {response.text}"
        logger.warning(error_msg)
        raise


def output_curl(url: str, headers: dict[str, str], payload: dict) -> str:
    """
    生成等效的 curl 命令字符串
    """
    curl_headers = " \\\n    ".join([f"-H '{k}: {v}'" for k, v in headers.items()])
    curl_payload = json.dumps(payload, ensure_ascii=False)
    curl_cmd = f"""curl -X POST '{url}' \\
    {curl_headers} \\
    -d '{curl_payload}'"""
    return curl_cmd
