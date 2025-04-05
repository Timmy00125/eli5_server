# Import necessary libraries
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging

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


# origin = os.getenv("ORIGIN")

origins = [
    "http://localhost:3000",  # Local development
    "https://eli5-client.vercel.app/",  # Production
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
    concept = "Algorithms"  # Fixed concept as per requirements

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
