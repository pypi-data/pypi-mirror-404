import os
import yaml
from dtsdance.bytecloud import SiteConfig


class ConfigLoader:

    _instance: "ConfigLoader | None" = None

    def __init__(self):
        self._site_configs: dict[str, SiteConfig] = {}

    @classmethod
    def get_instance(cls) -> "ConfigLoader":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    def load_from_file(self, sites: list[str] | None = None) -> None:
        """从配置文件加载配置"""
        config_path = os.environ.get("CONFIG_PATH", "config.yaml")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                configs = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"加载配置失败: {e}")

        self._site_configs.update(
            {
                k: SiteConfig(k, v["endpoint"], v["svc_account"], v["svc_secret"], v.get("endpoint_bytedts_spacex", None))
                for k, v in configs["sites"].items()
                if sites is None or k in sites
            }
        )

    def get(self, site: str) -> SiteConfig:
        """获取指定站点的配置"""
        if not self._site_configs:
            raise RuntimeError("配置未加载，请先调用 load_from_file()")

        if site not in self._site_configs:
            raise KeyError(f"站点 {site} 不存在")

        return self._site_configs[site]

    def get_site_configs(self) -> dict[str, SiteConfig]:
        """获取所有配置"""
        return self._site_configs
