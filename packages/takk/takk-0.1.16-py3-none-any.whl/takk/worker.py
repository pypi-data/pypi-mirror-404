import logging
from fastapi import FastAPI, Request
from takk.models import QueueMessage

logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/")
async def background_worker(request: Request) -> None:
    logging.basicConfig(level=logging.INFO)
    body = await request.body()
    content = QueueMessage.model_validate_json(body)
    await content.run()
