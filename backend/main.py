from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.initiate_table import recreate_tables


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8443", "http://127.0.0.1:8443", "http://150.240.70.64:8080", "http://127.0.0.1:8000"],  # Update with the address of your React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
