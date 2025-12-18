from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.initiate_table import recreate_tables


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "query": q}

@app.post("/initiate_tables")
def initiate_tables():
    try:
        recreate_tables("table_schema.yaml")   # can also be absolute path
        return {"status": "success", "message": "Tables recreated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
