"""AI 对话的请求/响应模型。

和前端的约定:
  - 请求只传 message 和 history,不传任何密钥;
  - 响应沿用项目统一的 {code, message, data} 结构。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """一条历史消息。role 限制成固定几种,防止前端传奇怪的东西给模型。"""

    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="这一轮用户说的话")
    history: list[ChatMessage] = Field(
        default_factory=list, description="之前的对话,最多取最近若干条"
    )


class ChatRecordResponse(BaseModel):
    id: int
    message: str
    response: str
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ChatListResponse(BaseModel):
    list: list[ChatRecordResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
