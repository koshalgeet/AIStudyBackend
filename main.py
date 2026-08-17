import os
import json
import random
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Primary model
PRIMARY_MODEL = "gemini-3.6-flash"

# Backup model
BACKUP_MODEL = "gemini-2.5-flash"


# ============================================================
# FASTAPI
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
# GEMINI CLIENT
# ============================================================

client = None

if GEMINI_API_KEY:

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("==============================================")
        print("Gemini client initialized successfully.")
        print("==============================================")

    except Exception as e:

        print("Gemini client initialization error:")
        print(str(e))

        client = None

else:

    print("==============================================")
    print("WARNING: GEMINI_API_KEY NOT FOUND")
    print("==============================================")


# ============================================================
# REQUEST MODELS
# ============================================================

class AskAIRequest(BaseModel):
    question: str


class NotesRequest(BaseModel):
    topic: str


class QuizRequest(BaseModel):
    topic: str
    number_of_questions: int = 5


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "success",
        "message": "Study With Raman AI Backend is running",
        "gemini_configured": client is not None,
        "primary_model": PRIMARY_MODEL,
        "backup_model": BACKUP_MODEL
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "server": "running",
        "gemini_configured": client is not None,
        "primary_model": PRIMARY_MODEL,
        "backup_model": BACKUP_MODEL
    }


# ============================================================
# GEMINI GENERATOR
# ============================================================

def ask_gemini(prompt: str) -> str:

    if client is None:

        raise Exception(
            "GEMINI_API_KEY is not configured."
        )

    # --------------------------------------------------------
    # TRY PRIMARY MODEL
    # --------------------------------------------------------

    try:

        print(
            f"Trying Gemini model: {PRIMARY_MODEL}"
        )

        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if text and text.strip():

            print(
                f"Gemini primary model worked: {PRIMARY_MODEL}"
            )

            return text.strip()

        raise Exception(
            "Primary model returned empty response."
        )

    except Exception as primary_error:

        print("==============================================")
        print("PRIMARY GEMINI ERROR")
        print(str(primary_error))
        print("==============================================")


    # --------------------------------------------------------
    # TRY BACKUP MODEL
    # --------------------------------------------------------

    try:

        print(
            f"Trying backup Gemini model: {BACKUP_MODEL}"
        )

        response = client.models.generate_content(
            model=BACKUP_MODEL,
            contents=prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if text and text.strip():

            print(
                f"Gemini backup model worked: {BACKUP_MODEL}"
            )

            return text.strip()

        raise Exception(
            "Backup model returned empty response."
        )

    except Exception as backup_error:

        print("==============================================")
        print("BACKUP GEMINI ERROR")
        print(str(backup_error))
        print("==============================================")

        raise Exception(
            "Gemini API request failed. "
            f"Primary error: {primary_error} | "
            f"Backup error: {backup_error}"
        )


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: AskAIRequest):

    question = request.question.strip()

    if not question:

        return {
            "answer": "Please enter a question."
        }

    prompt = f"""
You are Study With Raman AI Tutor.

Answer the student's question clearly and correctly.

Student Question:
{question}

Rules:

1. Explain in simple language.
2. Use examples when useful.
3. For school or college questions,
   explain step by step.
4. Do not make the answer unnecessarily long.
5. If the student asks in Hindi or Hinglish,
   answer in Hindi/Hinglish.
6. If the student asks in English,
   answer in English.
7. Never say that you are unable to answer
   unless the question is genuinely impossible.
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "answer": answer,
            "source": "gemini"
        }

    except Exception as e:

        print("==============================================")
        print("AI TUTOR ERROR")
        print(str(e))
        print("==============================================")

        return {
            "answer": (
                "AI Tutor temporarily unavailable. "
                "Gemini API/model/quota problem detected."
            ),
            "source": "error",
            "error": str(e)
        }


# ============================================================
# SMART NOTES
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: NotesRequest):

    topic = request.topic.strip()

    if not topic:

        return {
            "notes": "Please enter a topic."
        }

    prompt = f"""
You are Study With Raman AI Notes Generator.

Create clear, useful and student-friendly
study notes about:

{topic}

Use this format:

1. Definition
2. Important Points
3. Detailed Explanation
4. Examples
5. Key Facts
6. Quick Revision

Rules:

- Keep language simple.
- Use headings.
- Use bullet points where useful.
- Make it easy for students to revise.
"""

    try:

        notes = ask_gemini(prompt)

        return {
            "notes": notes,
            "source": "gemini"
        }

    except Exception as e:

        print("==============================================")
        print("NOTES ERROR")
        print(str(e))
        print("==============================================")

        return {
            "notes": (
                "AI Notes temporarily unavailable."
            ),
            "source": "error",
            "error": str(e)
        }


# ============================================================
# FALLBACK QUIZ DATABASE
# ============================================================

FALLBACK_QUIZZES = {

    "science": [

        {
            "question": "Which planet is known as the Red Planet?",
            "options": [
                "Earth",
                "Mars",
                "Jupiter",
                "Venus"
            ],
            "correctAnswer": 1,
            "explanation":
                "Mars is called the Red Planet because "
                "of iron oxide on its surface."
        },

        {
            "question":
                "What gas do plants mainly use during photosynthesis?",
            "options": [
                "Oxygen",
                "Nitrogen",
                "Carbon dioxide",
                "Hydrogen"
            ],
            "correctAnswer": 2,
            "explanation":
                "Plants use carbon dioxide during photosynthesis."
        },

        {
            "question": "What is H2O commonly known as?",
            "options": [
                "Oxygen",
                "Water",
                "Hydrogen",
                "Salt"
            ],
            "correctAnswer": 1,
            "explanation":
                "H2O is the chemical formula for water."
        },

        {
            "question":
                "Which organ pumps blood around the human body?",
            "options": [
                "Brain",
                "Lungs",
                "Heart",
                "Kidney"
            ],
            "correctAnswer": 2,
            "explanation":
                "The heart pumps blood throughout the body."
        },

        {
            "question":
                "What force pulls objects toward Earth?",
            "options": [
                "Magnetism",
                "Gravity",
                "Friction",
                "Electricity"
            ],
            "correctAnswer": 1,
            "explanation":
                "Gravity attracts objects toward Earth."
        }
    ],


    "math": [

        {
            "question": "What is 12 × 5?",
            "options": [
                "50",
                "60",
                "70",
                "80"
            ],
            "correctAnswer": 1,
            "explanation":
                "12 multiplied by 5 equals 60."
        },

        {
            "question": "What is the square of 10?",
            "options": [
                "20",
                "50",
                "100",
                "1000"
            ],
            "correctAnswer": 2,
            "explanation":
                "10 × 10 = 100."
        },

        {
            "question": "What is 100 ÷ 4?",
            "options": [
                "20",
                "25",
                "30",
                "40"
            ],
            "correctAnswer": 1,
            "explanation":
                "100 divided by 4 equals 25."
        },

        {
            "question": "What is 15 + 27?",
            "options": [
                "32",
                "42",
                "52",
                "62"
            ],
            "correctAnswer": 1,
            "explanation":
                "15 + 27 = 42."
        },

        {
            "question": "What is 9 × 9?",
            "options": [
                "72",
                "81",
                "91",
                "99"
            ],
            "correctAnswer": 1,
            "explanation":
                "9 × 9 = 81."
        }
    ],


    "history": [

        {
            "question":
                "Who was known as the Father of the Indian Constitution?",
            "options": [
                "Mahatma Gandhi",
                "Dr. B. R. Ambedkar",
                "Jawaharlal Nehru",
                "Sardar Patel"
            ],
            "correctAnswer": 1,
            "explanation":
                "Dr. B. R. Ambedkar played a leading role "
                "in drafting the Indian Constitution."
        },

        {
            "question":
                "Who was the first Prime Minister of independent India?",
            "options": [
                "Sardar Patel",
                "Jawaharlal Nehru",
                "Rajendra Prasad",
                "Subhas Chandra Bose"
            ],
            "correctAnswer": 1,
            "explanation":
                "Jawaharlal Nehru became India's first Prime Minister."
        },

        {
            "question":
                "India became independent in which year?",
            "options": [
                "1945",
                "1946",
                "1947",
                "1950"
            ],
            "correctAnswer": 2,
            "explanation":
                "India became independent on 15 August 1947."
        },

        {
            "question":
                "Who is popularly known as the Mahatma?",
            "options": [
                "Mahatma Gandhi",
                "Bhagat Singh",
                "A. P. J. Abdul Kalam",
                "Swami Vivekananda"
            ],
            "correctAnswer": 0,
            "explanation":
                "Mahatma Gandhi is popularly known as Mahatma."
        },

        {
            "question":
                "The Constitution of India came into effect in which year?",
            "options": [
                "1947",
                "1948",
                "1950",
                "1952"
            ],
            "correctAnswer": 2,
            "explanation":
                "The Constitution came into effect on "
                "26 January 1950."
        }
    ],


    "english": [

        {
            "question":
                "What is the opposite of 'hot'?",
            "options": [
                "Warm",
                "Cold",
                "Heat",
                "Fire"
            ],
            "correctAnswer": 1,
            "explanation":
                "The opposite of hot is cold."
        },

        {
            "question":
                "Which word is a noun?",
            "options": [
                "Run",
                "Beautiful",
                "School",
                "Quickly"
            ],
            "correctAnswer": 2,
            "explanation":
                "School is a noun because it names a place."
        },

        {
            "question":
                "What is the past tense of 'go'?",
            "options": [
                "Goed",
                "Gone",
                "Went",
                "Going"
            ],
            "correctAnswer": 2,
            "explanation":
                "The past tense of go is went."
        },

        {
            "question":
                "Which word is an adjective?",
            "options": [
                "Beautiful",
                "Run",
                "School",
                "Quickly"
            ],
            "correctAnswer": 0,
            "explanation":
                "Beautiful is an adjective."
        },

        {
            "question":
                "Choose the correct article: ___ apple",
            "options": [
                "A",
                "An",
                "The",
                "No article"
            ],
            "correctAnswer": 1,
            "explanation":
                "We use 'an' before a vowel sound."
        }
    ],


    "computer": [

        {
            "question":
                "What does CPU stand for?",
            "options": [
                "Central Processing Unit",
                "Computer Personal Unit",
                "Central Program Utility",
                "Control Processing User"
            ],
            "correctAnswer": 0,
            "explanation":
                "CPU stands for Central Processing Unit."
        },

        {
            "question":
                "Which device is used to type text?",
            "options": [
                "Monitor",
                "Keyboard",
                "Speaker",
                "Printer"
            ],
            "correctAnswer": 1,
            "explanation":
                "A keyboard is used to type text."
        },

        {
            "question":
                "What does RAM stand for?",
            "options": [
                "Random Access Memory",
                "Read Access Machine",
                "Rapid Application Memory",
                "Random Application Module"
            ],
            "correctAnswer": 0,
            "explanation":
                "RAM stands for Random Access Memory."
        },

        {
            "question":
                "Which is an operating system?",
            "options": [
                "Android",
                "Google",
                "YouTube",
                "Chrome"
            ],
            "correctAnswer": 0,
            "explanation":
                "Android is an operating system."
        },

        {
            "question":
                "Which language is commonly used for Android development?",
            "options": [
                "Kotlin",
                "HTML only",
                "SQL only",
                "CSS"
            ],
            "correctAnswer": 0,
            "explanation":
                "Kotlin is commonly used for Android development."
        }
    ]
}


# ============================================================
# FALLBACK QUIZ CREATOR
# ============================================================

def create_fallback_quiz(
    topic: str,
    number_of_questions: int
):

    topic_lower = topic.lower()

    selected_key = "science"

    if (
        "math" in topic_lower
        or "mathematics" in topic_lower
        or "algebra" in topic_lower
    ):

        selected_key = "math"

    elif (
        "history" in topic_lower
        or "india" in topic_lower
        or "gandhi" in topic_lower
    ):

        selected_key = "history"

    elif (
        "english" in topic_lower
        or "grammar" in topic_lower
        or "vocabulary" in topic_lower
    ):

        selected_key = "english"

    elif (
        "computer" in topic_lower
        or "coding" in topic_lower
        or "programming" in topic_lower
        or "android" in topic_lower
    ):

        selected_key = "computer"

    elif (
        "science" in topic_lower
        or "physics" in topic_lower
        or "chemistry" in topic_lower
        or "biology" in topic_lower
    ):

        selected_key = "science"

    source = FALLBACK_QUIZZES[selected_key]

    questions = source.copy()

    random.shuffle(questions)

    count = min(
        max(number_of_questions, 1),
        len(questions)
    )

    return questions[:count]


# ============================================================
# AI QUIZ GENERATOR
# ============================================================

def generate_ai_quiz(
    topic: str,
    number_of_questions: int
):

    prompt = f"""
Create a multiple-choice quiz for students.

Topic:
{topic}

Number of questions:
{number_of_questions}

Return ONLY valid JSON.

Required format:

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
- Questions must be factually correct.
- Make questions suitable for students.
- No markdown.
- No text outside JSON.
"""

    text = ask_gemini(prompt)

    text = text.strip()

    # Remove markdown fences
    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    data = json.loads(text)

    questions = data.get(
        "questions",
        []
    )

    clean_questions = []

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
            question
            and isinstance(options, list)
            and len(options) == 4
            and isinstance(correct_answer, int)
            and 0 <= correct_answer <= 3
        ):

            clean_questions.append(
                {
                    "question": question,
                    "options": options,
                    "correctAnswer": correct_answer,
                    "explanation": explanation
                }
            )

    if not clean_questions:

        raise Exception(
            "AI did not return valid quiz questions."
        )

    return clean_questions[
        :number_of_questions
    ]


# ============================================================
# QUIZ ENDPOINT
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(
    request: QuizRequest
):

    topic = request.topic.strip()

    number = request.number_of_questions

    if not topic:

        return {
            "questions": [],
            "source": "error",
            "message":
                "Please enter a quiz topic."
        }

    if number < 1:
        number = 5

    if number > 20:
        number = 20

    # --------------------------------------------------------
    # TRY GEMINI
    # --------------------------------------------------------

    try:

        questions = generate_ai_quiz(
            topic,
            number
        )

        print(
            f"AI Quiz generated: {topic}"
        )

        return {
            "questions": questions,
            "source": "gemini",
            "message":
                "AI quiz generated successfully."
        }

    except Exception as e:

        print("==============================================")
        print("QUIZ GEMINI ERROR")
        print(str(e))
        print("==============================================")

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        fallback_questions = create_fallback_quiz(
            topic,
            number
        )

        return {
            "questions": fallback_questions,
            "source": "fallback",
            "message":
                "Gemini unavailable. Fallback quiz returned.",
            "error": str(e)
        }


# ============================================================
# TEST GEMINI
# ============================================================

@app.get("/test-ai")
def test_ai():

    try:

        answer = ask_gemini(
            "Reply with exactly: Study With Raman AI is working."
        )

        return {
            "status": "success",
            "answer": answer
        }

    except Exception as e:

        print("TEST AI ERROR:")
        print(str(e))

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# STARTUP MESSAGE
# ============================================================

print("")
print("==============================================")
print("       STUDY WITH RAMAN AI BACKEND")
print("==============================================")
print(f"Primary model : {PRIMARY_MODEL}")
print(f"Backup model  : {BACKUP_MODEL}")
print(f"Gemini ready  : {client is not None}")
print("Server ready")
print("==============================================")
print("")
