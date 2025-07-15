# Import necessary libraries
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our custom modules
from database import create_tables
from routers import auth, explain, health, history

# Set up logging
logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the variables and functions that tests expect
# These imports need to be here for the tests to find them


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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
origins: list[str] = [
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
