
from fastapi import APIRouter,Depends, Query,HTTPException
from config.db_conf import get_db
from crud import news 
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix='/api/news',tags=['news'])

@router.get('/categories')
async def get_cat(page:int=1,page_size:int=8,db:AsyncSession=Depends(get_db)):
    
    data = await news.get_news_category(db,page,page_size)
    return {
    "code": 200,
    "message": "success",
    "data": data  
    }


@router.get('/list')
async def get_list(db:AsyncSession=Depends(get_db),
                        category_id:int=Query(2,alias='categoryId'),
                        page:int=1,
                        page_size: int=Query(default=3,le=100,alias='pageSize'),
                        ):
        data = await news.get_news_list(db,category_id,page,page_size)
        total = await news.get_news_total(db,category_id)
        has_more = (len(data)+(page-1)*page_size<total)
        return {
                "code": 200,
                "message": "success",
                "data": {
                    "list": data,
                    "total": total,
                    "hasMore": has_more
        }
}


@router.get('/detail')
async def get_detail(news_id:int=Query(...,alias='id'),
                    db:AsyncSession=Depends(get_db)
                        ):
    res = await news.get_news_detail(db,news_id)
    if res is None:
            raise HTTPException(
                status_code=404,
                detail='新闻不存在'
            )
        
    views =await news.get_news_views(db,news_id) 
    if views is None:
                raise HTTPException(
                    status_code=404,
                    detail='浏览新闻不存在'
                )
    related_news = await news.get_relatedNews(db,news_id,category_id=res.category_id)
    
    
    return {
        "code": 200,
        "message": "success",
        "data": {
                "id": res.id,
                "title": res.title,
                "content": res.content,
                "image": res.image,
                "author": res.author,
                "publishTime":res.publish_time,
                "categoryId": res.category_id,
                "views": res.views,
                "relatedNews": related_news
        }
}
    

print(">>> 我在这里 <<<", __file__)