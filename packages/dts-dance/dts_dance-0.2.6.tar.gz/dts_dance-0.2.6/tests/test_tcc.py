import json
from dtsdance.bytecloud import ByteCloudClient
from dtsdance.tcc_open import TCCClient
from dtsdance.tcc_inner import TCCInnerClient
from config import ConfigLoader

loader = ConfigLoader.get_instance()
loader.load_from_file(["boe", "us-ttp"])
# loader.load_from_file(["eu-ttp"])
site_configs = loader.get_site_configs()


# pytest tests/test_tcc.py::test_get_config -s
def test_get_config():
    site_info = site_configs["boe"]
    client_open = TCCClient(site_info.svc_account, site_info.svc_secret, endpoint=site_info.endpoint)
    config_ctrl_env = client_open.get_config(ns_name="bytedts.mgr.api", region="China-BOE", dir="/default", conf_name="ctrl_env")
    print(f"ctrl_env: {config_ctrl_env}")


# pytest tests/test_tcc.py::test_list_configs -s
def test_list_configs():
    bytecloud_client = ByteCloudClient(site_configs)
    client_inner = TCCInnerClient(bytecloud_client)
    # configs = client_inner.list_configs(site="boe", ns_name="bytedts.mgr.api", region="China-BOE", dir="/default", conf_name="route")
    configs = client_inner.list_configs(site="us-ttp", ns_name="bytedts.mgr.api", region="US-TTP", dir="/default", conf_name="route")
    # configs = client_inner.list_configs(site="eu-ttp", ns_name="bytedts.mgr.api", region="EU-TTP", dir="/default", conf_name="route")
    conf_names = [conf.get("conf_name", "") for conf in configs]
    print(f"conf_names: {json.dumps(conf_names, ensure_ascii=False, indent=2)}")
