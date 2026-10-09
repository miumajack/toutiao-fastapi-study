
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def response_json(data,message:str='success'):
    content={
        "code":200,
        'message':message,
        'data':data
    }
    return JSONResponse(jsonable_encoder(content))