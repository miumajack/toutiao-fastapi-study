import traceback

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status

# 开发模式：返回详细错误信息
# 生产模式：返回简化错误信息
DEBUG_MODE = True  # 教学项目保持开启

# 唯一索引名 -> 说人话的提示。
# 原来的写法是 if "username_UNIQUE" in msg or "Duplicate entry" in msg,
# 而"Duplicate entry"对任何唯一键冲突都成立,所以收藏重复也会提示"用户名已存在"。
# MySQL 的报错里带索引名,按索引名映射才准确:
#   (1062, "Duplicate entry '1-2' for key 'favorite.user_news_unique'")
UNIQUE_INDEX_MESSAGES = {
    "username_unique": "用户名已存在",
    "phone_unique": "该手机号已被注册",
    "token_unique": "令牌冲突,请重试",
    "user_news_unique": "这条新闻已经收藏过了",
    "name_unique": "该分类名称已存在",
    "news_related_unique": "这条相关新闻已经存在",
}


def describe_integrity_error(error_msg: str) -> str:
    """把数据库的约束错误翻译成用户能看懂的提示。"""
    lowered = error_msg.lower()

    if "duplicate entry" in lowered or "1062" in error_msg:
        for index_name, message in UNIQUE_INDEX_MESSAGES.items():
            if index_name in lowered:
                return message
        return "数据已存在,请勿重复提交"  # 兜底:不知道是哪个唯一键

    if "foreign key" in lowered or "1452" in error_msg:
        return "关联数据不存在"
    if "cannot be null" in lowered or "1048" in error_msg:
        return "必填字段不能为空"
    return "数据约束冲突,请检查输入"


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理 HTTPException 异常
    """
    # HTTPException 通常是业务逻辑主动抛出的，data 保持 None
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    处理数据库完整性约束错误
    """
    error_msg = str(exc.orig)
    detail = describe_integrity_error(error_msg)

    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": "IntegrityError",
            "error_detail": error_msg,
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": 400,
            "message": detail,
            "data": error_data
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """
    处理 SQLAlchemy 数据库错误
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败，请稍后重试",
            "data": error_data
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),
            "path": str(request.url)
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": error_data
        }
    )


