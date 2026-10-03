from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from datetime import datetime
from sqlalchemy import DateTime,String,Integer,Float,func,select
from contextlib import asynccontextmanager
from fastapi import FastAPI,Depends
"""
创建异步引擎
定义模型类    
创建表
上下文管理
创建会话
定义会话依赖
定义路由函数并注入依赖进行crud
"""
##创建异步引擎

DATABASE_URL = "mysql+aiomysql://root:root1234@localhost:3306/fastapi_heima?charset=utf8"


async_engine = create_async_engine(
    url = DATABASE_URL,  #数据库的地址
    pool_size =10,         #连接数量
    max_overflow = 20,      #最大连接数
    echo =True              #mysql的回显
)

##定义模型类  

class Base(DeclarativeBase):  #模型类的基类要继承DeclarativeBase类
    
    create_time: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),comment='创建时间')
    update_time: Mapped[datetime] = mapped_column(DateTime,server_default=func.now(),onupdate=func.now(),comment='更新时间')

class Book(Base):
    
    __tablename__='my_book'  #建立表的名字
    id : Mapped[int] = mapped_column(Integer,primary_key=True,nullable=False,comment='书籍id')
    book_name : Mapped[str] = mapped_column(String(255),nullable=False,comment='书籍名字')
    author : Mapped[str] = mapped_column(String(255),nullable=False,comment='书籍作者')
    price : Mapped[float] = mapped_column(Float,nullable=False,comment='书籍价格')
    publish : Mapped[str] = mapped_column(String(255),nullable=False,comment='书籍出版社')


##创建表

async def create_table():
    async with async_engine.begin() as conn:  #取一个数据库的连接并在连接上开启一个事务
        await conn.run_sync(Base.metadata.create_all)  #将所有继承自Base的元数据转换为SQL语句
        

##上下文管理
@asynccontextmanager
async def lifespan(app:FastAPI):  #当运行fastapi服务时，执行如下操作
    await create_table()   #直接建表
    yield                   #暂停等待其他过程的执行
    await async_engine.dispose()  #其他过程完成，关闭引擎连接
        


app = FastAPI(lifespan=lifespan) #fastapi服务的实例化


##创建会话

async_session = async_sessionmaker(   #创建会话工厂用于产生会话
    bind=async_engine,   #绑定的引擎
    class_=AsyncSession,  #类型
    expire_on_commit=False  #会话产生时，不过期
)

##定义会话依赖

async def get_db():  #创建会话依赖函数用于后续注入fastapi
    async with async_session() as session:  #产生会话并用with管理上下文，会话结束后，关闭连接
        try:   
            yield session   #产生会话等待路由函数执行完成
            await session.commit()  #正常情况下提交
        except Exception:
            await session.rollback()  #出现Exception则所有事务进行回滚
            raise
        
##定义路由函数并注入依赖进行crud

@app.get('/book/book_list')
async def get_book_info(db:AsyncSession = Depends(get_db)):   #注入依赖
    book=await db.execute(select(Book))  #异步查询数据库中的所有数据
    books = book.scalars().all()        #获取查询结果并转换为python类型
    return books    #返回查询结果


