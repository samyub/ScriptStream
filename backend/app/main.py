import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routes.research import router as research_router

app = FastAPI(
    title="Dyut Research Agent",
    description="PRAT Framework YouTube/Reddit Research Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
