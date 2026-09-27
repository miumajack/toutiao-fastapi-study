from fastapi import FastAPI

app =  FastAPI()

@app.get('/')
def hello():
    return {'message': 'hello8888'}

@app.get('/hello')
def hello_2():
    return {'message': 'hello_fastapi'}