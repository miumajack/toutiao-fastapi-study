from fastapi import FastAPI,Depends
from sqlalchemy import String,Float,Integer,DateTime,func,select
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession,async_sessionmaker
from sqlalchemy.orm import Mapped,mapped_column,DeclarativeBase
from datetime import datetime
from contextlib import asynccontextmanager
DATABASE_URL = "mysql+aiomysql://root:root1234@localhost:3306?fastapi_heima?charset=utf8"

#异步引擎
async_engine= create_async_engine(
    url= DATABASE_URL,
    pool_size =10,
    max_overflow = 20,
    echo = True
)

# 2. 定义模型类：基类 + 表对应的模型类
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="修改时间"
    )


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True, comment="书籍id")
    bookname: Mapped[str] = mapped_column(String(255), comment="书名")
    author: Mapped[str] = mapped_column(String(255), comment="作者")
    price: Mapped[float] = mapped_column(Float, comment="价格")
    publisher: Mapped[str] = mapped_column(String(255), comment="出版社")
    
##
async def create_table():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_table()
    yield
    await async_engine.dispose()
    

app = FastAPI(lifespan=lifespan)


async_session = async_sessionmaker(
    bind = async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        
@app.get('/hello')
async def get_book(db:AsyncSession=Depends(get_db)):
    book= await db.execute(select(Book))
    res = book.scalars().all()
    return res