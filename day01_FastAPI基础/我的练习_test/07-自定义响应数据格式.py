from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

class Book(BaseModel):
    id: int
    title: str
    content: str



@app.get('/book/{id}',response_model=Book)
def get_book(id:int):
    return {
        'id':id,
        'title':f'第{id}本书',
        'content':f'{id+100}',
        'ss':'ssss'  #定义响应模型一方面可以实现fastapi调用Pydantic对响应的类型检查，还可以实现过滤作用
        
        
    }
    
