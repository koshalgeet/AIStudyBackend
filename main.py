````python
import os
import json
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai


app = FastAPI(
    title="Study With Raman AI Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Agar Render Environment Variable me GEMINI_MODEL set nahi hai,
# to ye model use hoga.
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)

client: Optional[genai.Client] = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
    print("Gemini client initialized")
    print("Model:", GEMINI_MODEL)
else:
    print("WARNING: GEMINI_API_KEY not found")


class QuestionRequest(BaseModel):
    question: str


class TopicRequest(BaseModel):
    topic: str


class QuizRequest(BaseModel):
    topic: str
    number_of_questions: int = 5


def ask_gemini(prompt: str) -> str:
    if client is None:
        raise Exception(
            "GEMINI_API_KEY is not configured."
        )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    answer = getattr(response, "text", "")

    if not answer or not answer.strip():
        raise Exception(
            "Gemini returned an empty response."
        )

    return answer.strip()


@app.get("/")
def root():
    return {
        "status": "ok",
        "server": "running",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL,
        "features": [
            "AI Tutor",
            "Smart Notes",
            "AI Quiz"
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    }


@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):
    try:
        prompt = f"""
You are a friendly AI study tutor.

Answer the student's question clearly and simply.
Use examples when helpful.
Explain step by step when needed.

Student question:
{request.question}
"""

        answer = ask_gemini(prompt)

        return {
            "answer": answer
        }

    except Exception as error:
        print("AI TUTOR ERROR:", str(error))

        return {
            "answer": "AI Tutor error: " + str(error)
        }


@app.post("/generate-notes")
def generate_notes(request: TopicRequest):
    try:
        prompt = f"""
Create clear and easy study notes for this topic:

{request.topic}

Include:
1. Introduction
2. Important concepts
3. Key points
4. Examples
5. Quick revision summary

Use simple student-friendly language.
"""

        notes = ask_gemini(prompt)

        return {
            "notes": notes
        }

    except Exception as error:
        print("SMART NOTES ERROR:", str(error))

        return {
            "notes": "Smart Notes error: " + str(error)
        }


@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):
    try:
        number = max(
            1,
            min(request.number_of_questions, 10)
        )

        prompt = f"""
Create exactly {number} multiple choice questions about:

{request.topic}

Return ONLY valid JSON in this exact format:

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
- Exactly 4 options per question.
- correctAnswer must be 0, 1, 2, or 3.
- Do not use Markdown.
- Return only JSON.
"""

        raw = ask_gemini(prompt)

        cleaned = raw.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())

        return data

    except Exception as error:
        print("AI QUIZ ERROR:", str(error))

        return {
            "questions": []
        }


@app.post("/ai-test")
def ai_test():
    try:
        answer = ask_gemini(
            "Say exactly: Study With Raman AI is working!"
        )

        return {
            "status": "ok",
            "answer": answer
        }

    except Exception as error:
        return {
            "status": "error",
            "error": str(error)
        }
````
