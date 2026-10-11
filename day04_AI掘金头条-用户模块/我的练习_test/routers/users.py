from sqlalchemy.ext.asyncio import  AsyncSession
from starlette import status
from fastapi import APIRouter,Depends,HTTPException
from schemas.users import UserRegister
from config.db_conf import  get_db
from crud.users import  check_by_username,create_user,create_token,verify_user
from utils import response
from schemas import users
from utils import auth

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
    user_data=users.User_AuthResponse(token=user_token.token,userInfo=users.UserInfo.model_validate(new_user))
    res=response.fun_response(code='200',message='注册成功',data=user_data)
    ###要return
    return res   
#     return{
#     "code": 200,
#     "message": "注册成功",
#     "data": {
#         "token": user_token.token,
#         "userInfo": {
#         "id": new_user.id,
#         "username": userdata.username,
#         "bio": "这个人很懒，什么都没留下",
#         "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
#     }
# }
# }

##用户登录

@router.post('/login')
async def user_login(userdata:UserRegister,db:AsyncSession=Depends(get_db)):
    user= await verify_user(username=userdata.username,password=userdata.password,db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='账号或密码错误'
            )
    #账号密码对了发放新token
    new_token = await create_token(user_id=user.id,db=db)
    login_data=users.User_AuthResponse(token=new_token.token,userInfo=users.UserInfo.model_validate(user))
    res = response.fun_response(message='登录成功',data=login_data)
    return res


##查看用户信息
@router.get("/info")
async def get_user_info(user=Depends(auth.token_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='token过期')
    userinfo_data=users.User_AuthResponse(token=user.token,userInfo=users.UserInfo.model_validate(user))
    res = response.fun_response(data=userinfo_data)
    return res
