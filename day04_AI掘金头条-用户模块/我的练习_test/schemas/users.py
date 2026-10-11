from pydantic import BaseModel,ConfigDict,Field
from typing import Optional

class UserRegister(BaseModel):
    username:str
    password:str


class User_Options_Info(BaseModel):
    nickname:Optional[str]=Field(None,max_length=(50),description='昵称')
    avatar:Optional[str]=Field(None,description='头像')
    gender:Optional[str]=Field(None,max_length=(50),description='性别')
    bio:Optional[str]=Field(None,description='博客')
    phone:Optional[str]=Field(None,max_length=(50),description='电话')
    
    model_config=ConfigDict(   #允许从orm中取值
                from_attributes=True  
            )

class UserInfo(User_Options_Info):
    id:int
    username:str
    
    model_config=ConfigDict(   #允许从orm中取值
            from_attributes=True  
        )
    
    
    
    
class User_AuthResponse(BaseModel):
    token:str=Field(...,alias='token',description='用户token')
    user_info:UserInfo=Field(...,alias='userInfo',description='用户信息')

    model_config=ConfigDict(   #允许从orm中取值
        from_attributes=True,
        populate_by_name=True
    )


