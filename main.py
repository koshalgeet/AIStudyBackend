import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    number_of_questions: int = 5


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
# GEMINI FUNCTION
# ============================================================

def ask_gemini(prompt: str):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise Exception(
            "GEMINI_API_KEY is missing in Render Environment Variables"
        )

    client = genai.Client(
        api_key=api_key
    )

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


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):

    try:

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

{request.question}
"""

        answer = ask_gemini(prompt)

        return {
            "answer": answer
        }

    except Exception as e:

        print("AI TUTOR ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# SMART NOTES
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: TopicRequest):

    try:

        prompt = f"""
Create simple and useful study notes about:

{request.topic}

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

    except Exception as e:

        print("NOTES ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# AI QUIZ
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    try:

        prompt = f"""
Create exactly {request.number_of_questions} multiple choice quiz questions.

Topic: {request.topic}

IMPORTANT:

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
- 0 means first option.
- 1 means second option.
- 2 means third option.
- 3 means fourth option.
- explanation should be short.
- Return JSON only.
"""

        answer = ask_gemini(prompt)

        # Remove markdown if Gemini still sends it
        cleaned = answer.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Find JSON object safely
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1:
            raise Exception(
                "Gemini did not return valid JSON"
            )

        cleaned = cleaned[start:end + 1]

        data = json.loads(cleaned)

        questions = data.get("questions", [])

        if not isinstance(questions, list):
            raise Exception(
                "Invalid questions format"
            )

        valid_questions = []

        for item in questions:

            question = item.get("question", "")
            options = item.get("options", [])
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
                and correct_answer >= 0
                and correct_answer <= 3
            ):

                valid_questions.append(
                    {
                        "question": question,
                        "options": options,
                        "correctAnswer": correct_answer,
                        "explanation": explanation
                    }
                )

        if len(valid_questions) == 0:
            raise Exception(
                "No valid quiz questions generated"
            )

        return {
            "questions": valid_questions
        }

    except Exception as e:

        print("QUIZ ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# AI PRACTICE TEST
# ============================================================

@app.post("/ai-test")
def ai_test(request: TopicRequest):

    try:

        prompt = f"""
Create a practice test about:

{request.topic}

Include:

1. Multiple choice questions
2. Short answer questions
3. Correct answers

Use simple language.
"""

        answer = ask_gemini(prompt)

        return {
            "test": answer
        }

    except Exception as e:

        print("TEST ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
