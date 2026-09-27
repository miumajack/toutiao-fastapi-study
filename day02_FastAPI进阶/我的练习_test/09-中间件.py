from fastapi import FastAPI


app = FastAPI()

@app.middleware('http')
async def middleware2(request, call_next):
    print('中间价2开始')
    response = await call_next(request)
    print('中间价2结束')
    return response


@app.middleware('http')
async def middleware1(request, call_next):
    print('中间价1开始')
    response = await call_next(request)
    print('中间价1结束')
    return response




@app.get('/')
async def hello():
    return {'message':'hello fastapi'}
