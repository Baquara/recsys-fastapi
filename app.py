from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from typing import Optional
import time
import os
import json
import pandas as pd
import collaborative_filtering_rec
import content_based_rec
from typing import List, Dict
import subprocess
from fastapi.openapi.utils import get_openapi
from starlette.responses import JSONResponse
from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    itemId: str
    title: str
    description: str
    tag: List[str]

class ItemList(BaseModel):
    items: List[Item]

app = FastAPI()

engine = create_engine("sqlite:///db0.db?check_same_thread=False")

@app.delete("/clear_db")
async def clear_db(request: Request):
    with engine.begin() as conn:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        for table_name in table_names:
            delete_query = text(f'DELETE FROM {table_name}')
            conn.execute(delete_query)
    return {"detail": "Database cleared successfully"}

@app.get("/docs", include_in_schema=False)
async def get_documentation():
    """
    Custom endpoint to display the API documentation.
    """
    openapi_schema = get_openapi(
        title="Recommender System API",
        version="1.0.0",
        description="A general-use recommender system API",
        routes=app.routes,
    )
    return JSONResponse(content=openapi_schema)


@app.post("/item")
async def add_items_to_items(items_data: ItemList):
    with engine.begin() as connection:
        for item in items_data.items:
            # Convert tags list to string representation
            tags = json.dumps(item.tag)
            query = text('INSERT INTO items (itemId, title, description, tag) VALUES (:itemId, :title, :description, :tag)')
            connection.execute(query, {
                'itemId': item.itemId,
                'title': item.title,
                'description': item.description,
                'tag': tags
            })
    return {"detail": "Items added to items successfully"}

@app.post("/user")
async def add_items_to_user(request: Request):
    item_user_data = await request.json()
    with engine.begin() as conn:
        for item in item_user_data['items']:
            query = text('INSERT INTO users (userId, itemId, rating, timestamp) VALUES (:userId, :itemId, :rating, :timestamp)')
            conn.execute(query, {'userId': item['userId'], 'itemId': item['itemId'], 'rating': item['rating'], 'timestamp': item['timestamp']})
    return {"detail": "Ratings added successfully"}

@app.get("/items")
def get_items():
    with engine.begin() as conn:
        query = text('SELECT * FROM items')
        result = pd.read_sql_query(query, conn)
    return json.loads(result.to_json(orient="records"))

@app.delete("/user")
async def delete_user(request: Request):
    user = await request.json()
    with engine.begin() as conn:
        query = text('DELETE FROM users WHERE userId = :userId')
        conn.execute(query, user)
    return user

@app.get("/user")
async def get_user(request: Request):
    user = await request.json()
    with engine.begin() as conn:
        query = text('SELECT * FROM users WHERE userId = :userId')
        result = pd.read_sql_query(query, conn, params=user)
    return json.loads(result.to_json(orient="records"))

@app.get("/users")
def get_users():
    with engine.begin() as conn:
        query = text('SELECT * FROM users')
        result = pd.read_sql_query(query, conn)
    return json.loads(result.to_json(orient="records"))

@app.get("/user/events")
async def get_events(request: Request):
    user = await request.json()
    with engine.begin() as conn:
        query = text('SELECT * FROM events WHERE userId = :userId')
        result = pd.read_sql_query(query, conn, params=user)
    return json.loads(result.to_json(orient="records"))

@app.delete("/item")
async def delete_item(request: Request):
    item = await request.json()
    with engine.begin() as conn:
        query = text('DELETE FROM items WHERE itemId = :itemId')
        conn.execute(query, item)
    return item



@app.put("/item/{item_id}")
async def update_item(item_id: str, request: Request):
    item_data = await request.json()
    with engine.begin() as conn:
        query = text('UPDATE items SET title = :title, description = :description, tag = :tag WHERE itemId = :itemId')
        result = conn.execute(query, {
            'itemId': item_id,
            'title': item_data['title'],
            'description': item_data['description'],
            'tag': json.dumps(item_data['tag'])
        })
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item updated successfully"}

@app.put("/user/{user_id}")
async def update_user(user_id: str, request: Request):
    user_data = await request.json()
    with engine.begin() as conn:
        query = text('UPDATE users SET rating = :rating, timestamp = :timestamp WHERE userId = :userId AND itemId = :itemId')
        for item in user_data['items']:
            result = conn.execute(query, {
                'userId': user_id,
                'itemId': item['itemId'],
                'rating': item['rating'],
                'timestamp': item['timestamp']
            })
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} or item with ID {item['itemId']} not found")
    return {"detail": "User ratings updated successfully"}

@app.get("/item/neighbors")
async def get_similar_items(request: Request):
    itemno = request.query_params.get("itemno", 1)
    nitems = request.query_params.get("nitems", 3)
    lis = content_based_rec.start(0, int(itemno), int(nitems))
    exec_time = 0
    result = {"Item_number": "1", "API_exec_time": str(exec_time), "items": lis}
    return result

@app.get("/item/events")
async def get_item_events(request: Request):
    item = await request.json()
    with engine.begin() as conn:
        query = text('SELECT * FROM events WHERE itemId = :itemId')
        result = pd.read_sql_query(query, conn, params=item)
    return json.loads(result.to_json(orient="records"))

@app.post("/event")
async def post_event(request: Request):
    event = await request.json()
    with engine.begin() as conn:
        query = text('INSERT INTO events (userId, itemId, rating, timestamp) VALUES (:userId, :itemId, :rating, :timestamp)')
        conn.execute(query, event)
    return event

@app.get("/events")
def get_events():
    with engine.begin() as conn:
        query = text('SELECT * FROM events')
        result = pd.read_sql_query(query, conn)
    return json.loads(result.to_json(orient="records"))

@app.get("/user/recommendations", response_model=List[Dict])
def get_user_rec(nrec: Optional[int] = None, sel_item: Optional[str] = None):
    results = collaborative_filtering_rec.start(nrec,sel_item)
    return results

@app.post("/train")
def post_user_rec():
    return train.train_rec()

@app.get("/system")
def get_system():
    uptime = subprocess.check_output("uptime").decode().strip()
    total_ram = subprocess.check_output("free -m | awk 'NR==2{print $2}'", shell=True).decode().strip()
    available_ram = subprocess.check_output("free -m | awk 'NR==2{print $7}'", shell=True).decode().strip()
    cpu_model = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | uniq | awk -F: '{print $2}'", shell=True).decode().strip()
    cpu_clock = subprocess.check_output("cat /proc/cpuinfo | grep 'cpu MHz' | uniq | awk -F: '{print $2}'", shell=True).decode().strip()
    
    # Obtain the current directory path
    current_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(current_dir, "db0.db")
    estringue = f'du -sh {db_path}'
    database_size = subprocess.check_output(f"du -sh \'{db_path}\'", shell=True).decode().strip()
    
    return {
        'uptime': uptime,
        'total_ram': total_ram,
        'available_ram': available_ram,
        'cpu_model': cpu_model,
        'cpu_clock': cpu_clock,
        'database_size': database_size
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
