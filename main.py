# Import necessary libraries
import random
from datetime import timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import logging

# Import our custom modules
from database import get_db, create_tables
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from schemas import (
    UserRegistration,
    UserLogin,
    TokenResponse,
    ConceptResponse,
    MessageResponse,
    HistoryListResponse,
    SaveHistoryRequest,
    HistoryEntryResponse,
    UserResponse,
)
from services import UserService, HistoryService
from database import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check if API key is available
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.warning(
        "GEMINI_API_KEY environment variable is not set! Gemini API features will be disabled."
    )

# Initialize the Gemini client
client = None
try:
    if api_key:
        client = genai.Client(api_key=api_key)
        logger.info("Gemini API client initialized successfully")
    else:
        logger.info("Gemini API client not initialized - API key not provided")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API client: {str(e)}")
    client = None


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


# Create database tables on startup
# (Now handled by lifespan event handler above)


# List of Computer Science Concepts
CS_CONCEPTS = [
    "Algorithm",
    "Data Structure",
    "Variable",
    "Function",
    "Loop",
    "Conditional Statement (If/Else)",
    "API (Application Programming Interface)",
    "Database",
    "Version Control (Git)",
    "Operating System",
    "Computer Network",
    "IP Address",
    "DNS (Domain Name System)",
    "HTML",
    "CSS",
    "JavaScript",
    "Python Programming Language",
    "Debugging",
    "Encryption",
    "Cloud Computing",
    "Machine Learning",
    "Artificial Intelligence",
    "Binary Code",
    "Compiler",
    "Recursion",
    "Object-Oriented Programming (OOP)",
    "Boolean Logic",
    "CPU (Central Processing Unit)",
    "RAM (Random Access Memory)",
    "Software Development Life Cycle (SDLC)",
]


# origin = os.getenv("ORIGIN")

origins = [
    "http://localhost:3000",  # Local development
    "https://eli5-client.vercel.app",  # Production
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response model
# (ConceptResponse is imported from schemas)


# Define the prompt template for the Gemini model
def generate_prompt(concept: str) -> str:
    return (
        f"Explain the computer science concept of '{concept}' in a way that a five-year-old would understand. "
        f"Use simple language, real-world analogies, and avoid technical jargon. "
        f"Your explanation should be engaging, clear, and educational. Format your response using markdown "
        f"to make it visually appealing, including headings, lists, bold text, and code examples where appropriate. "
        f"Give a python code explaining the concepts."
    )


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================


@app.post("/api/auth/register", response_model=TokenResponse)
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Creates a new user with email, username, and hashed password.
    Returns access token for immediate login.
    """
    try:
        # Create the user
        user = UserService.create_user(db, user_data)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return TokenResponse(access_token=access_token, user=user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.

    Verifies email and password, returns JWT token for authenticated requests.
    """
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, user=user)


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Returns user profile data for the authenticated user.
    """
    return current_user


# =============================================================================
# HISTORY ENDPOINTS
# =============================================================================


@app.get("/api/history", response_model=HistoryListResponse)
async def get_user_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's history of explained concepts.

    Returns paginated list of user's saved concept explanations.
    """
    entries, total = HistoryService.get_user_history(db, current_user.id, limit, offset)

    return HistoryListResponse(
        entries=[HistoryEntryResponse.model_validate(entry) for entry in entries],
        total=total,
    )


@app.post("/api/history", response_model=HistoryEntryResponse)
async def save_history_entry(
    history_data: SaveHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save a concept explanation to user's history.

    Allows authenticated users to save explanations for future reference.
    """
    try:
        entry = HistoryService.save_history_entry(db, current_user.id, history_data)
        return entry

    except Exception as e:
        logger.error(f"Error saving history entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save history entry",
        )


@app.delete("/api/history/{entry_id}", response_model=MessageResponse)
async def delete_history_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a history entry.

    Removes a specific history entry from the user's saved explanations.
    """
    success = HistoryService.delete_history_entry(db, entry_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="History entry not found"
        )

    return MessageResponse(message="History entry deleted successfully")


# =============================================================================
# CONCEPT EXPLANATION ENDPOINTS
# =============================================================================


# API endpoint to explain a concept
@app.get("/api/explain", response_model=ConceptResponse)
async def explain_concept():
    concept = random.choice(CS_CONCEPTS)
    logger.info(f"Randomly selected concept: {concept}")

    if not api_key or not client:
        logger.error("API request made without a valid API key or client")
        raise HTTPException(
            status_code=500,
            detail="Gemini API not configured - please set GEMINI_API_KEY environment variable",
        )

    try:
        logger.info(f"Generating explanation for concept: {concept}")

        # Create the prompt
        prompt = generate_prompt(concept)

        # Set up the model and contents according to the new API format
        model = os.getenv(
            "GEMINI_MODEL", "gemini-pro"
        )  # Using gemini-pro as the default model
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        # Configure the generation parameters
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )

        # Generate content
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        logger.info("Successfully generated content from Gemini API")

        # Extract the explanation text from response
        explanation_text = (
            response.text if response.text else "Unable to generate explanation"
        )

        # Return the response with the markdown content
        return ConceptResponse(concept=concept, explanation=explanation_text)
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        # Return a more graceful error while still providing useful information
        raise HTTPException(
            status_code=500,
            detail=f"Error generating explanation. Please check your API key and network connection. Error: {str(e)}",
        )


# Fallback endpoint with the markdown example you provided
@app.get("/api/fallback-explain", response_model=ConceptResponse)
async def fallback_explain_concept():
    concept = "Algorithms"
    explanation = """Imagine you want to build a really tall tower with your blocks.  You can't just throw blocks randomly, right? You need a plan!

That's kind of what an **algorithm** is!  It's like a **set of instructions**, like a recipe, to do something.

Let's say you want to make a peanut butter and jelly sandwich.  You wouldn't just magically have a sandwich appear! You need to follow steps, right?

Here's a **sandwich algorithm**:

1. **Get two slices of bread.**  (Imagine holding up two pieces of bread)
2. **Get the peanut butter.** (Pretend to open a peanut butter jar)
3. **Use a spoon to put peanut butter on one slice of bread.** (Show spreading motion)
4. **Get the jelly.** (Pretend to open a jelly jar)
5. **Use a *clean* spoon to put jelly on the *other* slice of bread.** (Show spreading motion with a different imaginary spoon)
6. **Put the two slices of bread together, peanut butter and jelly sides facing each other.** (Clap your hands together with bread in between)
7. **Yay! You made a sandwich!** (Pretend to take a bite)

See?  Those steps are an **algorithm** for making a sandwich! It's a list of things to do, in order, to get a sandwich at the end.

**Computers are like super-fast helpers!**  But they aren't smart on their own. You have to tell them *exactly* what to do, step-by-step, just like our sandwich recipe.

When we give computers these step-by-step instructions, we call them **algorithms**.

**Think of it like this:**

* **You are the chef.** You know what you want the computer to do (like make a sandwich, or in computer terms, maybe sort toys by color, or draw a picture).
* **The algorithm is your recipe book.** It tells the computer *exactly* what to do in what order.
* **The computer is your super-fast kitchen helper.** It follows your recipe (algorithm) very quickly to do what you want.

Algorithms can be for anything!

* **Brushing your teeth algorithm:** 1. Get toothbrush. 2. Put toothpaste on toothbrush. 3. Brush up and down. 4. Brush side to side. 5. Rinse mouth.
* **Finding your red car toy algorithm:** 1. Look in the toy box. 2. Is it red? 3. Is it a car? 4. If yes to both, you found it! If no, keep looking.

**So, algorithms are just lists of steps to solve problems or do things, and computers use them to do amazing things really fast!**

Now, let's see a little bit of how we can write an algorithm for a computer using something called Python. Don't worry if it looks a little strange, just see if you can spot the steps!

```python
# This is like our "recipe" for sorting toys by size!

def sort_toys_by_size(toys):
  """
  This algorithm takes a list of toys and puts them in order from smallest to biggest.
  """
  sorted_toys = sorted(toys) # This one line does all the magic sorting!
  return sorted_toys

# Let's say these are our toys (imagine sizes from smallest to biggest)
my_toys = ["small teddy bear", "medium car", "big truck"]

# Now we use our algorithm to sort them
sorted_toys_list = sort_toys_by_size(my_toys)

# Let's see the sorted toys!
print(sorted_toys_list) # The computer will show us the toys in order! 
```
"""

    return ConceptResponse(concept=concept, explanation=explanation)


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.

    Returns the application status and database connectivity.
    """
    try:
        # Test database connection
        db = next(get_db())
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        db_status = "connected"
        db.close()
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "message": "ELI5 Server is running successfully!",
    }
