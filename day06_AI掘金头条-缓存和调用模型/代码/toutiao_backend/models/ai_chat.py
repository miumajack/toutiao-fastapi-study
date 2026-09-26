"""AI 聊天记录表。

字段和数据库里已经建好的 ai_chat 表一一对应(见课程物料 database.sql)。
注意这张表没有 updated_at,所以这里不能套用 models/news.py 里那个自带
created_at/updated_at 的 Base。
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 注意:外键这里必须引用 User.id 这个列对象,不能写成字符串 "user.id"。
# 因为本项目每个模型文件都各自定义了一个 Base,也就是各自一套注册表,
# 字符串"user.id"在自己那套表里找不到 user 表,写库时会报:
#   NoReferencedTableError: ... could not find table 'user'
# 导入模型类则直接把列对象带过来了,不存在"找不到"的问题。
from models.users import User


class Base(DeclarativeBase):
    pass


class AiChat(Base):
    __tablename__ = "ai_chat"

    __table_args__ = (
        Index("fk_ai_chat_user_idx", "user_id"),
        Index("idx_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="聊天记录ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(User.id), nullable=False, comment="用户ID"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="用户消息")
    response: Mapped[str] = mapped_column(Text, nullable=False, comment="AI回复")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )

    def __repr__(self):
        return f"<AiChat(id={self.id}, user_id={self.user_id})>"
