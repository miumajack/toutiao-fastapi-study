from pydantic import BaseModel,ConfigDict

class UserRegister(BaseModel):
    username:str
    password:str
    
    

class UserInfo():
    pass
    
class UserResponse():
    token:str
    user_info:UserInfo


