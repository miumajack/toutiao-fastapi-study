"""AI 聊天记录的数据访问层。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ai_chat import AiChat


async def create_chat(db: AsyncSession, user_id: int, message: str, response: str) -> AiChat:
    chat = AiChat(user_id=user_id, message=message, response=response)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def get_chat_list(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
):
    """返回 (记录列表, 总数)。和收藏/历史那两个列表接口保持一致的返回形状。"""
    count_result = await db.execute(
        select(func.count()).select_from(AiChat).where(AiChat.user_id == user_id)
    )
    total = count_result.scalar_one()

    query = (
        select(AiChat)
        .where(AiChat.user_id == user_id)
        .order_by(AiChat.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    return result.scalars().all(), total
