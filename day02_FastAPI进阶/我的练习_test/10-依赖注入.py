from fastapi import FastAPI, Depends, Query

app =  FastAPI()

#依赖注入共享函数
async def common(
    skip:int = Query(default=0,lt=10,description='跳过的页数'),
    limit:int = Query(default=10,lt=60,description='每页限制的页数')
    ):
    return {'skip':skip,'limit':limit}

@app.get('/user_list')
async def get_user(com = Depends(common)):
    return com

@app.get('/ques_list')
async def get_ques(com = Depends(common)):
    return com
