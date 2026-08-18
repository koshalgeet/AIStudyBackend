
````python
import os
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Study With Raman AI Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class QuestionRequest(BaseModel):
    question: str


class TopicRequest(BaseModel):
    topic: str


class QuizRequest(BaseModel):
    topic: str
    number_of_questions: int = Field(
        default=5,
        ge=1,
        le=10
    )


class FlashcardRequest(BaseModel):
    topic: str
    number_of_cards: int = Field(
        default=5,
        ge=1,
        le=20
    )


# ============================================================
# CONFIG
# ============================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Study With Raman AI Backend is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    api_key = os.getenv("GEMINI_API_KEY")

    return {
        "status": "healthy",
        "api_key_found": bool(api_key),
        "model": GEMINI_MODEL
    }


# ============================================================
# ERROR HANDLING
# ============================================================

def handle_gemini_error(error: Exception):

    error_text = str(error)

    print("GEMINI ERROR:", error_text)

    if (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "quota" in error_text.lower()
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "AI request limit temporarily reached. "
                "Please wait a little and try again."
            )
        )

    raise HTTPException(
        status_code=500,
        detail="AI service is temporarily unavailable. Please try again."
    )


# ============================================================
# GEMINI FUNCTION
# ============================================================

def ask_gemini(prompt: str) -> str:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is missing."
        )

    client = genai.Client(
        api_key=api_key
    )

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        answer = response.text

        if not answer or not answer.strip():
            raise Exception(
                "Gemini returned an empty response"
            )

        return answer.strip()

    except HTTPException:
        raise

    except Exception as error:
        handle_gemini_error(error)


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    prompt = f"""
You are Raman AI Tutor.

Answer the student's question clearly and correctly.

Rules:
- Give a short answer by default.
- Use simple language.
- If the student asks in Hindi or Hinglish, answer in Hindi or Hinglish.
- If the student asks in English, answer in English.
- Explain only what is necessary.
- Give an example only when useful.
- Do not add unnecessary information.

Student Question:

{question}
"""

    answer = ask_gemini(prompt)

    return {
        "answer": answer
    }


# ============================================================
# SMART NOTES
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: TopicRequest):

    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty."
        )

    prompt = f"""
Create simple and useful study notes about:

{topic}

Include:

1. Introduction
2. Important concepts
3. Simple explanation
4. Important points
5. Short summary

Use easy language.

Do not make the answer unnecessarily long.
"""

    answer = ask_gemini(prompt)

    return {
        "notes": answer
    }


# ============================================================
# AI QUIZ
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty."
        )

    prompt = f"""
Create exactly {request.number_of_questions} multiple choice quiz questions.

Topic: {topic}

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not write any explanation outside JSON.

Use exactly this format:

{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "correctAnswer": 0,
      "explanation": "Short explanation"
    }}
  ]
}}

Rules:

- Generate exactly {request.number_of_questions} questions.
- Every question must have exactly 4 options.
- correctAnswer must be a number from 0 to 3.
- explanation should be short.
- Return JSON only.
"""

    try:

        answer = ask_gemini(prompt)

        cleaned = answer.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Gemini did not return valid JSON."
            )

        data = json.loads(
            cleaned[start:end + 1]
        )

        questions = data.get(
            "questions",
            []
        )

        valid_questions = []

        for item in questions:

            question = item.get(
                "question",
                ""
            )

            options = item.get(
                "options",
                []
            )

            correct_answer = item.get(
                "correctAnswer",
                0
            )

            explanation = item.get(
                "explanation",
                ""
            )

            if (
                isinstance(question, str)
                and question.strip()
                and isinstance(options, list)
                and len(options) == 4
                and isinstance(correct_answer, int)
                and 0 <= correct_answer <= 3
            ):

                valid_questions.append(
                    {
                        "question": question.strip(),
                        "options": options,
                        "correctAnswer": correct_answer,
                        "explanation": str(explanation)
                    }
                )

        if not valid_questions:
            raise ValueError(
                "No valid quiz questions generated."
            )

        return {
            "questions": valid_questions
        }

    except HTTPException:
        raise

    except Exception as error:

        print("QUIZ ERROR:", str(error))

        raise HTTPException(
            status_code=500,
            detail="Quiz could not be generated. Please try again."
        )


# ============================================================
# FLASHCARDS
# ============================================================

@app.post("/generate-flashcards")
def generate_flashcards(
    request: FlashcardRequest
):

    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty."
        )

    prompt = f"""
Create exactly {request.number_of_cards} useful study flashcards.

Topic: {topic}

Return ONLY valid JSON.

Use exactly this format:

{{
  "flashcards": [
    {{
      "front": "Question or term",
      "back": "Short simple answer"
    }}
  ]
}}

Rules:

- Generate exactly {request.number_of_cards} flashcards.
- Keep answers short and easy to remember.
- Return JSON only.
"""

    try:

        answer = ask_gemini(prompt)

        cleaned = answer.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Gemini did not return valid JSON."
            )

        data = json.loads(
            cleaned[start:end + 1]
        )

        flashcards = data.get(
            "flashcards",
            []
        )

        valid_cards = []

        for item in flashcards:

            front = str(
                item.get("front", "")
            ).strip()

            back = str(
                item.get("back", "")
            ).strip()

            if front and back:

                valid_cards.append(
                    {
                        "front": front,
                        "back": back
                    }
                )

        if not valid_cards:
            raise ValueError(
                "No valid flashcards generated."
            )

        return {
            "flashcards": valid_cards
        }

    except HTTPException:
        raise

    except Exception as error:

        print(
            "FLASHCARDS ERROR:",
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Flashcards could not be generated. Please try again."
        )


# ============================================================
# AI PRACTICE TEST
# ============================================================

@app.post("/ai-test")
def ai_test(request: TopicRequest):

    topic = request.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty."
        )

    prompt = f"""
Create a useful practice test about:

{topic}

Include:

1. Five multiple choice questions.
2. Three short answer questions.
3. A separate answer key at the end.

Use simple and clear language.

Make the practice test suitable for students.
"""

    answer = ask_gemini(prompt)

    return {
        "test": answer
    }
````
