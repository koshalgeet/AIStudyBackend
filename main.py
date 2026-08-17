import os

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


class QuestionRequest(BaseModel):
    question: str


class TopicRequest(BaseModel):
    topic: str


class QuizRequest(BaseModel):
    topic: str
    number_of_questions: int = 5


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
        "model": "gemini-3.6-flash"
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
        model="gemini-3.6-flash",
        contents=prompt
    )

    answer = response.text

    if not answer:
        raise Exception(
            "Gemini returned an empty answer"
        )

    return answer


@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):

    try:

        prompt = f"""
You are Raman AI Tutor, a helpful and professional teacher.

Answer the student's question clearly and correctly.

Rules:
- Explain in simple language.
- If the student asks in Hindi or Hinglish, answer in Hindi or Hinglish.
- If the student asks in English, answer in English.
- Give examples when useful.
- Make the explanation easy for students.
- Answer directly without unnecessary information.

Student Question:

{request.question}
"""

        answer = ask_gemini(prompt)

        return {
            "answer": answer
        }

    except Exception as e:

        print("=" * 60)
        print("AI TUTOR ERROR")
        print(str(e))
        print("=" * 60)

        return {
            "answer": "AI Tutor Error: " + str(e)
        }


@app.post("/generate-notes")
def generate_notes(request: TopicRequest):

    try:

        prompt = f"""
Create easy and detailed study notes about:

{request.topic}

Include:

1. Introduction
2. Important concepts
3. Simple explanation
4. Examples
5. Key points
6. Short summary

Make the notes easy for students to understand.
"""

        answer = ask_gemini(prompt)

        return {
            "notes": answer
        }

    except Exception as e:

        return {
            "notes": "Error: " + str(e)
        }


@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    try:

        prompt = f"""
Create a quiz about:

Topic: {request.topic}

Number of questions: {request.number_of_questions}

For each question provide:

Question
A. Option
B. Option
C. Option
D. Option

Then clearly show:

Correct Answer: A/B/C/D

Make the quiz useful for students.
"""

        answer = ask_gemini(prompt)

        return {
            "quiz": answer
        }

    except Exception as e:

        return {
            "quiz": "Error: " + str(e)
        }


@app.post("/ai-test")
def ai_test(request: TopicRequest):

    try:

        prompt = f"""
Create a practice test about:

{request.topic}

Include:

1. Multiple choice questions
2. Short answer questions
3. Correct answers at the end

Make it suitable for students.
"""

        answer = ask_gemini(prompt)

        return {
            "test": answer
        }

    except Exception as e:

        return {
            "test": "Error: " + str(e)
        }
