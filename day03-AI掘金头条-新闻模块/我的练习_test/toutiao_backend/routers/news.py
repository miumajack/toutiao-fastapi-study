
from fastapi import APIRouter,Depends, Query
from config.db_conf import get_db
from crud.news import get_news_category,get_news_list,get_news_total
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix='/api/news',tags=['news'])

@router.get('/categories')
async def get_cat(page:int=1,page_size:int=8,db:AsyncSession=Depends(get_db)):
    
    data = await get_news_category(db,page,page_size)
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
        data = await get_news_list(db,category_id,page,page_size)
        total = await get_news_total(db,category_id)
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

print(">>> 我在这里 <<<", __file__)