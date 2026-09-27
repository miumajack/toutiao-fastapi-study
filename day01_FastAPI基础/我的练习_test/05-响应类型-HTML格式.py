from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/html/{id}',response_class=HTMLResponse)
def get_html(id: int):
    return f'<h1>这是第{id}本书</h1>'

