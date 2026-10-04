from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


## 创建异步引擎

DATABASE_URL = "mysql+aiomysql://root:root1234@localhost:3306/news_app?charset=utf8"

async_engine = create_async_engine(
    url=DATABASE_URL,       # 数据库连接地址
    pool_size=10,           # 连接池中保持的连接数
    max_overflow=20,        # 连接池溢出时允许额外创建的连接数
    echo=True               # 是否打印 SQLAlchemy 执行的 SQL 日志
)


## 创建会话工厂

async_session = async_sessionmaker(   # 创建会话工厂，用于产生会话
    bind=async_engine,                # 绑定的异步引擎
    class_=AsyncSession,              # 会话类型
    expire_on_commit=False            # commit 后对象属性不过期
)

## 定义会话依赖

async def get_db():  # 会话依赖函数，用于注入到 FastAPI 路由
    async with async_session() as session:  # 创建会话，结束后自动关闭会话
        try:
            yield session                   # 将会话交给路由函数使用
            await session.commit()          # 路由执行成功后提交事务
        except Exception:
            await session.rollback()        # 出现异常则回滚事务
            raise


