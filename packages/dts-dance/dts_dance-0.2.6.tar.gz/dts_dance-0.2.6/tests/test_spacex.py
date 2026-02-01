import json
from dtsdance.bytecloud import ByteCloudClient
from dtsdance.spacex import GatewayInfo, SpaceXClient
from config import ConfigLoader

loader = ConfigLoader.get_instance()
loader.load_from_file(["eu-ttp"])
site_configs = loader.get_site_configs()
bytecloud_client = ByteCloudClient(site_configs)
spacex = SpaceXClient(bytecloud_client)


# pytest tests/test_spacex.py::test_list_mgr -s
def test_list_mgr():
    mgr_list = spacex.list_mgr("eu-ttp")
    print(f"mgr_list: {json.dumps(mgr_list, indent=2, ensure_ascii=False)}")


# pytest tests/test_spacex.py::test_register_gateway -s
def test_register_gateway():
    gateway_info = GatewayInfo(
        mgr_name="boe",
        ctrl_name="boe_halo_test",
        gateway_endpoint="volc.dts.gateway.service.boe:cluster:boe_halo_test:family:v6",
        auth_user="bytedts_backend",
        auth_password="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJieXRlZHRzX2JhY2tlbmQiLCJleHAiOjQ4OTEzMzQ0MDAsImRvbWFpbiI6IioifQ.D_87X-JCQn1CU9ru3PpeM1lmlOgVki6bVHo-kQ60eio",
        root_secret_key="97oscH5k",
        gw_meta_db="bytedts_sre_halo",
    )
    result = spacex.register_gateway("boe", gateway_info)
    print(f"result: {result}")
