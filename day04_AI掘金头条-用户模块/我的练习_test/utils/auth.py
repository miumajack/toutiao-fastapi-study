from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users


# 整合 根据 Token 查询用户，返回用户
async def token_user(db:AsyncSession=Depends(get_db),
                     authorization:str=Header(alias='Authorization')
                     ):
    token=authorization.split(' ')[1]
    res =await users.check_user_by_token(db=db,token=token)
    
    return res
    
