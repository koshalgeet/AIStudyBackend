````python
import os
import json
import traceback
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Study With Raman AI Backend",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Current stable Gemini model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)

client: Optional[genai.Client] = None


if GEMINI_API_KEY:
    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("==============================================")
        print("GEMINI CLIENT INITIALIZED")
        print("Model:", GEMINI_MODEL)
        print("==============================================")

    except Exception as e:
        print("==============================================")
        print("GEMINI CLIENT INITIALIZATION ERROR")
        print(str(e))
        print("==============================================")

else:
    print("==============================================")
    print("WARNING: GEMINI_API_KEY NOT FOUND")
    print("==============================================")


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
# GEMINI HELPER
# ============================================================

def ask_gemini(prompt: str) -> str:

    if client is None:
        raise Exception(
            "GEMINI_API_KEY is not configured on Render."
        )

    if not prompt.strip():
        raise Exception(
            "Empty prompt received."
        )

    print("----------------------------------------------")
    print("Trying Gemini model:", GEMINI_MODEL)
    print("----------------------------------------------")

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if text is None:
            text = ""

        text = text.strip()

        if not text:
            raise Exception(
                "Gemini returned an empty response."
            )

        print("----------------------------------------------")
        print("GEMINI SUCCESS")
        print("----------------------------------------------")

        return text

    except Exception as e:

        print("==============================================")
        print("GEMINI ERROR")
        print(type(e).__name__)
        print(str(e))
        print("==============================================")

        raise


# ============================================================
# ROOT / HEALTH
# ============================================================

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
            "AI Quiz",
            "Fallback Quiz",
            "Health Check",
            "AI Test"
        ]
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    }


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):

    question = request.question.strip()

    if not question:
        return {
            "answer": "Please enter a study question."
        }

    prompt = f"""
You are Study With Raman, a friendly AI study tutor.

Answer the student's question clearly and accurately.

Rules:
- Explain in simple language.
- If the question is academic, teach step-by-step.
- Use examples when useful.
- Do not make the answer unnecessarily complicated.
- If a formula is needed, show the formula clearly.
- If the student asks a general question, answer naturally.
- Keep the answer useful for a student.

Student question:
{question}
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "answer": answer
        }

    except Exception as e:

        print("==============================================")
        print("AI TUTOR ERROR")
        print(str(e))
        print("==============================================")

        return {
            "answer": (
                "AI Tutor is temporarily unavailable. "
                "Please try again in a moment."
            )
        }


# ============================================================
# SMART NOTES
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: TopicRequest):

    topic = request.topic.strip()

    if not topic:
        return {
            "notes": "Please enter a topic."
        }

    prompt = f"""
You are an AI study-notes generator for Study With Raman.

Create clear, student-friendly notes about:

{topic}

Use this structure:

1. Topic Overview
2. Important Definitions
3. Main Concepts
4. Key Points
5. Examples
6. Important Formulas or Facts
7. Quick Revision

Rules:
- Use simple language.
- Make the notes easy to revise.
- Use headings and bullet points.
- Do not add unnecessary information.
- Make the notes educational and accurate.
"""

    try:

        notes = ask_gemini(prompt)

        return {
            "notes": notes
        }

    except Exception as e:

        print("==============================================")
        print("SMART NOTES ERROR")
        print(str(e))
        print("==============================================")

        return {
            "notes": (
                "Smart Notes is temporarily unavailable. "
                "Please try again in a moment."
            )
        }


# ============================================================
# AI QUIZ
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    topic = request.topic.strip()

    if not topic:
        return {
            "questions": []
        }

    number = request.number_of_questions

    if number < 1:
        number = 5

    if number > 10:
        number = 10

    prompt = f"""
You are an AI quiz generator for Study With Raman.

Create exactly {number} multiple-choice questions about:

{topic}

Every question must have exactly 4 options.

Return ONLY valid JSON.

The JSON must have exactly this structure:

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

Important:
- correctAnswer must be an integer from 0 to 3.
- 0 means first option.
- 1 means second option.
- 2 means third option.
- 3 means fourth option.
- Do not use Markdown.
- Do not put ```json around the response.
- Make questions educational.
- Make sure the correct answer is actually correct.
"""

    try:

        raw = ask_gemini(prompt)

        # ----------------------------------------------------
        # Clean possible markdown wrapping
        # ----------------------------------------------------

        cleaned = raw.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        data = json.loads(cleaned)

        questions = data.get(
            "questions",
            []
        )

        valid_questions = []

        for item in questions:

            if not isinstance(item, dict):
                continue

            question = str(
                item.get("question", "")
            ).strip()

            options = item.get(
                "options",
                []
            )

            correct_answer = item.get(
                "correctAnswer",
                0
            )

            explanation = str(
                item.get("explanation", "")
            ).strip()

            if not isinstance(options, list):
                continue

            options = [
                str(option).strip()
                for option in options
            ]

            if len(options) != 4:
                continue

            try:
                correct_answer = int(
                    correct_answer
                )
            except Exception:
                correct_answer = 0

            if correct_answer < 0 or correct_answer > 3:
                correct_answer = 0

            if not question:
                continue

            valid_questions.append(
                {
                    "question": question,
                    "options": options,
                    "correctAnswer": correct_answer,
                    "explanation": explanation
                }
            )

        if not valid_questions:

            raise Exception(
                "Gemini returned no valid quiz questions."
            )

        return {
            "questions": valid_questions
        }

    except Exception as e:

        print("==============================================")
        print("AI QUIZ ERROR")
        print(str(e))
        print("==============================================")

        # ----------------------------------------------------
        # Fallback quiz
        # ----------------------------------------------------

        fallback_questions = [
            {
                "question": f"What is the main subject of {topic}?",
                "options": [
                    f"Understanding {topic}",
                    "Cooking",
                    "Driving",
                    "Dancing"
                ],
                "correctAnswer": 0,
                "explanation": (
                    f"The quiz topic is {topic}, "
                    f"so understanding {topic} is the relevant answer."
                )
            },
            {
                "question": f"Why should students study {topic}?",
                "options": [
                    "To understand the subject better",
                    "To avoid learning",
                    "To waste time",
                    "None of these"
                ],
                "correctAnswer": 0,
                "explanation": (
                    "Studying helps students understand "
                    "and remember the subject."
                )
            }
        ]

        return {
            "questions": fallback_questions
        }


# ============================================================
# AI TEST
# ============================================================

@app.post("/ai-test")
def ai_test():

    try:

        answer = ask_gemini(
            "Reply with exactly: Study With Raman AI is working!"
        )

        return {
            "status": "ok",
            "answer": answer,
            "model": GEMINI_MODEL
        }

    except Exception as e:

        return {
            "status": "error",
            "error": str(e),
            "model": GEMINI_MODEL
        }


# ============================================================
# SERVER START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
````
