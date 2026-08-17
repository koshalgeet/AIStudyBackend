import os
import json

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
    number_of_questions: int = 5


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
        "model": "gemini-3.6-flash"
    }


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(prompt: str):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise Exception(
            "GEMINI_API_KEY is missing"
        )

    client = genai.Client(
        api_key=api_key
    )

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    answer = response.text

    if not answer:
        raise Exception(
            "Gemini returned an empty answer"
        )

    return answer


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):

    try:

        prompt = f"""
You are Raman AI Tutor.

Answer the student's question clearly.

Rules:
- Give a short and direct answer by default.
- Use simple language.
- If the question is in Hindi or Hinglish, answer in Hindi or Hinglish.
- If the question is in English, answer in English.
- Give an example only when useful.
- Do not add unnecessary information.

Student Question:
{request.question}
"""

        answer = ask_gemini(prompt)

        return {
            "answer": answer
        }

    except Exception as e:

        print("AI TUTOR ERROR:", str(e))

        return {
            "answer": "AI Tutor Error: " + str(e)
        }


# ============================================================
# SMART NOTES
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: TopicRequest):

    try:

        prompt = f"""
Create clear and easy study notes about:

{request.topic}

Include:

1. Introduction
2. Important concepts
3. Simple explanation
4. Examples where useful
5. Key points
6. Short summary

Use simple language suitable for students.
"""

        answer = ask_gemini(prompt)

        return {
            "notes": answer
        }

    except Exception as e:

        print("NOTES ERROR:", str(e))

        return {
            "notes": "Error: " + str(e)
        }


# ============================================================
# AI QUIZ
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    try:

        prompt = f"""
Create exactly {request.number_of_questions} multiple-choice
quiz questions about:

{request.topic}

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not write any explanation outside the JSON.

Use exactly this format:

{{
  "questions": [
    {{
      "question": "Question text here",
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

- Every question must have exactly 4 options.
- correctAnswer must be a number from 0 to 3.
- 0 means first option is correct.
- 1 means second option is correct.
- 2 means third option is correct.
- 3 means fourth option is correct.
- Return exactly {request.number_of_questions} questions.
- Return only JSON.
"""

        answer = ask_gemini(prompt)

        # Remove accidental markdown formatting
        answer = answer.strip()

        if answer.startswith("```json"):
            answer = answer.replace(
                "```json",
                "",
                1
            )

        if answer.startswith("```"):
            answer = answer.replace(
                "```",
                "",
                1
            )

        if answer.endswith("```"):
            answer = answer[:-3]

        answer = answer.strip()

        # Convert Gemini JSON text into real JSON
        quiz_data = json.loads(answer)

        if "questions" not in quiz_data:
            raise Exception(
                "Questions key missing from Gemini response"
            )

        if not isinstance(
            quiz_data["questions"],
            list
        ):
            raise Exception(
                "Questions is not a list"
            )

        return quiz_data

    except Exception as e:

        print("QUIZ ERROR:", str(e))

        return {
            "questions": [],
            "error": str(e)
        }


# ============================================================
# PRACTICE TEST
# ============================================================

@app.post("/ai-test")
def ai_test(request: TopicRequest):

    try:

        prompt = f"""
Create a useful practice test about:

{request.topic}

Include:

1. Multiple choice questions
2. Short answer questions
3. Correct answers at the end

Use simple language for students.
"""

        answer = ask_gemini(prompt)

        return {
            "test": answer
        }

    except Exception as e:

        print("PRACTICE TEST ERROR:", str(e))

        return {
            "test": "Error: " + str(e)
        }
