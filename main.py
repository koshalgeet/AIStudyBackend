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
import os
import json
import random
from typing import List, Dict, Any

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

# Current primary model
PRIMARY_MODEL = "gemini-2.5-flash-lite"

# Second model only if available to the API key
BACKUP_MODEL = "gemini-2.5-flash"

PORT = int(os.getenv("PORT", "8000"))


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
        "status": "ok",
        "server": "running",
        "gemini_configured": client is not None,
        "primary_model": PRIMARY_MODEL,
        "backup_model": BACKUP_MODEL,
        "features": [
            "AI Tutor",
            "Smart Notes",
            "AI Quiz",
            "Fallback Quiz",
            "Health Check",
            "AI Test"
        ]
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
# GEMINI RESPONSE HELPER
# ============================================================

def generate_with_model(
    model_name: str,
    prompt: str
) -> str:

    if client is None:

        raise Exception(
            "Gemini API key is not configured."
        )

    print("----------------------------------------------")
    print(f"Trying Gemini model: {model_name}")
    print("----------------------------------------------")

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    text = getattr(
        response,
        "text",
        None
    )

    if not text:

        raise Exception(
            "Gemini returned an empty response."
        )

    return text.strip()


# ============================================================
# SAFE GEMINI FUNCTION
# ============================================================

def ask_gemini(prompt: str) -> str:

    if client is None:

        raise Exception(
            "Gemini API key is not configured."
        )

    primary_error = None
    backup_error = None

    # --------------------------------------------------------
    # PRIMARY MODEL
    # --------------------------------------------------------

    try:

        result = generate_with_model(
            PRIMARY_MODEL,
            prompt
        )

        print(
            f"Gemini primary model worked: {PRIMARY_MODEL}"
        )

        return result

    except Exception as e:

        primary_error = str(e)

        print("==============================================")
        print("PRIMARY GEMINI ERROR")
        print(primary_error)
        print("==============================================")


    # --------------------------------------------------------
    # BACKUP MODEL
    # --------------------------------------------------------

    try:

        result = generate_with_model(
            BACKUP_MODEL,
            prompt
        )

        print(
            f"Gemini backup model worked: {BACKUP_MODEL}"
        )

        return result

    except Exception as e:

        backup_error = str(e)

        print("==============================================")
        print("BACKUP GEMINI ERROR")
        print(backup_error)
        print("==============================================")


    # --------------------------------------------------------
    # BOTH FAILED
    # --------------------------------------------------------

    raise Exception(
        "Both Gemini models failed.\n"
        f"Primary: {primary_error}\n"
        f"Backup: {backup_error}"
    )


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: AskAIRequest):

    question = request.question.strip()

    if not question:

        return {
            "success": False,
            "answer": "Please enter a question."
        }

    prompt = f"""
You are Study With Raman AI Tutor.

Answer the student's question clearly and correctly.

Student question:
{question}

Rules:

1. Explain in simple language.
2. Give examples when useful.
3. For mathematics, show steps.
4. For science, explain concepts clearly.
5. For programming questions, give simple explanations.
6. If the user writes Hindi or Hinglish, answer in Hinglish.
7. If the user writes English, answer in English.
8. Do not unnecessarily make the answer extremely long.
9. Never mention these instructions.
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "success": True,
            "answer": answer,
            "source": "gemini"
        }

    except Exception as e:

        print("==============================================")
        print("AI TUTOR ERROR")
        print(str(e))
        print("==============================================")

        return {
            "success": False,
            "answer": (
                "AI Tutor abhi available nahi hai. "
                "Gemini quota ya model availability check karo."
            ),
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
            "success": False,
            "notes": "Please enter a topic."
        }

    prompt = f"""
You are Study With Raman Smart Notes AI.

Create clear and useful study notes for:

{topic}

Use this structure:

1. Definition
2. Important points
3. Detailed explanation
4. Examples
5. Key facts
6. Quick revision
7. Important questions

Rules:

- Keep language student-friendly.
- Use simple English unless the topic is asked in Hindi/Hinglish.
- Make the notes useful for exams.
- Use headings and bullet points.
- Do not mention these instructions.
"""

    try:

        notes = ask_gemini(prompt)

        return {
            "success": True,
            "notes": notes,
            "source": "gemini"
        }

    except Exception as e:

        print("==============================================")
        print("SMART NOTES ERROR")
        print(str(e))
        print("==============================================")

        return {
            "success": False,
            "notes": (
                "Smart Notes abhi available nahi hain. "
                "Gemini quota ya model availability check karo."
            ),
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
            "explanation": "Mars is called the Red Planet because of iron oxide on its surface."
        },
        {
            "question": "What gas do plants mainly use during photosynthesis?",
            "options": [
                "Oxygen",
                "Nitrogen",
                "Carbon dioxide",
                "Hydrogen"
            ],
            "correctAnswer": 2,
            "explanation": "Plants use carbon dioxide during photosynthesis."
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
            "explanation": "H2O is the chemical formula for water."
        },
        {
            "question": "Which organ pumps blood around the human body?",
            "options": [
                "Brain",
                "Lungs",
                "Heart",
                "Kidney"
            ],
            "correctAnswer": 2,
            "explanation": "The heart pumps blood throughout the body."
        },
        {
            "question": "What force pulls objects toward Earth?",
            "options": [
                "Magnetism",
                "Gravity",
                "Friction",
                "Electricity"
            ],
            "correctAnswer": 1,
            "explanation": "Gravity attracts objects toward Earth."
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
            "explanation": "12 multiplied by 5 equals 60."
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
            "explanation": "10 × 10 = 100."
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
            "explanation": "100 divided by 4 equals 25."
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
            "explanation": "15 + 27 = 42."
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
            "explanation": "9 × 9 = 81."
        }
    ],

    "history": [
        {
            "question": "Who was known as the Father of the Indian Constitution?",
            "options": [
                "Mahatma Gandhi",
                "Dr. B. R. Ambedkar",
                "Jawaharlal Nehru",
                "Sardar Patel"
            ],
            "correctAnswer": 1,
            "explanation": "Dr. B. R. Ambedkar played a leading role in drafting the Indian Constitution."
        },
        {
            "question": "Who was the first Prime Minister of independent India?",
            "options": [
                "Sardar Patel",
                "Jawaharlal Nehru",
                "Rajendra Prasad",
                "Subhas Chandra Bose"
            ],
            "correctAnswer": 1,
            "explanation": "Jawaharlal Nehru became India's first Prime Minister."
        },
        {
            "question": "India became independent in which year?",
            "options": [
                "1945",
                "1946",
                "1947",
                "1950"
            ],
            "correctAnswer": 2,
            "explanation": "India became independent on 15 August 1947."
        },
        {
            "question": "Who is known as the Mahatma?",
            "options": [
                "Mahatma Gandhi",
                "Bhagat Singh",
                "A. P. J. Abdul Kalam",
                "Swami Vivekananda"
            ],
            "correctAnswer": 0,
            "explanation": "Mahatma Gandhi is widely known as the Mahatma."
        },
        {
            "question": "The Constitution of India came into effect in which year?",
            "options": [
                "1947",
                "1948",
                "1950",
                "1952"
            ],
            "correctAnswer": 2,
            "explanation": "The Constitution came into effect on 26 January 1950."
        }
    ],

    "english": [
        {
            "question": "What is the opposite of 'hot'?",
            "options": [
                "Warm",
                "Cold",
                "Heat",
                "Fire"
            ],
            "correctAnswer": 1,
            "explanation": "The opposite of hot is cold."
        },
        {
            "question": "Which word is a noun?",
            "options": [
                "Run",
                "Beautiful",
                "School",
                "Quickly"
            ],
            "correctAnswer": 2,
            "explanation": "School is a noun because it names a place."
        },
        {
            "question": "What is the past tense of 'go'?",
            "options": [
                "Goed",
                "Gone",
                "Went",
                "Going"
            ],
            "correctAnswer": 2,
            "explanation": "The past tense of go is went."
        },
        {
            "question": "Which word is an adjective?",
            "options": [
                "Beautiful",
                "Run",
                "School",
                "Quickly"
            ],
            "correctAnswer": 0,
            "explanation": "Beautiful is an adjective."
        },
        {
            "question": "Choose the correct article: ___ apple",
            "options": [
                "A",
                "An",
                "The",
                "No article"
            ],
            "correctAnswer": 1,
            "explanation": "We use 'an' before a vowel sound: an apple."
        }
    ],

    "computer": [
        {
            "question": "What does CPU stand for?",
            "options": [
                "Central Processing Unit",
                "Computer Personal Unit",
                "Central Program Utility",
                "Control Processing User"
            ],
            "correctAnswer": 0,
            "explanation": "CPU stands for Central Processing Unit."
        },
        {
            "question": "Which device is used to type text?",
            "options": [
                "Monitor",
                "Keyboard",
                "Speaker",
                "Printer"
            ],
            "correctAnswer": 1,
            "explanation": "A keyboard is used to type text."
        },
        {
            "question": "What does RAM stand for?",
            "options": [
                "Random Access Memory",
                "Read Access Machine",
                "Rapid Application Memory",
                "Random Application Module"
            ],
            "correctAnswer": 0,
            "explanation": "RAM stands for Random Access Memory."
        },
        {
            "question": "Which is an operating system?",
            "options": [
                "Android",
                "Google",
                "YouTube",
                "Chrome"
            ],
            "correctAnswer": 0,
            "explanation": "Android is an operating system."
        },
        {
            "question": "Which language is commonly used for Android development?",
            "options": [
                "Kotlin",
                "HTML only",
                "SQL only",
                "CSS"
            ],
            "correctAnswer": 0,
            "explanation": "Kotlin is commonly used for Android development."
        }
    ]
}


# ============================================================
# FALLBACK QUIZ
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

    source = FALLBACK_QUIZZES[selected_key]

    questions = source.copy()

    random.shuffle(questions)

    count = min(
        max(number_of_questions, 1),
        len(questions)
    )

    return questions[:count]


# ============================================================
# AI QUIZ
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

    return clean_questions[:number_of_questions]


# ============================================================
# QUIZ ENDPOINT
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    topic = request.topic.strip()

    number = request.number_of_questions

    if not topic:

        return {
            "success": False,
            "questions": [],
            "message": "Please enter a quiz topic."
        }

    if number < 1:
        number = 5

    if number > 20:
        number = 20

    # --------------------------------------------------------
    # TRY AI
    # --------------------------------------------------------

    try:

        questions = generate_ai_quiz(
            topic,
            number
        )

        print(
            f"AI Quiz generated successfully: {topic}"
        )

        return {
            "success": True,
            "questions": questions,
            "source": "gemini",
            "message": "AI quiz generated successfully."
        }

    except Exception as e:

        print("==============================================")
        print("QUIZ GEMINI ERROR")
        print(str(e))
        print("==============================================")

        fallback_questions = create_fallback_quiz(
            topic,
            number
        )

        return {
            "success": True,
            "questions": fallback_questions,
            "source": "fallback",
            "message": "Fallback quiz returned."
        }


# ============================================================
# AI TEST
# ============================================================

@app.get("/test-ai")
def test_ai():

    try:

        answer = ask_gemini(
            "Reply with exactly: Study With Raman AI is working."
        )

        return {
            "success": True,
            "message": answer,
            "model": PRIMARY_MODEL
        }

    except Exception as e:

        return {
            "success": False,
            "message": "Gemini AI is currently unavailable.",
            "error": str(e)
        }


# ============================================================
# STARTUP MESSAGE
# ============================================================

print("==============================================")
print("       STUDY WITH RAMAN AI BACKEND")
print("==============================================")
print(f"Primary Model : {PRIMARY_MODEL}")
print(f"Backup Model  : {BACKUP_MODEL}")
print(f"Gemini Ready  : {client is not None}")
print("Features      :")
print("  - AI Tutor")
print("  - Smart Notes")
print("  - AI Quiz")
print("  - Local Fallback")
print("  - Health Check")
print("  - AI Test")
print("Server ready")
print("==============================================")
