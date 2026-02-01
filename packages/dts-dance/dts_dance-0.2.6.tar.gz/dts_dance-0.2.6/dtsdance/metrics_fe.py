from loguru import logger
import requests
import threading
import time
from typing import NamedTuple, Optional
from datetime import datetime, timedelta


class MetricEnvInfo(NamedTuple):
    """Metric 环境配置"""

    name: str
    ak: str
    sk: str
    endpoint: str


class MetricType:
    def __init__(self, name: str, desc: str, metric_name: str, aggregator: str, rate: bool = False):
        self.name = name
        self.desc = desc
        self.metric_name = metric_name
        self.aggregator = aggregator
        self.rate = rate


class MetricTypeEnum(MetricType):
    DSYNCER_LATENCY = MetricType("dsyncer_latency", "DSyncer 延迟", "middleware.dsyncer.server.total.delay.latency.avg", "avg", False)
    DSYNCER_RT = MetricType("dsyncer_rt", "DSyncer RT", "middleware.dsyncer.server.total.time_consume.latency.pct99", "avg", False)
    DSYNCER_TPS = MetricType("dsyncer_tps", "DSyncer TPS", "middleware.dsyncer.server.success.row.count.total.rate", "sum", False)
    DSYNCER_MQ_BACKLOG = MetricType("dsyncer_mq_backlog", "DSyncer MQ 堆积", "rocketmq.consumer_group.depth", "sum", False)
    DSYNCER_MQ_CONSUME = MetricType("dsyncer_mq_consume", "DSyncer MQ 消费速率", "rocketmq.consumer_group.message.rate", "sum", True)
    DSYNCER_DFLOW_NODE_ERROR = MetricType("dsyncer_dflow_node_error", "DSyncer 对应的 DFlow 节点错误数", "dflow.error", "max", False)
    DFLOW_NODE_ERROR = MetricType("dflow_node_error", "DFlow 节点错误数", "dflow.error", "max", False)
    DFLOW_TPS = MetricType("dflow_tps", "DFlow TPS", "dflow.rows", "sum", True)


def get_metric_type_by_name(metric_name: str) -> Optional[MetricType]:
    """
    根据指标名称获取 MetricType 实例

    Args:
        metric_name: 指标名称

    Returns:
        Optional[MetricType]: MetricType 实例，如果不存在则返回 None
    """
    # 遍历 MetricTypeEnum 的所有属性
    for attr_name in dir(MetricTypeEnum):
        # 跳过私有属性和方法
        if attr_name.startswith("_"):
            continue

        attr_value = getattr(MetricTypeEnum, attr_name)

        # 检查是否是 MetricType 实例且名称匹配
        if isinstance(attr_value, MetricType) and attr_value.name == metric_name:
            return attr_value

    return None


class MetricsClient:
    """
    Metrics Client
    """

    # https://cloud.bytedance.net/docs/metrics/docs/63bbbb1ec6b537022a6000c7/63bbd4e8777a300220d4ac3a?x-resource-account=public&x-bc-region-id=bytedance
    # 2小时有效，过期前15分钟可刷新。所以，刷新间隔为15分钟
    _REFRESH_INTERVAL = 15 * 60

    def __init__(self, envs: dict[str, MetricEnvInfo]):
        """
        初始化 Metrics Client
        从配置文件加载所有环境的信息，并为每个环境初始化访问令牌
        """
        self.envs = envs

        # 初始化线程锁，用于保护 tokens 的并发访问
        self.token_lock = threading.Lock()

        # 初始化访问令牌缓存，按环境名称索引
        self.tokens: dict[str, str] = {}

        # 更新所有环境的配置信息
        self._refresh_tokens()

        # 启动 token 刷新线程
        self._start_refresh_thread()

    def _start_refresh_thread(self):
        """
        启动一个后台线程，定期刷新指定环境的访问令牌
        """
        refresh_thread = threading.Thread(
            target=self._refresh_token_periodically,
            daemon=True,
            name="metric-token-refresh",
        )
        refresh_thread.start()

    def _refresh_token_periodically(self):
        """
        定期刷新指定环境的访问令牌的线程函数
        """

        while True:
            # 等待指定时间
            time.sleep(self._REFRESH_INTERVAL)
            self._refresh_tokens()

    def _refresh_tokens(self):
        """
        刷新所有环境的访问令牌
        """
        logger.debug("开始刷新所有环境的访问令牌...")

        for _, env in self.envs.items():
            try:
                # 刷新令牌
                new_token = self._acquire_token(env.name, env.ak, env.sk, env.endpoint)
                # 使用线程锁更新缓存中的访问令牌
                with self.token_lock:
                    self.tokens[env.name] = new_token
                    logger.debug(f"环境 {env} 的访问令牌成功刷新，新令牌: {new_token}")

            except Exception as e:
                logger.error(f"环境 {env} 的访问令牌刷新失败: {e}")

        logger.debug(f"所有环境的访问令牌已成功刷新。tokens: {self.tokens}")

    def _acquire_token(self, env: str, ak: str, sk: str, endpoint: str) -> str:
        """
        获取访问令牌

        Args:
            env: 环境名称，如 'China-North', 'China-East' 等
            ak: 应用名称 (app_name)
            sk: 应用密钥 (app_secret)
            endpoint: API 端点

        Returns:
            str: 访问令牌
        """
        url = endpoint + "/api/access_token?force_new&_region=" + env

        # 准备请求体
        data = {"app_name": ak, "app_secret": sk}

        try:
            # 发送 POST 请求
            response = requests.post(url, json=data, timeout=30)

            # 检查响应状态码
            response.raise_for_status()

            # 解析响应
            response_json = response.json()
            # logger.debug(f"response_json: {response_json}")

            # 检查响应是否成功
            if response_json.get("code") != 0:
                error_msg = response_json.get("message", "未知错误")
                raise Exception(f"获取令牌失败: {error_msg}")

            # 提取令牌
            token = response_json.get("access_token")
            if not token:
                raise Exception("响应中没有找到 access_token")

            return token

        except Exception as e:
            logger.error(f"获取令牌时出错: {e}")
            raise

    def _get_token(self, env: str) -> str:
        """
        获取指定环境的访问令牌

        Args:
            env: 环境名称，如 'China-North', 'China-East' 等

        Returns:
            str: 当前有效的访问令牌

        Raises:
            KeyError: 如果指定的环境不存在
        """
        # 使用线程锁保护并发访问
        with self.token_lock:
            if env not in self.tokens:
                raise KeyError(f"环境 {env} 的访问令牌不存在")
            return self.tokens[env]

    def _get_endpoint(self, env_name: str) -> str:
        """
        获取指定环境的API端点

        Args:
            env: 环境名称，如 'China-North', 'China-East' 等

        Returns:
            str: API端点

        Raises:
            KeyError: 如果指定的环境不存在
        """
        if env_name not in self.envs:
            raise KeyError(f"未找到环境 {env_name} 的endpoint配置")

        return self.envs[env_name].endpoint

    def _build_query_payload(
        self, metric_name: str, aggregator: str, start_time_ms: int, end_time_ms: int, filters: list[dict], rate: bool, **kwargs
    ) -> dict:
        """
        构建查询请求体

        Args:
            metric_name: 指标名称
            aggregator: 聚合方式
            start_time_ms: 开始时间（毫秒）
            end_time_ms: 结束时间（毫秒）
            filters: 过滤条件列表
            **kwargs: 其他可选参数，如 topK, groupBy 等

        Returns:
            Dict: 请求体
        """
        query = {
            "metric": metric_name,
            "tenant": "default",
            "aggregator": aggregator,
            "rightAxis": 0,
            "rate": rate,
            "rateOptions": {"counter": True, "diff": False, "order": "before_downsample"},
            "isMultiField": False,
            "downsample": "30s-avg",
            "filters": filters,
        }

        # 添加可选参数
        if "topK" in kwargs:
            query["topK"] = kwargs["topK"]
        if "downsample" in kwargs:
            query["downsample"] = kwargs["downsample"]

        return {
            "allowCoprocessor": False,
            "start": start_time_ms,
            "end": end_time_ms,
            "queries": [query],
        }

    def _execute_metrics_query(
        self, env: str, metric_name: str, aggregator: str, start_time: str, end_time: str, filters: list[dict], rate: bool, **kwargs
    ) -> dict:
        """
        执行通用的指标查询

        Args:
            env: 环境名称
            metric_name: 指标名称
            aggregator: 聚合方式
            start_time: 开始时间
            end_time: 结束时间
            filters: 过滤条件列表
            rate: 是否使用速率计算
            **kwargs: 其他可选参数

        Returns:
            Dict: 包含指标的字典，包括metric和dps（数据点）

        Raises:
            Exception: 如果API请求失败
        """
        try:
            # 获取访问令牌和端点
            token = self._get_token(env)
            endpoint = self._get_endpoint(env)

            # 构建API请求URL
            url = f"{endpoint}/api/query?_region={env}"
            start_time_ms = int(datetime.fromisoformat(start_time).timestamp() * 1000)
            end_time_ms = int(datetime.fromisoformat(end_time).timestamp() * 1000)

            # 构建请求体
            payload = self._build_query_payload(metric_name, aggregator, start_time_ms, end_time_ms, filters, rate, **kwargs)
            # logger.debug(f"Executing metrics query, payload: {payload}")

            # 设置请求头
            headers = {"Content-Type": "text/plain", "Authorization": token}

            # 发送POST请求
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            # 解析响应
            result = response.json()

            # 检查响应是否为空
            if not result or len(result) == 0:
                return {"metric": metric_name, "dps": {}}

            # 提取指标数据
            metric_data = result[0]
            dps = metric_data.get("dps", {})

            # 移除最后一个统计不完全的数据点
            filtered_dps = self._remove_last_datapoint(end_time, dps)

            return {"metric": metric_data.get("metric"), "dps": filtered_dps}

        except Exception as e:
            logger.error(f"execute_metrics_query error: env={env}, metric={metric_name}, error={e}")
            raise Exception(f"获取指标失败: {e}")

    def get_mq_group_metrics(
        self, env: str, cluster: str, topic: str, group: str, start_time: str, end_time: str, metric_type: MetricType, **kwargs
    ) -> dict:
        """
        获取指定时间段的堆积指标

        Args:
            env: 环境名称，如 'China-North', 'China-East' 等
            cluster: RocketMQ 集群名称
            topic: RocketMQ 主题名称
            group: RocketMQ 消费组名称
            start_time: 开始时间
            end_time: 结束时间
            metric_name: 指标名称

        Returns:
            Dict: 包含堆积指标的字典，包括metric和dps（数据点）

        Raises:
            KeyError: 如果指定的环境不存在
            Exception: 如果API请求失败
        """
        logger.debug(
            f"get_mq_backlog_metrics env: {env}, cluster: {cluster}, topic: {topic}, group: {group}, start_time: {start_time}, end_time: {end_time}"
        )

        filters = [
            {"tagk": "cluster", "filter": cluster, "type": "literal_or", "groupBy": False},
            {"tagk": "consumer_group", "filter": group, "type": "literal_or", "groupBy": False},
            {"tagk": "topic", "filter": topic, "type": "literal_or", "groupBy": False},
        ]

        try:
            result = self._execute_metrics_query(
                env, metric_type.metric_name, metric_type.aggregator, start_time, end_time, filters, rate=False, kwargs=kwargs
            )
            # logger.debug(f"get_mq_backlog_metrics filtered_dps: {str(result['dps'])[:400]}...")
            # logger.debug(f"get_mq_backlog_metrics filtered_dps: {str(result['dps'])}")
            return result
        except Exception as e:
            logger.error(f"get_backlog_metrics env: {env}, cluster: {cluster}, topic: {topic}, group: {group}, error: {e}")
            raise Exception(f"获取堆积指标失败: {e}")

    def get_dsyncer_mq_group_1d_max_consume_tps(
        self,
        env: str,
        task_id: str,
        cluster: str,
        topic: str,
        group: str,
    ) -> int:
        """
        获取 DSyncer 任务最近几小时的 MQ 消费平均 TPS
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        # 转换为ISO格式字符串
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        logger.debug(f"查询时间范围: {start_time_str} 到 {end_time_str}")

        result = self.get_mq_group_metrics(
            env, cluster, topic, group, start_time_str, end_time_str, MetricTypeEnum.DSYNCER_MQ_CONSUME, downsample="1h-max"
        )
        data_points = result.get("dps", {})

        # 计算最大TPS
        max_consume_tps = 0.0
        if data_points:
            # 获取所有TPS值
            tps_values = [float(value) for value in data_points.values() if value is not None]
            if tps_values:
                max_consume_tps = max(tps_values)
                logger.debug(f"任务 {task_id}: 数据点数量={len(tps_values)}, TPS值={tps_values[:5]}..., 最大TPS={max_consume_tps:.2f}")
            else:
                logger.warning(f"任务 {task_id}: 没有有效的TPS数据点")
        else:
            logger.warning(f"任务 {task_id}: 没有获取到TPS数据")

        return int(max_consume_tps)

    def get_dsyncer_task_metrics(self, env: str, metric_type: MetricType, dsyncer_increment_task_id: str, start_time: str, end_time: str) -> dict:
        """
        获取 DSyncer 任务指定时间段的指标

        Args:
            env: 环境名称，如 'China-North', 'China-East' 等
            metric_type: 指标类型
            increment_task_id: 增量任务 ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Dict: 包含指标的字典，包括metric和dps（数据点）

        Raises:
            KeyError: 如果指定的环境不存在
            Exception: 如果API请求失败
        """
        # 校验 increment_task_id
        if not dsyncer_increment_task_id or not dsyncer_increment_task_id.strip():
            raise ValueError("dsyncer_increment_task_id 参数无效：不能为空")

        logger.debug(
            f"get_dsyncer_task_metrics env: {env}, metric_type: {metric_type}, dsyncer_increment_task_id: {dsyncer_increment_task_id}, start_time: {start_time}, end_time: {end_time}"
        )

        filters = [
            {"tagk": "task_id", "filter": dsyncer_increment_task_id, "type": "literal_or", "groupBy": True},
        ]

        try:
            return self._execute_metrics_query(env, metric_type.metric_name, metric_type.aggregator, start_time, end_time, filters, rate=False)
        except Exception as e:
            logger.error(f"get_task_latency_metrics env: {env}, dsyncer_increment_task_id: {dsyncer_increment_task_id}, error: {e}")
            raise Exception(f"获取指标失败: {e}")

    def get_dflow_task_metrics(self, env: str, dflow_task_id: str, metric_type: MetricType, start_time: str, end_time: str, **kwargs) -> dict:
        """
        获取指定时间段的 DFlow 指标

        Args:
            env: 环境名称，如 'China-North', 'China-East' 等
            dflow_task_id: DFlow 任务 ID
            metric_type: 指标类型
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            Dict: 包含指标的字典，包括metric和dps（数据点）

        Raises:
            KeyError: 如果指定的环境不存在
            Exception: 如果API请求失败
        """
        logger.debug(
            f"get_dflow_error_metrics env: {env}, dflow_task_id: {dflow_task_id}, metric_type: {metric_type}, start_time: {start_time}, end_time: {end_time}"
        )

        filters = [
            {"tagk": "task_id", "filter": dflow_task_id, "type": "literal_or", "groupBy": False},
        ]

        try:
            result = self._execute_metrics_query(
                env, metric_type.metric_name, metric_type.aggregator, start_time, end_time, filters, rate=metric_type.rate, kwargs=kwargs
            )
            logger.debug(f"get_dflow_task_metrics filtered_dps: {str(result['dps'])[:400]}...")
            return result
        except Exception as e:
            logger.error(f"get_dflow_task_metrics env: {env}, dflow_task_id: {dflow_task_id}, error: {e}")
            raise Exception(f"获取指标失败: {e}")

    @staticmethod
    def _remove_last_datapoint(end_time: str, dps: dict[str, float]) -> dict[str, float]:
        """
        移除监控数据中最后一个数据点，因为最后一个点往往不准确
        只有当最后一个点的时间戳与 end_time 相差在 15 秒内时才移除

        Args:
            end_time: 查询的结束时间
            dps: 数据点字典，键为时间戳字符串，值为指标值

        Returns:
            Dict[str, float]: 移除最后一个数据点后的字典
        """
        if not dps:
            return dps

        # 获取所有时间戳并排序
        timestamps = sorted(dps.keys())
        if not timestamps:
            return dps

        # 获取最后一个时间戳
        last_timestamp = timestamps[-1]

        # 将 end_time 转换为秒级时间戳
        try:
            end_time_sec = int(datetime.fromisoformat(end_time).timestamp())
            last_timestamp_sec = int(last_timestamp)

            # 计算时间差（秒）
            time_diff_sec = abs(end_time_sec - last_timestamp_sec)

            # 如果最后一个数据点的时间戳与 end_time 相差在 30 秒内，则移除
            if time_diff_sec <= 30:
                filtered_dps = {k: v for k, v in dps.items() if k != last_timestamp}
                logger.debug(f"移除最后一个数据点: 时间戳={last_timestamp}, 与end_time相差={time_diff_sec}s")
                return filtered_dps
            else:
                logger.debug(f"保留最后一个数据点: 时间戳={last_timestamp}, 与end_time相差={time_diff_sec}s > 30s")
                return dps

        except Exception as e:
            logger.warning(f"解析时间戳时出错，保留所有数据点: {e}")
            return dps
