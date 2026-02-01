import json
from dtsdance.dflow import DFlowClient
from dtsdance.bytecloud import ByteCloudClient
from config import ConfigLoader

loader = ConfigLoader.get_instance()
loader.load_from_file(["boe", "cn"])
site_configs = loader.get_site_configs()
bytecloud_client = ByteCloudClient(site_configs)
dflow_client = DFlowClient(bytecloud_client)


# pytest tests/test_dflow.py::test_get_task_info -s
def test_get_task_info():
    # info = dflow_client.get_task_info("cn", "106037095986690")
    info = dflow_client.get_task_info("cn", "10457709471247")
    print(f"DFlow Info: {info}")

# pytest tests/test_dflow.py::test_list_resources -s
def test_list_resources():
    resources = dflow_client.list_resources("cn", "cn_east", vregion = "China-East")
    print(f"list_resources: {json.dumps(resources, indent=2)}")

# pytest tests/test_dflow.py::test_get_all_ctrl_envs -s
def test_get_all_ctrl_envs():
    ctrl_envs = dflow_client.get_all_ctrl_envs("cn")
    print(f"get_all_ctrl_envs: {json.dumps(ctrl_envs, indent=2)}")
