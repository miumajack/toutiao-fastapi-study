from fastapi import FastAPI, Path

app = FastAPI()

@app.get('/book/{book_id}')
def get_book(book_id : int = Path(..., description='根据id查找对应的书籍', ge=1,lt=10) ):
    return {'id':book_id,
            'title':f'这是第{book_id}本书'
            }

@app.get('/author/{name}')
def get_name(name: str = Path(..., description='查询书籍的作者',min_length=2,max_length=10)):
    return {'name':f'书的作者是{name}'}