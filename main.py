# Import necessary libraries
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
from fastapi.responses import StreamingResponse
import json

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

# Initialize FastAPI app
app = FastAPI(title="LearnInFive API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
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
        f"The explanation should be engaging, clear, and educational."
        f"Give a python code implementing the concept"
    )


# API endpoint to explain a concept
@app.get("/api/explain", response_model=ConceptResponse)
async def explain_concept():
    concept = "Algorithms"  # Fixed concept as per requirements

    if not api_key:
        logger.error("API request made without a valid API key")
        raise HTTPException(status_code=500, detail="API key not configured")

    try:
        logger.info(f"Generating explanation for concept: {concept}")

        # Create the prompt
        prompt = generate_prompt(concept)

        # Set up the model and contents according to the new API format
        model = "gemini-2.0-flash-thinking-exp-01-21"  # Using gemini-pro as the default model
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

        # Return the response
        return {
            "concept": concept,
            "explanation": response.text
        }
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        # Return a more graceful error while still providing useful information
        raise HTTPException(
            status_code=500,
            detail=f"Error generating explanation. Please check your API key and network connection. Error: {str(e)}"
        )


# Fallback endpoint to provide a static explanation if Gemini API fails
@app.get("/api/fallback-explain", response_model=ConceptResponse)
async def fallback_explain_concept():
    concept = "Algorithms"
    explanation = """
    Imagine you're making a sandwich. An algorithm is like your recipe!

    It's a list of steps that tells you exactly what to do:
    1. Take two slices of bread
    2. Spread peanut butter on one slice
    3. Spread jelly on the other slice
    4. Put the slices together

    Computers use algorithms too! They follow step-by-step instructions to solve problems or do tasks. 
    Just like how your recipe helps you make a yummy sandwich, algorithms help computers know exactly what to do!
    """

    return {
        "concept": concept,
        "explanation": explanation
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "api_key_configured": bool(api_key)}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)