# Import necessary libraries
import random
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
from typing import Optional
from contextlib import asynccontextmanager

# Import service clients for inter-microservice communication
from service_clients import auth_client, history_client, cleanup_clients

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check if API key is available
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY environment variable is not set!")

# Initialize the Gemini client
try:
    client = genai.Client(api_key=api_key)
    logger.info("Gemini API client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API client: {str(e)}")


# Initialize FastAPI app with lifespan for cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ELI5 service...")
    yield
    # Shutdown
    logger.info("Shutting down ELI5 service...")
    await cleanup_clients()


app = FastAPI(title="LearnInFive API", lifespan=lifespan)


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
class ConceptResponse(BaseModel):
    concept: str
    explanation: str


# Define the prompt template for the Gemini model
def generate_prompt(concept):
    return (
        f"Explain the computer science concept of '{concept}' in a way that a five-year-old would understand. "
        f"Use simple language, real-world analogies, and avoid technical jargon. "
        f"Your explanation should be engaging, clear, and educational. Format your response using markdown "
        f"to make it visually appealing, including headings, lists, bold text, and code examples where appropriate. "
        f"Give a python code explaining the concepts."
    )


# API endpoint to explain a concept
@app.get("/api/explain", response_model=ConceptResponse)
async def explain_concept():
    # concept = (
    #     "Any random computer science concept "  # Fixed concept as per requirements
    # )
    concept = random.choice(CS_CONCEPTS)
    logger.info(f"Randomly selected concept: {concept}")

    if not api_key:
        logger.error("API request made without a valid API key")
        raise HTTPException(status_code=500, detail="API key not configured")

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

        # Return the response with the markdown content
        return {"concept": concept, "explanation": response.text}
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
  \"\"\"
  This algorithm takes a list of toys and puts them in order from smallest to biggest.
  \"\"\"
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


# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Dependency to get current authenticated user from JWT token.
    Returns user data with token included if valid, raises HTTPException otherwise.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from "Bearer <token>" format
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]
        user_data = await auth_client.validate_token(token)

        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Include the token in the user data for other service calls
        user_data["token"] = token
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


# New Pydantic models for user management
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class AuthenticatedConceptResponse(ConceptResponse):
    saved_to_history: bool = False


# User registration endpoint
@app.post("/api/auth/signup")
async def signup_user(user: UserCreate):
    """
    Register a new user via the auth service.
    """
    try:
        result = await auth_client.create_user(
            username=user.username, email=user.email, password=user.password
        )
        return {"message": "User created successfully", "user": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user")


# User login endpoint
@app.post("/api/auth/login")
async def login_user(user: UserLogin):
    """
    Login user and return access token.
    """
    try:
        result = await auth_client.login_user(email=user.email, password=user.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


# Get user history endpoint
@app.get("/api/history")
async def get_user_history(current_user: dict = Depends(get_current_user)):
    """
    Get the authenticated user's concept history.
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        # Get the token from the current request context (we'll need to modify this)
        # For now, we'll need to pass the token through the dependency
        history = await history_client.get_user_history(
            token=current_user.get("token"),  # We'll need to modify auth dependency
            user_id=user_id,
        )

        return {"history": history or []}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get history")


# Updated explain endpoint with authentication (optional)
@app.get("/api/explain/authenticated", response_model=AuthenticatedConceptResponse)
async def explain_concept_authenticated(current_user: dict = Depends(get_current_user)):
    """
    Generate concept explanation for authenticated users and save to history.
    """
    concept = random.choice(CS_CONCEPTS)
    logger.info(f"Generating authenticated explanation for concept: {concept}")

    if not api_key:
        logger.error("API request made without a valid API key")
        raise HTTPException(status_code=500, detail="API key not configured")

    try:
        # Generate explanation (same logic as before)
        prompt = generate_prompt(concept)
        model = os.getenv("GEMINI_MODEL", "gemini-pro")
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        explanation = response.text
        logger.info("Successfully generated content from Gemini API")

        # Save to history
        saved_to_history = False
        try:
            concept_details = {
                "concept": concept,
                "explanation": explanation,
                "model_used": model,
                "prompt": prompt,
            }

            history_result = await history_client.add_history_record(
                token=current_user.get("token"),  # We'll modify this
                concept_details=concept_details,
            )

            saved_to_history = history_result is not None
            if saved_to_history:
                logger.info("Successfully saved concept to user history")
            else:
                logger.warning("Failed to save concept to history")

        except Exception as history_error:
            logger.error(f"Error saving to history: {str(history_error)}")
            # Don't fail the request if history saving fails

        return {
            "concept": concept,
            "explanation": explanation,
            "saved_to_history": saved_to_history,
        }

    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating explanation: {str(e)}",
        )
