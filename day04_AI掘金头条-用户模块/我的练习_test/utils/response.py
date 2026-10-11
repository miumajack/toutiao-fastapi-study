from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def fun_response(data,code='200',message='success'):
    content = {
        'code':code,
        'message':message,
        'data':data
    }
    return JSONResponse(content=jsonable_encoder(content))
    