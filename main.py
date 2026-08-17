import os
import json
import random
import traceback
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

# Stable models
PRIMARY_MODEL = "gemini-2.5-flash"
BACKUP_MODEL = "gemini-2.5-flash-lite"


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

        print("Gemini client initialized successfully.")

    except Exception as e:
        print("Gemini client initialization error:")
        print(str(e))

        client = None

else:
    print("WARNING: GEMINI_API_KEY not found.")


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
# GEMINI STATUS TEST
# ============================================================

@app.get("/test-ai")
def test_ai():

    if client is None:

        return {
            "status": "error",
            "gemini": False,
            "message": "GEMINI_API_KEY is not configured."
        }

    try:

        answer = ask_gemini(
            "Reply with only: Study With Raman AI is working."
        )

        return {
            "status": "success",
            "gemini": True,
            "model": answer["model"],
            "answer": answer["text"]
        }

    except Exception as e:

        print("TEST AI ERROR:")
        print(str(e))

        return {
            "status": "error",
            "gemini": True,
            "message": str(e)
        }


# ============================================================
# GEMINI HELPER
# ============================================================

def ask_gemini(prompt: str):

    if client is None:

        raise Exception(
            "Gemini client is not configured. "
            "Check GEMINI_API_KEY."
        )

    errors = []

    # --------------------------------------------------------
    # PRIMARY MODEL
    # --------------------------------------------------------

    try:

        print(
            f"Trying Gemini primary model: {PRIMARY_MODEL}"
        )

        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt
        )

        text = getattr(response, "text", None)

        if text and text.strip():

            print(
                f"Gemini primary model worked: {PRIMARY_MODEL}"
            )

            return {
                "text": text.strip(),
                "model": PRIMARY_MODEL
            }

        raise Exception(
            "Primary model returned empty response."
        )

    except Exception as e:

        error_text = str(e)

        print(
            "Primary Gemini model failed:"
        )

        print(error_text)

        errors.append(
            f"{PRIMARY_MODEL}: {error_text}"
        )


    # --------------------------------------------------------
    # BACKUP MODEL
    # --------------------------------------------------------

    try:

        print(
            f"Trying Gemini backup model: {BACKUP_MODEL}"
        )

        response = client.models.generate_content(
            model=BACKUP_MODEL,
            contents=prompt
        )

        text = getattr(response, "text", None)

        if text and text.strip():

            print(
                f"Gemini backup model worked: {BACKUP_MODEL}"
            )

            return {
                "text": text.strip(),
                "model": BACKUP_MODEL
            }

        raise Exception(
            "Backup model returned empty response."
        )

    except Exception as e:

        error_text = str(e)

        print(
            "Backup Gemini model failed:"
        )

        print(error_text)

        errors.append(
            f"{BACKUP_MODEL}: {error_text}"
        )


    # --------------------------------------------------------
    # BOTH MODELS FAILED
    # --------------------------------------------------------

    final_error = "\n".join(errors)

    raise Exception(final_error)


# ============================================================
# CHECK GEMINI ERROR TYPE
# ============================================================

def is_gemini_quota_or_model_error(error_text: str) -> bool:

    text = error_text.lower()

    keywords = [
        "quota",
        "429",
        "resource exhausted",
        "rate limit",
        "too many requests",
        "billing",
        "permission denied",
        "not found",
        "404",
        "model",
        "limit"
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# ============================================================
# LOCAL TUTOR FALLBACK
# ============================================================

def local_tutor_answer(question: str) -> str:

    q = question.lower().strip()

    if "photosynthesis" in q:

        return """
Photosynthesis is the process by which green plants make their food.

Simple explanation:

1. Plants take carbon dioxide from the air.
2. Roots absorb water from the soil.
3. Chlorophyll captures sunlight.
4. Using sunlight, plants convert water and carbon dioxide into glucose.
5. Oxygen is released into the atmosphere.

Formula:

Carbon dioxide + Water + Sunlight → Glucose + Oxygen

In short:
Plants use sunlight to make food and release oxygen.
""".strip()


    if "gravity" in q:

        return """
Gravity is the force that attracts objects toward each other.

On Earth, gravity pulls objects toward the Earth's center.

Example:
When you throw a ball upward, it comes back down because Earth's gravity pulls it downward.

Simple definition:
Gravity is the force that pulls objects toward Earth.
""".strip()


    if "newton" in q:

        return """
Newton's Laws of Motion explain how objects move.

1. First Law:
An object remains at rest or continues moving unless an external force acts on it.

2. Second Law:
Force = Mass × Acceleration.

3. Third Law:
For every action, there is an equal and opposite reaction.

Example:
When you push a wall, the wall pushes back with an equal and opposite force.
""".strip()


    if "cpu" in q:

        return """
CPU stands for Central Processing Unit.

It is often called the brain of a computer because it processes instructions and performs calculations.

Main functions:
• Executes instructions
• Performs calculations
• Controls operations
• Processes data

Example:
When you open an application, the CPU processes the instructions needed to run it.
""".strip()


    if "ram" in q:

        return """
RAM stands for Random Access Memory.

RAM is temporary memory used by a computer or phone while applications are running.

More RAM generally allows a device to handle more applications at the same time.

Example:
If you open several apps, they use RAM to keep their active data available.
""".strip()


    if "python" in q:

        return """
Python is a high-level programming language.

It is popular because its syntax is relatively simple and easy to read.

Python is used for:
• Artificial Intelligence
• Machine Learning
• Web development
• Automation
• Data science
• Backend development

Example:

print("Hello World")

This displays Hello World.
""".strip()


    return f"""
Study With Raman AI Tutor

Your question:
{question}

I can help you understand this topic step by step.

For the best AI-generated explanation, Gemini needs to be available. 
The current Gemini service is temporarily unavailable, so this is the local study fallback.

Try asking a simple question about:
• Science
• Mathematics
• Physics
• Chemistry
• Biology
• History
• English
• Computer
• Programming
""".strip()


# ============================================================
# AI TUTOR
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: AskAIRequest):

    question = request.question.strip()

    if not question:

        return {
            "answer": "Please enter a question.",
            "source": "validation"
        }

    prompt = f"""
You are Study With Raman AI Tutor.

Answer the student's question clearly and correctly.

Question:
{question}

Rules:
- Explain in simple language.
- Use examples when useful.
- For school and college questions, explain step by step.
- Do not make the answer unnecessarily long.
- If the student asks in Hindi or Hinglish, answer in Hinglish.
- If the student asks in English, answer in English.
- Be accurate and educational.
"""

    try:

        result = ask_gemini(prompt)

        return {
            "answer": result["text"],
            "source": "gemini",
            "model": result["model"]
        }

    except Exception as e:

        error_text = str(e)

        print("")
        print("==========================================")
        print("GEMINI TUTOR ERROR")
        print(error_text)
        print("==========================================")
        print("")

        # Local fallback
        fallback = local_tutor_answer(question)

        return {
            "answer": fallback,
            "source": "local_fallback",
            "gemini_error": (
                "Gemini request failed. "
                "Local study answer returned."
            )
        }


# ============================================================
# LOCAL NOTES FALLBACK
# ============================================================

def local_notes(topic: str) -> str:

    topic_lower = topic.lower()

    if "photosynthesis" in topic_lower:

        return """
PHOTOSYNTHESIS - QUICK NOTES

1. Definition
Photosynthesis is the process by which green plants prepare food using sunlight.

2. Requirements
• Sunlight
• Water
• Carbon dioxide
• Chlorophyll

3. Main Product
Glucose is produced as food.

4. By-product
Oxygen is released.

5. Important Point
Chlorophyll captures sunlight energy.

Quick Revision:
CO₂ + H₂O + Sunlight → Glucose + O₂
""".strip()


    if "gravity" in topic_lower:

        return """
GRAVITY - QUICK NOTES

1. Definition
Gravity is the force of attraction between objects having mass.

2. Earth
Earth's gravity pulls objects toward its center.

3. Example
A ball thrown upward comes back down because of gravity.

4. Importance
Gravity keeps us on Earth and helps keep planets and satellites in orbit.

Quick Revision:
Gravity = Attractive force between masses.
""".strip()


    if "computer" in topic_lower:

        return """
COMPUTER - QUICK NOTES

1. Definition
A computer is an electronic device that processes data.

2. Main Components
• CPU
• RAM
• Storage
• Input devices
• Output devices

3. CPU
CPU processes instructions.

4. RAM
RAM provides temporary working memory.

5. Storage
Storage keeps data for longer periods.

Quick Revision:
Input → Processing → Output
""".strip()


    return f"""
{topic.upper()} - QUICK NOTES

1. Definition
{topic} is an important study topic that should be understood using its basic concepts.

2. Important Points
• Learn the basic definition.
• Understand the main concepts.
• Study important examples.
• Revise key facts.

3. Explanation
Break the topic into small sections and understand each section step by step.

4. Examples
Use real-world examples wherever possible.

5. Quick Revision
Read the definition, important points and examples once again before your test.

Note:
Gemini is currently unavailable, so Study With Raman has provided a local study fallback.
""".strip()


# ============================================================
# AI NOTES
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: NotesRequest):

    topic = request.topic.strip()

    if not topic:

        return {
            "notes": "Please enter a topic.",
            "source": "validation"
        }

    prompt = f"""
You are Study With Raman AI Notes Generator.

Create clear and useful study notes about:

{topic}

Format:

1. Definition
2. Important points
3. Detailed explanation
4. Examples
5. Key facts
6. Quick revision

Rules:
- Keep it student-friendly.
- Use simple language.
- Use headings.
- Avoid unnecessary information.
- Make it useful for exam preparation.
"""

    try:

        result = ask_gemini(prompt)

        return {
            "notes": result["text"],
            "source": "gemini",
            "model": result["model"]
        }

    except Exception as e:

        print("")
        print("==========================================")
        print("GEMINI NOTES ERROR")
        print(str(e))
        print("==========================================")
        print("")

        return {
            "notes": local_notes(topic),
            "source": "local_fallback",
            "gemini_error": "Gemini unavailable. Local notes returned."
        }


# ============================================================
# FALLBACK QUIZZES
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
                "Mars is called the Red Planet because of iron oxide on its surface."
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
            "explanation": "12 × 5 = 60."
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
            "explanation": "100 ÷ 4 = 25."
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
            "question":
                "Who played a leading role in drafting the Constitution of India?",
            "options": [
                "Mahatma Gandhi",
                "Dr. B. R. Ambedkar",
                "Jawaharlal Nehru",
                "Sardar Patel"
            ],
            "correctAnswer": 1,
            "explanation":
                "Dr. B. R. Ambedkar played a leading role in drafting the Constitution."
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
                "India became independent in 1947."
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
            "explanation":
                "Mahatma Gandhi is widely known as Mahatma Gandhi."
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
                "The Constitution came into effect in 1950."
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
            "explanation":
                "The opposite of hot is cold."
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
            "explanation":
                "School is a noun because it names a place."
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
            "explanation":
                "The past tense of go is went."
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
            "explanation":
                "Beautiful is an adjective."
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
            "explanation":
                "We use 'an' before the vowel sound in apple."
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
            "question": "What does RAM stand for?",
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
            "question": "Which is an operating system?",
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
                "Kotlin is a primary language used for Android development."
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

    result = ask_gemini(prompt)

    text = result["text"].strip()

    # Remove markdown fences if Gemini accidentally returns them
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

    return {
        "questions": clean_questions[:number_of_questions],
        "model": result["model"]
    }


# ============================================================
# QUIZ ENDPOINT
# ============================================================

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    topic = request.topic.strip()

    number = request.number_of_questions

    if not topic:

        return {
            "questions": [],
            "source": "error",
            "message": "Please enter a quiz topic."
        }

    if number < 1:
        number = 5

    if number > 20:
        number = 20

    # --------------------------------------------------------
    # TRY GEMINI
    # --------------------------------------------------------

    try:

        result = generate_ai_quiz(
            topic,
            number
        )

        print(
            f"AI Quiz generated successfully: {topic}"
        )

        return {
            "questions": result["questions"],
            "source": "gemini",
            "model": result["model"],
            "message": "AI quiz generated successfully."
        }

    except Exception as e:

        print("")
        print("==========================================")
        print("GEMINI QUIZ ERROR")
        print(str(e))
        print("==========================================")
        print("")

        # ----------------------------------------------------
        # FALLBACK QUIZ
        # ----------------------------------------------------

        fallback_questions = create_fallback_quiz(
            topic,
            number
        )

        print(
            f"Fallback Quiz used for topic: {topic}"
        )

        return {
            "questions": fallback_questions,
            "source": "fallback",
            "message": (
                "Gemini unavailable. "
                "Fallback quiz returned."
            )
        }


# ============================================================
# SERVER INFO
# ============================================================

@app.get("/server-info")
def server_info():

    return {
        "app": "Study With Raman",
        "backend": "FastAPI",
        "status": "running",
        "gemini_configured": client is not None,
        "primary_model": PRIMARY_MODEL,
        "backup_model": BACKUP_MODEL,
        "features": [
            "AI Tutor",
            "Smart Notes",
            "AI Quiz",
            "Fallback Tutor",
            "Fallback Notes",
            "Fallback Quiz",
            "Health Check",
            "AI Test"
        ]
    }


# ============================================================
# STARTUP MESSAGE
# ============================================================

print("")
print("==============================================")
print("       STUDY WITH RAMAN AI BACKEND")
print("==============================================")
print(f"Primary Model : {PRIMARY_MODEL}")
print(f"Backup Model  : {BACKUP_MODEL}")
print(
    f"Gemini Ready  : {client is not None}"
)
print("Features      :")
print("  - AI Tutor")
print("  - Smart Notes")
print("  - AI Quiz")
print("  - Local Fallback")
print("  - Health Check")
print("  - AI Test")
print("==============================================")
print("")
