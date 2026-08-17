# main.py

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
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Current Gemini Interactions API model

GEMINI_MODEL = "gemini-3.6-flash"

class QuestionRequest(BaseModel):
question: str

class TopicRequest(BaseModel):
topic: str

class QuizRequest(BaseModel):
topic: str
number_of_questions: int = 5

@app.get("/")
def root():
return {
"message": "Study With Raman AI Backend is running",
"model": GEMINI_MODEL
}

@app.get("/health")
def health():
return {
"status": "healthy",
"model": GEMINI_MODEL,
"gemini_api_key_found": bool(GEMINI_API_KEY)
}

def get_ai_answer(prompt: str):

```
if not GEMINI_API_KEY:
    raise Exception(
        "GEMINI_API_KEY is not configured in Render Environment Variables."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)

interaction = client.interactions.create(
    model=GEMINI_MODEL,
    input=prompt
)

answer = interaction.output_text

if not answer:
    raise Exception("Gemini returned an empty response.")

return answer
```

@app.post("/ask-ai")
def ask_ai(request: QuestionRequest):

```
try:
    prompt = f"""
```

You are Raman AI Tutor, a helpful professional teacher.

Answer the student's question clearly and correctly.

Instructions:

* Explain in simple language.
* If the question is in Hindi or Hinglish, answer in Hindi/Hinglish.
* If the question is in English, answer in English.
* Give examples when helpful.
* Make the answer easy for students to understand.
* Do not say that you are unavailable unless there is a real error.

Student Question:
{request.question}
"""

```
    answer = get_ai_answer(prompt)

    return {
        "answer": answer
    }

except Exception as e:

    print("=" * 60)
    print("AI TUTOR ERROR")
    print(str(e))
    print("=" * 60)

    return {
        "answer": f"AI Tutor Error: {str(e)}"
    }
```

@app.post("/generate-notes")
def generate_notes(request: TopicRequest):

```
try:

    prompt = f"""
```

You are a professional teacher.

Create easy and detailed study notes about:

{request.topic}

Include:

1. Introduction
2. Important concepts
3. Simple explanation
4. Examples
5. Key points
6. Short summary

Make the notes easy for students.
"""

```
    answer = get_ai_answer(prompt)

    return {
        "notes": answer
    }

except Exception as e:

    return {
        "notes": f"Error: {str(e)}"
    }
```

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

```
try:

    prompt = f"""
```

Create a student quiz about:

Topic: {request.topic}

Number of questions: {request.number_of_questions}

For every question provide:

Question
A. Option
B. Option
C. Option
D. Option

Then provide the correct answer.

Make the quiz educational and easy to understand.
"""

```
    answer = get_ai_answer(prompt)

    return {
        "quiz": answer
    }

except Exception as e:

    return {
        "quiz": f"Error: {str(e)}"
    }
```

@app.post("/ai-test")
def ai_test(request: TopicRequest):

```
try:

    prompt = f"""
```

Create a practice test about:

{request.topic}

Include multiple choice questions and short answer questions.

At the end provide correct answers.

Make it useful for students.
"""

```
    answer = get_ai_answer(prompt)

    return {
        "test": answer
    }

except Exception as e:

    return {
        "test": f"Error: {str(e)}"
    }
```
