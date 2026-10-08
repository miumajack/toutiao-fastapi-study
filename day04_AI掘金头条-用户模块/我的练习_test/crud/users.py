from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select,update
from models.users import User,UserToken
from utils import security
from schemas import users
from uuid import uuid4
from datetime import datetime

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
    expires_at =datetime.now()
    user_token=UserToken(user_id=user_id,token=new_token,expires_at=expires_at)
    db.add(user_token)
    await db.commit()
    await db.refresh(user_token)
    return user_token
    
    