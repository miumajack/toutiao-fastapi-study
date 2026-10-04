
from  fastapi import FastAPI
from routers import news
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
#添加跨域允许中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return {"msg": "我是新版本"}

app.include_router(news.router)
