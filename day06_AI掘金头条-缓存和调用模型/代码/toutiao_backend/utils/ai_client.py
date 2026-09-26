"""调用大模型:整个项目里唯一一处"主动访问外部服务"的代码。

单独拆成一个文件,换来两件好处:
  1. 以后换模型厂商(阿里云百炼 → 别家),只改这里,业务代码一行不动;
  2. 能被测试替换掉(打桩),不用真的花钱调模型也能测通整条链路。

注意这里用的是 httpx 而不是 requests:接口是 async 的,
用同步的 requests 会把事件循环堵住,一个请求就能拖慢整个服务。
"""

import httpx

from config import ai_conf


class ModelError(Exception):
    """模型服务调不通、超时、或者返回了预期之外的东西。"""


def _mock_reply(messages: list[dict]) -> str:
    """假回复。内容里写明自己是假的,免得有人误以为模型已经接通了。"""
    question = messages[-1]["content"] if messages else ""
    return (
        "**这是本地假回复,不是真实 AI 生成的。**\n\n"
        f"你刚才问的是:{question}\n\n"
        "要接真实的模型,去阿里云百炼申请一个 Key,填进后端项目的 `.env`:\n\n"
        "```ini\n"
        "AI_API_KEY=sk-你自己的key\n"
        "AI_MOCK=0\n"
        "```\n\n"
        "然后重启后端即可。"
    )


async def chat_completion(messages: list[dict]) -> str:
    """把消息列表发给模型,拿回文本回复。"""
    # 本地假模型:不影响别的代码,只在最外层拦一下
    if ai_conf.AI_MOCK:
        return _mock_reply(messages)

    if not ai_conf.is_configured():
        raise ModelError("服务端还没有配置模型 API Key")

    payload = {
        "model": ai_conf.AI_MODEL,
        "messages": messages,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {ai_conf.AI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        # timeout 必填。没有超时的外部调用,等于把接口的命交到对方手里
        async with httpx.AsyncClient(timeout=ai_conf.AI_TIMEOUT) as client:
            response = await client.post(
                f"{ai_conf.AI_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException as exc:
        raise ModelError(f"模型服务响应超时({ai_conf.AI_TIMEOUT} 秒)") from exc
    except httpx.HTTPError as exc:
        raise ModelError(f"连接模型服务失败:{exc}") from exc

    if response.status_code != 200:
        # 把上游的错误原样带一部分出来,便于排查;但不要把 key 带出去
        raise ModelError(f"模型服务返回 {response.status_code}:{response.text[:200]}")

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelError(f"模型返回的结构不是预期格式:{str(data)[:200]}") from exc


def build_messages(message: str, history: list[dict]) -> list[dict]:
    """拼出发给模型的完整消息:系统提示 + 最近若干轮历史 + 本轮提问。

    为什么只带最近几条?因为上下文越长越贵、越慢,而且超出模型窗口还会报错。
    """
    recent = history[-ai_conf.AI_MAX_HISTORY:] if ai_conf.AI_MAX_HISTORY > 0 else []
    return [
        {"role": "system", "content": ai_conf.AI_SYSTEM_PROMPT},
        *recent,
        {"role": "user", "content": message},
    ]
