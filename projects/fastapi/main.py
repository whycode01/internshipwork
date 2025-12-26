from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "tetsing FastApi"}

items=[]

@app.post("/items")
def create_item(item: str):
    items.append(item)
    return {"items": items}

@app.get("/items")
def get_items():
    return {"items": items}