import os
import re
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# If your installed Gemini SDK does not support this model,
# the application will automatically continue using local logic.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Interview Agent",
    description="AI-powered personalized technical interview agent",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",

        # Vercel frontend
        "https://ai-interview-agent-ebon-six.vercel.app",
        "https://ai-interview-agent-git-main-keerthuz.vercel.app",
        "https://ai-interview-agent-k9iw097qp-keerthuz.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None

if GEMINI_API_KEY and genai is not None:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini client initialized.")
    except Exception as error:
        print("Gemini initialization failed:", error)
        client = None
else:
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not configured.")
    else:
        print("Google Gemini SDK is not installed.")


# ============================================================
# REQUEST MODELS
# ============================================================

class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# ============================================================
# IN-MEMORY INTERVIEW SESSIONS
# ============================================================

sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================
# INTERVIEW QUESTIONS
# ============================================================

QUESTIONS = [
    {
        "topic": "RAG",
        "question": (
            "Explain Retrieval-Augmented Generation (RAG). "
            "How would you design a basic RAG system?"
        ),
        "answer": (
            "RAG retrieves relevant documents or chunks from an external "
            "knowledge source, usually using embeddings and vector search, "
            "then provides that retrieved context to an LLM before generation."
        ),
        "keywords": [
            "retrieval",
            "embedding",
            "vector",
            "context",
            "document",
            "llm",
        ],
    },
    {
        "topic": "Vector Database",
        "question": (
            "What is a vector database and why is it useful in an AI application?"
        ),
        "answer": (
            "A vector database stores numerical embeddings and supports "
            "similarity search so applications can retrieve semantically "
            "related information."
        ),
        "keywords": [
            "embedding",
            "vector",
            "similarity",
            "search",
            "semantic",
            "database",
        ],
    },
    {
        "topic": "Prompt Engineering",
        "question": (
            "What is prompt engineering? Give an example of how you would "
            "improve a prompt for a technical AI assistant."
        ),
        "answer": (
            "Prompt engineering is the process of designing instructions "
            "and context for an LLM to produce more reliable and useful results. "
            "Good prompts define the role, task, context, constraints, and output format."
        ),
        "keywords": [
            "prompt",
            "instruction",
            "context",
            "role",
            "constraint",
            "format",
        ],
    },
    {
        "topic": "Agents",
        "question": (
            "What is an AI agent? Explain how an agent differs from a normal "
            "LLM chatbot."
        ),
        "answer": (
            "An AI agent can reason about a task, maintain state, choose actions, "
            "use tools, observe results, and continue toward a goal. A normal "
            "chatbot may simply generate a response from the current conversation."
        ),
        "keywords": [
            "agent",
            "tool",
            "action",
            "reason",
            "state",
            "goal",
        ],
    },
    {
        "topic": "MCP",
        "question": (
            "What is MCP and how could it be useful for an AI interview agent?"
        ),
        "answer": (
            "MCP, or Model Context Protocol, provides a standardized way for "
            "AI applications to interact with external tools and data sources."
        ),
        "keywords": [
            "mcp",
            "model context protocol",
            "tool",
            "data",
            "server",
            "context",
        ],
    },
    {
        "topic": "Production Architecture",
        "question": (
            "Design a production architecture for an AI interview agent "
            "that needs to handle many simultaneous candidates."
        ),
        "answer": (
            "A production architecture should include a scalable API layer, "
            "session/state storage, an LLM service, database, caching where "
            "appropriate, authentication, rate limiting, monitoring, logging, "
            "and asynchronous processing where useful."
        ),
        "keywords": [
            "api",
            "scaling",
            "database",
            "redis",
            "queue",
            "authentication",
            "monitoring",
            "rate",
            "load",
        ],
    },
    {
        "topic": "Evaluation",
        "question": (
            "How would you evaluate whether an AI interview agent is producing "
            "good questions and fair candidate evaluations?"
        ),
        "answer": (
            "Evaluation can use predefined rubrics, representative test sets, "
            "human review, consistency checks, accuracy metrics, hallucination "
            "checks, bias testing, and monitoring of production outcomes."
        ),
        "keywords": [
            "evaluation",
            "rubric",
            "accuracy",
            "bias",
            "human",
            "testing",
            "metrics",
        ],
    },
    {
        "topic": "Deployment",
        "question": (
            "How would you deploy this AI interview application to production "
            "and keep it reliable?"
        ),
        "answer": (
            "Deploy the frontend and backend separately or through a managed "
            "platform, store secrets securely, use HTTPS, configure monitoring "
            "and logging, add health checks, rate limiting, error handling, "
            "autoscaling, and a reliable persistent database."
        ),
        "keywords": [
            "deploy",
            "https",
            "secret",
            "monitoring",
            "logging",
            "health",
            "database",
            "scaling",
        ],
    },
]


# ============================================================
# HELPER: NORMALIZE TEXT
# ============================================================

def normalize_text(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )


# ============================================================
# SCORE INDIVIDUAL ANSWER
# ============================================================

def score_answer(
    answer: str,
    question_data: Dict[str, Any],
) -> int:

    if not answer or not answer.strip():
        return 0

    text = normalize_text(answer)

    keywords = question_data.get("keywords", [])

    if not keywords:
        return 50

    matches = 0

    for keyword in keywords:
        if keyword.lower() in text:
            matches += 1

    keyword_score = (matches / len(keywords)) * 75

    word_count = len(text.split())

    length_bonus = 0

    if word_count >= 20:
        length_bonus = 10

    if word_count >= 50:
        length_bonus = 15

    final_score = int(
        min(keyword_score + length_bonus, 100)
    )

    if word_count < 5:
        final_score = min(final_score, 20)

    return final_score


# ============================================================
# LOCAL FINAL EVALUATION
# ============================================================

def local_final_evaluation(
    session: Dict[str, Any],
) -> Dict[str, Any]:

    answers = session.get("answers", [])

    if not answers:
        return {
            "score": 0,
            "feedback": "No answers were submitted.",
            "strengths": [],
            "areasToImprove": [
                "Provide answers to the interview questions."
            ],
        }

    scores = [
        item.get("score", 0)
        for item in answers
    ]

    overall_score = int(
        sum(scores) / len(scores)
    )

    if overall_score >= 85:

        feedback = (
            "Excellent technical performance. You demonstrated strong "
            "understanding of AI engineering concepts and communicated "
            "your reasoning effectively."
        )

    elif overall_score >= 70:

        feedback = (
            "Good technical performance. You demonstrated a solid "
            "understanding of the major concepts, although some answers "
            "could benefit from more depth and production examples."
        )

    elif overall_score >= 50:

        feedback = (
            "Fair performance. You understand several important concepts, "
            "but your answers need more technical depth, examples, and "
            "discussion of real-world trade-offs."
        )

    else:

        feedback = (
            "Your answers show some initial understanding, but you should "
            "strengthen your fundamentals and provide more detailed "
            "technical explanations."
        )

    strengths = []

    if overall_score >= 70:
        strengths.append(
            "Good understanding of AI engineering concepts"
        )

    if overall_score >= 60:
        strengths.append(
            "Able to explain core technical ideas"
        )

    if any(
        item.get("score", 0) >= 80
        for item in answers
    ):
        strengths.append(
            "Strong performance on selected technical topics"
        )

    if not strengths:
        strengths.append(
            "Demonstrated willingness to engage with technical questions"
        )

    areas = []

    if overall_score < 80:
        areas.append(
            "Provide more technical depth in your answers"
        )

    if overall_score < 70:
        areas.append(
            "Use concrete real-world project examples"
        )

    if overall_score < 60:
        areas.append(
            "Strengthen fundamentals around AI architecture and deployment"
        )

    if not areas:
        areas.append(
            "Continue improving production architecture trade-off explanations"
        )

    return {
        "score": overall_score,
        "feedback": feedback,
        "strengths": strengths,
        "areasToImprove": areas,
    }


# ============================================================
# GEMINI FINAL EVALUATION
# ============================================================

def gemini_final_evaluation(
    session: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if client is None:
        return None

    answers = session.get("answers", [])

    if not answers:
        return None

    evaluation_data = []

    for item in answers:
        evaluation_data.append(
            {
                "question": item["question"],
                "candidateAnswer": item["answer"],
                "expectedAnswer": item["expectedAnswer"],
            }
        )

    prompt = f"""
You are a professional technical interviewer.

Evaluate the candidate's interview performance.

Interview answers:

{json.dumps(evaluation_data, indent=2)}

Return ONLY valid JSON in this exact structure:

{{
    "score": 0,
    "feedback": "short overall feedback",
    "strengths": [
        "strength 1",
        "strength 2"
    ],
    "areasToImprove": [
        "improvement 1",
        "improvement 2"
    ]
}}

Rules:

- score must be an integer from 0 to 100
- evaluate technical correctness
- evaluate depth
- evaluate clarity
- do not reward an answer merely because it is long
- do not invent information about the candidate
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        text = response.text.strip()

        text = text.replace(
            "```json",
            "",
        )

        text = text.replace(
            "```",
            "",
        )

        text = text.strip()

        result = json.loads(text)

        return {
            "score": int(
                result.get("score", 0)
            ),
            "feedback": result.get(
                "feedback",
                "",
            ),
            "strengths": result.get(
                "strengths",
                [],
            ),
            "areasToImprove": result.get(
                "areasToImprove",
                [],
            ),
        }

    except Exception as error:

        print(
            "Gemini evaluation failed:",
            error,
        )

        return None


# ============================================================
# GEMINI QUESTION GENERATION
# ============================================================

def generate_question_with_gemini(
    topic: str,
    previous_answers: List[Dict[str, Any]],
) -> Optional[str]:

    if client is None:
        return None

    prompt = f"""
You are a technical interviewer conducting an AI engineering interview.

Topic:
{topic}

Previous interview answers:
{json.dumps(previous_answers, indent=2)}

Create ONE concise technical interview question.

The question should test practical understanding.

Do not provide the answer.

Return only the question text.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
            ),
        )

        if response.text:
            return response.text.strip()

    except Exception as error:

        print(
            "Gemini question generation failed:",
            error,
        )

    return None


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "name": "AI Interview Agent",
        "version": "1.0.0",
        "status": "running",
        "message": (
            "AI-powered personalized technical interview agent"
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "geminiConfigured": client is not None,
        "model": GEMINI_MODEL,
        "activeSessions": len(sessions),
    }


# ============================================================
# TEST DATA
# ============================================================

@app.get("/test-data")
def test_data():

    return {
        "candidate": {
            "id": "CAND-001",
            "name": "Sarah Johnson",
        },
        "topics": [
            "RAG",
            "Vector DB",
            "Prompt Engineering",
            "Agentic AI",
            "MCP",
            "Deployment",
        ],
    }


# ============================================================
# GET CANDIDATE
# ============================================================

@app.get("/candidate/{candidate_id}")
def get_candidate(
    candidate_id: str,
):

    return {
        "id": candidate_id,
        "name": "Candidate",
        "status": "ready",
    }


# ============================================================
# TEST GEMINI
# ============================================================

@app.get("/test-gemini")
def test_gemini():

    if client is None:

        return {
            "success": False,
            "error": (
                "GEMINI_API_KEY is not configured "
                "or Gemini SDK is unavailable."
            ),
            "model": GEMINI_MODEL,
        }

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                "Explain RAG in one short paragraph "
                "for a technical interview."
            ),
        )

        return {
            "success": True,
            "response": response.text,
            "model": GEMINI_MODEL,
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error),
            "model": GEMINI_MODEL,
        }


# ============================================================
# START / CONTINUE INTERVIEW
# ============================================================

@app.post("/api/interview")
def interview(
    request: InterviewRequest,
):

    session_id = request.sessionId

    # --------------------------------------------------------
    # CREATE SESSION
    # --------------------------------------------------------

    if session_id not in sessions:

        sessions[session_id] = {
            "candidate": request.candidate or {},
            "question_index": 0,
            "answers": [],
            "completed": False,
        }

    session = sessions[session_id]

    # --------------------------------------------------------
    # IF ALREADY COMPLETED
    # --------------------------------------------------------

    if session["completed"]:

        evaluation = session.get(
            "evaluation",
            {},
        )

        return {
            "sessionId": session_id,
            "done": True,
            "score": evaluation.get(
                "score",
                0,
            ),
            "feedback": evaluation.get(
                "feedback",
                "",
            ),
            "strengths": evaluation.get(
                "strengths",
                [],
            ),
            "areasToImprove": evaluation.get(
                "areasToImprove",
                [],
            ),
            "answerKey": session.get(
                "answerKey",
                [],
            ),
        }

    # --------------------------------------------------------
    # FIRST REQUEST
    # message == None
    # --------------------------------------------------------

    if request.message is None:

        current_index = session["question_index"]

        question_data = QUESTIONS[current_index]

        question = question_data["question"]

        return {
            "sessionId": session_id,
            "done": False,
            "questionNumber": current_index + 1,
            "totalQuestions": len(QUESTIONS),
            "topic": question_data["topic"],
            "question": question,
        }

    # --------------------------------------------------------
    # SAVE CANDIDATE ANSWER
    # --------------------------------------------------------

    current_index = session["question_index"]

    if current_index >= len(QUESTIONS):

        current_index = len(QUESTIONS) - 1

    question_data = QUESTIONS[current_index]

    candidate_answer = request.message.strip()

    answer_score = score_answer(
        candidate_answer,
        question_data,
    )

    session["answers"].append(
        {
            "questionNumber": current_index + 1,
            "topic": question_data["topic"],
            "question": question_data["question"],
            "answer": candidate_answer,
            "score": answer_score,
            "expectedAnswer": question_data["answer"],
        }
    )

    # --------------------------------------------------------
    # MOVE TO NEXT QUESTION
    # --------------------------------------------------------

    session["question_index"] += 1

    # --------------------------------------------------------
    # INTERVIEW COMPLETE
    # --------------------------------------------------------

    if session["question_index"] >= len(QUESTIONS):

        # Try Gemini first.
        evaluation = gemini_final_evaluation(
            session
        )

        # Fallback to local evaluation.
        if evaluation is None:

            evaluation = local_final_evaluation(
                session
            )

        session["evaluation"] = evaluation

        # ----------------------------------------------------
        # BUILD ANSWER KEY
        # ----------------------------------------------------

        answer_key = []

        for item in session["answers"]:

            answer_key.append(
                {
                    "questionNumber": item[
                        "questionNumber"
                    ],
                    "topic": item[
                        "topic"
                    ],
                    "question": item[
                        "question"
                    ],
                    "candidateAnswer": item[
                        "answer"
                    ],
                    "expectedAnswer": item[
                        "expectedAnswer"
                    ],
                    "questionScore": item[
                        "score"
                    ],
                }
            )

        session["answerKey"] = answer_key

        session["completed"] = True

        return {
            "sessionId": session_id,
            "done": True,
            "score": evaluation["score"],
            "feedback": evaluation[
                "feedback"
            ],
            "strengths": evaluation[
                "strengths"
            ],
            "areasToImprove": evaluation[
                "areasToImprove"
            ],
            "answerKey": answer_key,
        }

    # --------------------------------------------------------
    # NEXT QUESTION
    # --------------------------------------------------------

    next_index = session["question_index"]

    next_question_data = QUESTIONS[
        next_index
    ]

    next_question = next_question_data[
        "question"
    ]

    return {
        "sessionId": session_id,
        "done": False,
        "questionNumber": next_index + 1,
        "totalQuestions": len(QUESTIONS),
        "topic": next_question_data[
            "topic"
        ],
        "question": next_question,
    }


# ============================================================
# GET INTERVIEW RESULT
# ============================================================

@app.get("/api/interview/{session_id}/result")
def get_interview_result(
    session_id: str,
):

    if session_id not in sessions:

        return {
            "success": False,
            "error": "Interview session not found.",
        }

    session = sessions[session_id]

    if not session.get("completed"):

        return {
            "success": False,
            "error": "Interview is not completed yet.",
        }

    evaluation = session.get(
        "evaluation",
        {},
    )

    return {
        "success": True,
        "sessionId": session_id,
        "score": evaluation.get(
            "score",
            0,
        ),
        "feedback": evaluation.get(
            "feedback",
            "",
        ),
        "strengths": evaluation.get(
            "strengths",
            [],
        ),
        "areasToImprove": evaluation.get(
            "areasToImprove",
            [],
        ),
        "answerKey": session.get(
            "answerKey",
            [],
        ),
    }


# ============================================================
# OPTIONAL: RESET SESSION
# ============================================================

@app.delete("/api/interview/{session_id}")
def reset_interview(
    session_id: str,
):

    if session_id in sessions:

        del sessions[session_id]

    return {
        "success": True,
        "sessionId": session_id,
        "message": "Interview session reset.",
    }