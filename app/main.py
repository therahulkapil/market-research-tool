from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.config_loader import load_config
from app.api.report_generator import router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router) 

@app.on_event("startup")
async def startup_event():
    logger.info("Loading configuration...")
    load_config()
    logger.info("Application started.")

app.include_router(router) 
