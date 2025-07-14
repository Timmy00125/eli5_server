# Import necessary libraries
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Import our custom modules
from database import create_tables
from routers import auth, history, explain, health

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes database tables when the application starts.
    """
    # Startup
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        logger.warning("Application will continue without database connectivity")

    yield

    # Shutdown (if needed)
    logger.info("Application shutdown")


# Initialize FastAPI app
app = FastAPI(
    title="LearnInFive API",
    description="Learn computer science concepts in simple terms",
    lifespan=lifespan,
)

# List of allowed origins
origins = [
    "http://localhost:3000",  # Local development
    "https://eli5-client.vercel.app",  # Production
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(explain.router)
app.include_router(health.router)
