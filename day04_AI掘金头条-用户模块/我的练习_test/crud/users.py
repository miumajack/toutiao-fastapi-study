from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select,update
from models.users import User,UserToken
from utils import security
from schemas import users
from uuid import uuid4
from datetime import datetime,timedelta
from fastapi import HTTPException,status

#检查用户是否存在
async def check_by_username(username: str,db:AsyncSession)->User|None:
    user = await db.execute(select(User).where(User.username==username))
    return user.scalar_one_or_none()
    
    

async def create_user(user_pydantic:users.UserRegister,db:AsyncSession):
    #加密密码
    password = security.get_hash_password(user_pydantic.password)
    new_user = User(username=user_pydantic.username,password=password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    print(f'========create_user=========={new_user.id}======')
    
    return new_user
    



#创建token
async def create_token(user_id:int,db:AsyncSession)->UserToken:
    new_token =str(uuid4())
    expires_at =datetime.now()+timedelta(days=7)
    user_token=UserToken(user_id=user_id,token=new_token,expires_at=expires_at)
    db.add(user_token)
    await db.commit()
    await db.refresh(user_token)
    return user_token



#用户密码验证用户    
async def verify_user(username,password,db:AsyncSession):
    #验证用户名
    user=await check_by_username(username=username,db=db)
    if not user:
        return None
    #用户找到后验证密码
    res=security.verify_password(plain_password=password,hashed_password=user.password)
    if not res:
        return None
    return user
    

##
async def check_user_by_token(db:AsyncSession,token):
    res = await db.execute(select(UserToken).where(UserToken.token==token))
    res=res.scalar_one_or_none()
    if not res or res.expires_at<datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='token过期')
    user=await db.execute(select(User).where(User.id==res.user_id))
    return user.scalar_one_or_none()
        