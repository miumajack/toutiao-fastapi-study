from pydantic import BaseModel,ConfigDict

class UserRegister(BaseModel):
    username:str
    password:str
