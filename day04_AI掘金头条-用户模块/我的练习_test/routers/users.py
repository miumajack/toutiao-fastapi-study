from sqlalchemy.ext.asyncio import  AsyncSession
from starlette import status
from fastapi import APIRouter,Depends,HTTPException
from schemas.users import UserRegister
from config.db_conf import  get_db
from crud.users import  check_by_username,create_user,create_token


router = APIRouter(prefix='/api/user',tags=['user'])

@router.post('/register')
async def user_register(userdata:UserRegister,db:AsyncSession=Depends(get_db)):
    user = await check_by_username(userdata.username,db)
    if user:
        print('user_None测试============')
        print(user)
        print('user_None测试============')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='用户已注册'
            
        )
        
    #创建用户
    new_user = await create_user(user_pydantic=userdata,db=db)
    print(f'================{type(new_user)}================')
    user_token = await create_token(user_id=new_user.id,db=db)  
        
    return{
    "code": 200,
    "message": "注册成功",
    "data": {
        "token": user_token.token,
        "userInfo": {
        "id": new_user.id,
        "username": userdata.username,
        "bio": "这个人很懒，什么都没留下",
        "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
    }
}
}