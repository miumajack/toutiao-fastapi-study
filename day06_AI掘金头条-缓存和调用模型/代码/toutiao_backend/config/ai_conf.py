"""模型服务的配置。

这次改造的重点就在这个文件:密钥只能从环境变量读,绝不写进代码。

为什么不能写在前端?因为前端代码是**发给浏览器的**。
任何人按 F12 打开 Network 面板,或者直接看源码,就能拿到 key。
这不是"藏得不够深"的问题 —— 浏览器里的东西藏不住。
所以正确的位置只有一个:后端。前端调你的后端,后端再拿 key 去调模型服务。

配置写在项目根目录的 .env 文件里,格式见 .env.example。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 读取项目根目录下的 .env(不存在也不报错,只是读不到配置)。
# 这里用 __file__ 推绝对路径,而不是光写 load_dotenv() ——
# 后者是从"当前工作目录"往上找 .env,换个目录启动后端就读不到了。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_BASE_URL = os.getenv(
    "AI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
).rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "qwen-plus")
AI_TIMEOUT = float(os.getenv("AI_TIMEOUT", "30"))

AI_SYSTEM_PROMPT = os.getenv(
    "AI_SYSTEM_PROMPT",
    "你是一个新闻资讯网站的 AI 助手,回答简洁准确,使用中文,不要编造新闻事实。",
)
# 最多带多少轮历史给模型,防止上下文无限增长(既费钱又慢)
AI_MAX_HISTORY = int(os.getenv("AI_MAX_HISTORY", "10"))

# 本地假模型开关。
# 打开后不调用真实模型,直接返回一段写死的回复,用来:
#   - 前端联调时验证界面和链路(不用等模型、不花钱)
#   - 演示给别人看的时候不消耗额度
# 回复内容会明确标注"这是假回复",不会让人误以为是真 AI 输出。
AI_MOCK = os.getenv("AI_MOCK", "0").strip().lower() in ("1", "true", "yes", "on")


def is_configured() -> bool:
    """有没有配密钥。没配就明确告诉调用方,而不是发一个注定失败的请求出去。"""
    return bool(AI_API_KEY) or AI_MOCK
