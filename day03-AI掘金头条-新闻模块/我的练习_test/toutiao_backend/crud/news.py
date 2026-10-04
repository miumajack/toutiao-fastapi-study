from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from models.news import Category,News

async def get_news_category(db:AsyncSession,page=1,page_size=3):
    skip = (page-1)*page_size
    category_orm = await db.execute(select(Category).offset(skip).limit(page_size))
    data = category_orm.scalars().all()
    return data

#返回同一个类别下的分页结果
async def get_news_list(db:AsyncSession,category_id:int,page:int=1,page_size:int=1):
    #进行分页
    skip = (page-1)*page_size
    new_list=await db.execute(select(News).where(News.category_id==category_id).offset(skip).limit(page_size))
    res = new_list.scalars().all()
    return res


#返回总量
async def get_news_total(db:AsyncSession,category_id:int):
    num = await db.execute(select(func.count(News.id)).where(News.category_id==category_id))
    res = num.scalar_one()
    return res