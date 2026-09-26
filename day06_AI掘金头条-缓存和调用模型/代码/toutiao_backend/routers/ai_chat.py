"""AI 对话接口。

分层和新闻/用户模块完全一样,路由层只做三件事:
  1. 校验请求(交给 Pydantic);
  2. 调用其它层(ai_client 调模型、crud 存库);
  3. 把异常翻译成合适的 HTTP 状态码。

这里没有一行"怎么调模型"的细节,也没有一行 SQL。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import ai_chat
from models.users import User
from schemas.ai_chat import ChatListResponse, ChatRecordResponse, ChatRequest
from utils import ai_client
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat")
async def chat(
    data: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发一句话给 AI,返回它的回复,并把这一轮对话存进 ai_chat 表。

    为什么要登录?两个理由:
      - 模型是按调用量收费的,不登录等于把钱包敞开;
      - ai_chat 表要求 user_id,不知道是谁就没法存。
    """
    messages = ai_client.build_messages(
        data.message, [m.model_dump() for m in data.history]
    )

    try:
        reply = await ai_client.chat_completion(messages)
    except ai_client.ModelError as exc:
        # 是模型服务的锅,不是调用方的错 -> 503,让前端提示"稍后再试"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    record = await ai_chat.create_chat(db, user.id, data.message, reply)
    return success_response("对话成功", ChatRecordResponse.model_validate(record))


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = Query(10, alias="pageSize", le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records, total = await ai_chat.get_chat_list(db, user.id, page, page_size)
    payload = ChatListResponse(
        list=[ChatRecordResponse.model_validate(item) for item in records],
        total=total,
        has_more=(page - 1) * page_size + len(records) < total,
    )
    return success_response("获取对话记录成功", payload)
