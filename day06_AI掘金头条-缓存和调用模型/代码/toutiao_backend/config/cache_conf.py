import json
import time
from typing import Any

import redis.asyncio as redis
from redis.backoff import NoBackoff
from redis.retry import Retry

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0


# ============ 以下是原课程代码没有的部分,原因见下 ============
# 实测:Redis 没启动时,一次请求要等 49.5 秒才返回。
# 原因是两个叠加的问题:
#   1. 客户端没设超时,连不上就一直等;
#   2. redis-py 默认会自动重试,把等待时间成倍放大。
# 结论:Redis 本来是"可有可无"的缓存,却能把整个接口拖死,这就不叫可选了。
# 任何走网络的东西都一样——不设超时,就是把你的可用性交给对方。
FAILURE_COOLDOWN = 30  # 失败后多少秒内不再尝试(熔断)
_unavailable_until = 0.0


def _redis_ready() -> bool:
    return time.monotonic() >= _unavailable_until


def _mark_unavailable(exc: Exception) -> None:
    """失败一次就熔断一段时间,避免每个请求都去撞同一堵墙。"""
    global _unavailable_until
    _unavailable_until = time.monotonic() + FAILURE_COOLDOWN
    print(f"Redis 不可用,{FAILURE_COOLDOWN} 秒内跳过缓存:{exc}")


# 创建 Redis 的连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,  # Redis 服务器的主机地址
    port=REDIS_PORT,  # Redis 端口号
    db=REDIS_DB,  # Redis 数据库编号，0~15
    decode_responses=True,  # 是否将字节数据解码为字符串
    socket_connect_timeout=1.0,  # 建立连接最多等 1 秒
    socket_timeout=1.0,  # 读/写最多等 1 秒
    retry=Retry(NoBackoff(), 0),  # 不自动重试
    retry_on_error=[],
    retry_on_timeout=False,
)


# 设置 和 读取（字符串 和 列表或字典）"[{}]"
# 读取：字符串
async def get_cache(key: str):
    # return await redis_client.get(key)
    if not _redis_ready():
        return None
    try:
        return await redis_client.get(key)
    except Exception as e:
        _mark_unavailable(e)
        return None


# 读取：列表或字典
async def get_json_cache(key: str):
    if not _redis_ready():
        return None
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)  # 序列化
        return None
    except Exception as e:
        _mark_unavailable(e)
        return None


# 设置缓存 setex(key, expire, value)
async def set_cache(key: str, value: Any, expire: int = 3600):
    if not _redis_ready():
        return False
    try:
        if isinstance(value, (dict, list)):
            # 转字符串再存
            value = json.dumps(value, ensure_ascii=False)  # 中文正常保存
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        _mark_unavailable(e)
        return False
