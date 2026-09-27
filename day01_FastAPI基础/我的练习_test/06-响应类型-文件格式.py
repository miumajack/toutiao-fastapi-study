from fastapi import FastAPI
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/file1')
def get_jpg():
    
    # path = "../代码/files/1.jpeg"写法1相对路径
    path=Path(__file__).parent.parent/'代码'/'files'/"1.jpeg" #推荐写法
    
    return FileResponse(path)


