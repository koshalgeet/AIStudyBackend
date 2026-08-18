# main.py

````python
import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai


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


class QuestionRequest(BaseModel):
    question: str


class TopicRequest(BaseModel):
    topic: str


class QuizRequest(BaseModel):
    topic: str
    number_of_questions: int = 5


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


@app.get("/")
def home():
    return {
        "message": "Study With Raman AI Backend is running"
    }


@app.get("/health")
def health():
    api_key = os.getenv("GEMINI_API_KEY")

    return {
        "status": "healthy",
        "api_key_found": bool(api_key),
        "model": GEMINI_MODEL
    }


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
- Give examples only when useful.

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


@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    try:

        prompt = f"""
Create exactly {request.number_of_questions} multiple choice quiz questions.

Topic: {request.topic}

Return ONLY valid JSON.

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
- Return JSON only.
"""

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
            raise Exception(
                "Gemini did not return valid JSON"
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
                        "question": question,
                        "options": options,
                        "correctAnswer": correct_answer,
                        "explanation": explanation
                    }
                )

        if not valid_questions:
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
````
