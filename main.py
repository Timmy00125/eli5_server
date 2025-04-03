# Import necessary libraries
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    )


# API endpoint to explain a concept
@app.get("/api/explain", response_model=ConceptResponse)
async def explain_concept():
    concept = "Algorithms"  # Fixed concept as per requirements

    try:
        # Generate content with Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(generate_prompt(concept))

        # Format and return the response
        return {
            "concept": concept,
            "explanation": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)