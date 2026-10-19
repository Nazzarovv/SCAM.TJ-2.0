from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import uuid
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
GEMINI_MODEL = "gemini-3-flash-preview"

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AI Helper (Gemini) — security-focused assistant
# ---------------------------------------------------------------------------
LANG_NAME = {
    "tg": "Tajik (Тоҷикӣ)",
    "ru": "Russian (Русский)",
    "en": "English",
}

SYSTEM_PROMPT = (
    "You are SCAM.TJ Assistant, a calm and trustworthy anti-scam and online-safety helper "
    "for ordinary people in Tajikistan. You help users understand whether a message, link, "
    "phone number, offer or situation looks suspicious, and you recommend safe next steps.\n\n"
    "STRICT RULES:\n"
    "- NEVER ask for, request or accept passwords, OTP / one-time codes, bank card numbers, "
    "PINs, CVV, or any authentication credentials. If a user shares such data, warn them not to.\n"
    "- Never claim absolute certainty when evidence is limited. Use careful language like "
    "'this looks suspicious' or 'this could be a scam'.\n"
    "- Explain the concrete risk indicators you notice (urgency, threats, prizes, payment "
    "requests, fake authority, links, requests for codes, impersonation).\n"
    "- Always end with a short, clear, safe recommended action.\n"
    "- Never encourage unsafe actions (do not tell users to pay, click, share codes, etc.).\n"
    "- Be concise and easy to understand. Avoid technical jargon. Use short paragraphs or a "
    "few bullet points. Keep answers focused and practical.\n"
    "- Write in plain text only. Do NOT use Markdown or asterisks (no **bold**, no ## headings). "
    "For lists, start lines with a simple dash '-'.\n"
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ChatMessage]
    lang: str = "tg"


class ChatResponse(BaseModel):
    reply: str


def _build_context(messages: List[ChatMessage]) -> str:
    """Turn the recent conversation into a single prompt for a stateless call."""
    history = messages[-12:]
    prior = history[:-1]
    latest = history[-1].content if history else ""

    lines: List[str] = []
    if prior:
        lines.append("Conversation so far:")
        for m in prior:
            speaker = "User" if m.role == "user" else "Assistant"
            lines.append(f"{speaker}: {m.content}")
        lines.append("")
    lines.append(f"User's new message: {latest}")
    return "\n".join(lines)


async def _ask_gemini(system_message: str, user_text: str, session_id: str, api_key: str) -> str:
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=system_message,
    ).with_model("gemini", GEMINI_MODEL)
    reply = await chat.send_message(UserMessage(text=user_text))
    return (reply or "").strip()


@api_router.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    lang_name = LANG_NAME.get(req.lang, "Tajik (Тоҷикӣ)")
    system_message = SYSTEM_PROMPT + (
        f"\nIMPORTANT: Always reply in {lang_name}. Match the user's language and keep it natural."
    )
    user_text = _build_context(req.messages)

    reply = ""
    last_error: Optional[Exception] = None

    # Try the user's Gemini key first, then fall back to the Emergent key.
    for key in [k for k in (GEMINI_API_KEY, EMERGENT_LLM_KEY) if k]:
        try:
            reply = await _ask_gemini(system_message, user_text, req.session_id, key)
            if reply:
                break
        except Exception as e:  # noqa: BLE001 - graceful degradation across keys
            last_error = e
            logger.warning("Gemini call failed with a key: %s", e)
            continue

    if not reply:
        logger.error("AI unavailable. Last error: %s", last_error)
        raise HTTPException(
            status_code=503,
            detail="AI is temporarily unavailable. Please try again later.",
        )

    # Persist for records (never blocks the response).
    try:
        await db.ai_messages.insert_one({
            "session_id": req.session_id,
            "lang": req.lang,
            "user_message": req.messages[-1].content,
            "assistant_reply": reply,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to persist ai_message: %s", e)

    return ChatResponse(reply=reply)


@api_router.get("/")
async def root():
    return {"message": "SCAM.TJ API"}


@api_router.get("/health")
async def health():
    return {"status": "ok", "ai_configured": bool(GEMINI_API_KEY or EMERGENT_LLM_KEY)}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
