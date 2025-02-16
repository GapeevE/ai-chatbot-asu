from fastapi.middleware.cors import CORSMiddleware
from models.index import ChatMessage
from providers.ollama import query_rag
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
async def read_root():
    return {"Hello": "world"}

@app.post("/chat/{chat_id}")
async def ask(chat_id: str, message: ChatMessage):
    return {"response": query_rag(message, chat_id)}