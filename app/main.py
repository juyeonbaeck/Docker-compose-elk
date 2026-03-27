from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from elasticsearch import AsyncElasticsearch
import os
import logging

logger = logging.getLogger("uvicorn.error")

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
INDEX_NAME = "items"

es: AsyncElasticsearch = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global es
    es = AsyncElasticsearch([ES_HOST])
    # 인덱스 없으면 자동 생성
    if not await es.indices.exists(index=INDEX_NAME):
        await es.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text"},
                        "tag": {"type": "keyword"},
                    }
                },
            },
        )
        logger.info(f"Index '{INDEX_NAME}' created.")
    yield
    await es.close()


app = FastAPI(title="FastAPI + Elasticsearch Demo", lifespan=lifespan)


class Item(BaseModel):
    title: str
    description: str
    tag: str = "general"


@app.get("/health")
async def health():
    cluster = await es.cluster.health()
    return {"api": "ok", "es_status": cluster["status"]}


@app.post("/items", status_code=201)
async def create_item(item: Item):
    resp = await es.index(index=INDEX_NAME, document=item.model_dump())
    return {"id": resp["_id"], **item.model_dump()}


@app.get("/items/search")
async def search_items(q: str = Query(..., min_length=1)):
    resp = await es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["title^2", "description"],  # title 가중치 2배
                }
            }
        },
    )
    hits = [{"id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]
    return {"total": resp["hits"]["total"]["value"], "results": hits}


@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    try:
        await es.delete(index=INDEX_NAME, id=item_id)
        return {"deleted": item_id}
    except Exception:
        raise HTTPException(status_code=404, detail="Item not found")
