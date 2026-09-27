from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

list1 = [a for a in range(1000)]

@app.get('/book')
async def get_skip(
    skip: int =Query(default=0,description='指跳过了多少页',le=20),
    limit: int =Query(default=10,description='最多返回多少页',le=20)
    ):
    return list1[skip*limit:skip*limit+limit]
    