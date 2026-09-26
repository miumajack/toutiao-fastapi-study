"""AI 对话链路的自测:不花钱也能验证整条链路。

思路是把"调用模型"这一步替换掉(打桩),其余全部走真实代码 ——
真实的鉴权、真实的数据库读写、真实的响应结构。这样验证了链路,
却不用真的去调模型、不产生任何费用。

这本身就说明了一件事:把外部依赖单独放一个文件(utils/ai_client.py),
好处不只是"好换",还在于"好测"。

跑法(先 cd 到项目根目录):

    python tests/test_ai_chat.py

每个用例都接收一个 client 参数。下面的 main() 会一次性建好它并传进去;
装了 pytest 的话,文件末尾那个 fixture 会负责提供同名参数:

    python -m pytest tests -p no:cacheprovider

为什么要用 with TestClient(app) 包起来?这是踩过的坑:
不包的话,TestClient 每次请求都会新开一个事件循环,而数据库连接池里的连接
是上一个循环建立的 —— 表现就是"注册成功了,紧接着登录却报
AttributeError: 'NoneType' object has no attribute 'send'"。
用 with 包住,整段测试共用同一个循环,问题就消失了。
"""

import pathlib
import sys

# 直接运行本脚本时,Python 只会把 tests/ 加进搜索路径,
# 所以这里手动把项目根目录补上,让 main / utils 这些包能被 import。
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from main import app
from utils import ai_client

USERNAME = "codex_ai_demo"
PASSWORD = "123456"


def _token(client) -> str:
    """注册(已存在就登录)一个测试账号,返回它的 token。"""
    client.post("/api/user/register", json={"username": USERNAME, "password": PASSWORD})
    resp = client.post("/api/user/login", json={"username": USERNAME, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["token"]


def test_未登录不能调用(client):
    """不登录就调 AI,应该被挡住(模型按调用量收费,不能敞开)。"""
    resp = client.post("/api/ai/chat", json={"message": "你好"})
    assert resp.status_code in (401, 422), f"期望被拒绝,实际 {resp.status_code}: {resp.text}"


def test_没配密钥时返回503(client):
    """后端没配 AI_API_KEY 时,应该明确告诉我们"未配置",而不是发一个注定失败的请求。"""
    # 注意要同时把 AI_MOCK 关掉:否则会先走假模型分支,根本到不了这条逻辑。
    # 这就是"加了新分支之后,针对老分支的测试要一起更新"。
    original_configured = ai_client.ai_conf.is_configured
    original_mock = ai_client.ai_conf.AI_MOCK
    ai_client.ai_conf.is_configured = lambda: False
    ai_client.ai_conf.AI_MOCK = False
    try:
        resp = client.post(
            "/api/ai/chat",
            json={"message": "你好"},
            headers={"Authorization": _token(client)},
        )
    finally:
        ai_client.ai_conf.is_configured = original_configured
        ai_client.ai_conf.AI_MOCK = original_mock

    assert resp.status_code == 503, f"期望 503,实际 {resp.status_code}: {resp.text}"
    assert "API Key" in resp.json()["message"]


def test_对话成功并落库(client):
    """把模型调用打桩,验证:鉴权 -> 拼消息 -> 存库 -> 返回,整条链路通。"""
    seen = {}

    async def fake_chat_completion(messages):
        seen["messages"] = messages
        return "这是一条来自桩函数的测试回复"

    original = ai_client.chat_completion
    ai_client.chat_completion = fake_chat_completion
    try:
        resp = client.post(
            "/api/ai/chat",
            json={
                "message": "把这句话翻译成英文:你好",
                "history": [{"role": "user", "content": "在吗"},
                            {"role": "assistant", "content": "在的"}],
            },
            headers={"Authorization": _token(client)},
        )
    finally:
        ai_client.chat_completion = original

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["response"] == "这是一条来自桩函数的测试回复"
    assert data["id"] > 0
    assert "createdAt" in data

    # 检查真正发给模型的消息:第一条是系统提示,最后一条是本次提问
    messages = seen["messages"]
    assert messages[0]["role"] == "system", messages[0]
    assert messages[-1] == {"role": "user", "content": "把这句话翻译成英文:你好"}
    assert len(messages) == 4, f"应该是 系统+2条历史+本次,实际 {len(messages)} 条"


def test_历史接口能查到刚才那条(client):
    resp = client.get(
        "/api/ai/history",
        headers={"Authorization": _token(client)},
        params={"page": 1, "pageSize": 5},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["total"] >= 1
    assert any(item["response"] == "这是一条来自桩函数的测试回复" for item in data["list"])


def test_空消息被参数校验拦掉(client):
    resp = client.post(
        "/api/ai/chat",
        json={"message": ""},
        headers={"Authorization": _token(client)},
    )
    assert resp.status_code == 422, f"期望 422,实际 {resp.status_code}"


def test_假模型开关能返回假回复(client):
    """AI_MOCK=1 时应该直接返回假回复,并且明确标注自己是假的。"""
    original = ai_client.ai_conf.AI_MOCK
    ai_client.ai_conf.AI_MOCK = True
    try:
        resp = client.post(
            "/api/ai/chat",
            json={"message": "测试假模型"},
            headers={"Authorization": _token(client)},
        )
    finally:
        ai_client.ai_conf.AI_MOCK = original

    assert resp.status_code == 200, resp.text
    reply = resp.json()["data"]["response"]
    assert "假回复" in reply, reply
    assert "测试假模型" in reply, "假回复里应该回显用户的问题"


def main() -> int:
    # 按定义顺序执行(和 pytest 的行为一致)。
    # 别用 sorted() —— 那会打乱顺序,让"历史"用例跑在"对话落库"之前。
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = []
    # 整段测试共用一个 client(也就是共用一个事件循环)
    with TestClient(app) as client:
        for func in tests:
            name = func.__name__
            try:
                func(client)
            except AssertionError as exc:
                failed.append(name)
                print(f"[FAIL] {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failed.append(name)
                print(f"[ERROR] {name}: {type(exc).__name__}: {exc}")
            else:
                print(f"[PASS] {name}")

    print(f"\n{len(tests) - len(failed)}/{len(tests)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())


# 装了 pytest 时,用它提供上面那些用例需要的 client 参数
try:
    import pytest

    @pytest.fixture(scope="session")
    def client():
        with TestClient(app) as test_client:
            yield test_client

except ImportError:  # 没装 pytest 也能当普通脚本跑
    pass
