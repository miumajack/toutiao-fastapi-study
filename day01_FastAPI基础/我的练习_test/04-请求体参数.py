from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

class User(BaseModel):
    name:str = Field(description='用户名',max_length=10,min_length=3)
    password:str = Field(description='密码',min_length=8,max_length=20)
    
@app.post('/res')
def book_register(user: User):
    return f'{user.name}注册成功'

