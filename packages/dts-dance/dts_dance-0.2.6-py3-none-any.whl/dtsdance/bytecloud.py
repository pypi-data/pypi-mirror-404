import requests
import threading
import time
from typing import Dict
from loguru import logger
from typing import NamedTuple


class SiteConfig(NamedTuple):
    name: str
    endpoint: str
    svc_account: str
    svc_secret: str
    endpoint_bytedts_spacex: str | None = None


class ByteCloudClient:
    """
    ByteCloud Client
    """

    # 每小时刷新一次，单位为秒
    _REFRESH_INTERVAL = 2 * 60 * 60

    def __init__(self, sites: dict[str, SiteConfig] | None = None, enable_jwt_cache: bool = False) -> None:
        """
        初始化 ByteCloud Client
        从配置文件加载所有环境的信息，并为每个环境初始化 JWT 令牌
        sites 中保存内容 list[(name, endpoint, svc_account, svc_secret)]
        """
        self.enable_jwt_cache = enable_jwt_cache
        self.sites = sites if sites is not None else {}

        # 初始化线程锁，用于保护 jwt_tokens 的并发访问
        self.token_lock = threading.Lock()

        # 初始化 JWT 令牌缓存，按环境名称索引
        self.jwt_tokens: Dict[str, str] = {}

        if enable_jwt_cache:
            logger.info("启用 JWT 令牌缓存")

            # 更新所有环境的 JWT 令牌
            self._refresh_tokens()

            # 启动 JWT 令牌刷新线程
            self._start_refresh_thread()

    def _start_refresh_thread(self):
        """
        启动一个后台线程，定期刷新所有环境的 JWT 令牌
        """
        refresh_thread = threading.Thread(
            target=self._refresh_token_periodically,
            daemon=True,
            name="jwt-token-refresh",
        )
        refresh_thread.start()

    def _refresh_token_periodically(self):
        """
        定期刷新所有环境的 JWT 令牌的线程函数
        """
        while True:
            # 等待指定时间
            time.sleep(self._REFRESH_INTERVAL)
            self._refresh_tokens()

    def _refresh_tokens(self):
        """
        刷新所有环境的 JWT 令牌
        """
        logger.debug("开始刷新所有环境的 JWT 令牌...")

        for _, site in self.sites.items():
            try:
                # 刷新令牌
                new_token = self._acquire_jwt_token(site.endpoint, site.svc_secret)
                # 使用线程锁更新缓存中的 JWT 令牌
                with self.token_lock:
                    self.jwt_tokens[site.name] = new_token
                    logger.debug(f"环境 {site.name} 的 JWT 令牌成功刷新，新令牌: {new_token}")
            except Exception as e:
                logger.error(f"环境 {site.name} 的 JWT 令牌刷新失败: {e}")

        logger.debug(f"所有环境的 JWT 令牌已成功刷新。jwt_tokens: {self.jwt_tokens}")

    def _acquire_jwt_token(self, endpoint: str, svc_secret: str) -> str:
        """
        获取 JWT 令牌

        Args:
            token: 认证令牌
            endpoint: API 端点

        Returns:
            str: JWT 令牌
        """
        url = endpoint + "/auth/api/v1/jwt"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + svc_secret,
        }

        try:
            # 发送 GET 请求
            response = requests.get(url, headers=headers, timeout=60)

            # 调试用途，输出返回内容，保存内容到本地文件
            # logger.debug(f"获取JWT令牌响应: response.text={response.text}")
            # with open("jwt_response.html", "w", encoding="utf-8") as f:
            #     f.write(response.text)

            # 检查响应状态码
            if response.status_code != 200:
                raise Exception(f"获取JWT令牌失败。status_code: {response.status_code}, response.text: {response.text}")

            # 解析响应体
            response_json = response.json()
            if response_json.get("code", -1) != 0:
                raise Exception(f"获取JWT令牌失败: {response.text}")

            # 从响应头中获取 JWT 令牌
            jwt_token = response.headers.get("X-Jwt-Token")
            if not jwt_token:
                raise Exception("响应头中没有 X-Jwt-Token")

            return jwt_token

        except Exception as e:
            logger.error(f"获取JWT令牌时出错: {e}")
            raise

    def get_jwt_token(self, site: str) -> str:
        """
        获取指定站点的 JWT 令牌
        """
        if self.enable_jwt_cache:
            # 使用线程锁保护并发访问
            with self.token_lock:
                if site not in self.jwt_tokens:
                    raise KeyError(f"站点 {site} 的 JWT 令牌不存在")
                return self.jwt_tokens[site]
        else:
            site_config = self.get_site_config(site)
            return self._acquire_jwt_token(site_config.endpoint, site_config.svc_secret)

    def build_request_headers(self, site: str, vregion: str | None = None) -> dict[str, str]:
        """
        构建请求头

        Args:
            site: 站点名称
            vregion: 默认为 None
        Returns:
            dict[str, str]: 请求头字典
        """
        jwt_token = self.get_jwt_token(site)
        headers = {"Content-Type": "application/json", "x-jwt-token": jwt_token}
        if vregion:
            headers["x-bcgw-vregion"] = vregion
            headers["get-svc"] = "1"  # response header 中显示实际请求的机房

        return headers

    def get_site_config(self, site: str) -> SiteConfig:
        """
        获取指定环境的信息

        Args:
            site: 站点名称

        Returns:
            SiteConfig: 指定站点的信息

        Raises:
            KeyError: 如果指定的站点不存在
        """
        if site not in self.sites:
            raise KeyError(f"站点 {site} 不存在")

        return self.sites[site]
