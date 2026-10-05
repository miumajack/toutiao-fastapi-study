from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from models.news import Category, News


async def get_news_category(db: AsyncSession, page=1, page_size=3):
    skip = (page - 1) * page_size
    category_orm = await db.execute(select(Category).offset(skip).limit(page_size))
    data = category_orm.scalars().all()
    return data


# 返回同一个类别下的分页结果
async def get_news_list(
    db: AsyncSession, category_id: int, page: int = 1, page_size: int = 1
):
    # 进行分页
    skip = (page - 1) * page_size
    new_list = await db.execute(
        select(News)
        .where(News.category_id == category_id)
        .offset(skip)
        .limit(page_size)
    )
    res = new_list.scalars().all()
    return res


# 返回总量
async def get_news_total(db: AsyncSession, category_id: int):
    num = await db.execute(
        select(func.count(News.id)).where(News.category_id == category_id)
    )
    res = num.scalar_one()
    return res


# 返回新闻详情
async def get_news_detail(db: AsyncSession, news_id: int):
    news_detail = await db.execute(select(News).where(News.id == news_id))
    res = news_detail.scalar_one_or_none()
    return res


# 返回新闻浏览量并增加
async def get_news_views(db: AsyncSession, news_id: int):
    res =await db.execute(
        update(News).where(News.id == news_id).values(views=News.views + 1)
    )
    await db.commit()
    # res = news_view.scalar_one()  # 更新后的值update不返回值
    return res.rowcount > 0


# 返回同类的点赞高，时间近的新闻
async def get_relatedNews(
    db: AsyncSession, news_id: int, category_id: int=0, limit: int = 10
):
    res = await db.execute(
        select(News)
        .where(News.category_id == category_id, News.id != news_id)
        .order_by(News.views.desc(), News.publish_time.desc())
        .limit(limit)
    )
    result = res.scalars().all()
    return [{
                        "id": res.id,
                        "title": res.title,
                        "content": res.content,
                        "author": res.author,
                        "categoryId": res.category_id,
                        "views": res.views,
                    
    }
        for res in result]
