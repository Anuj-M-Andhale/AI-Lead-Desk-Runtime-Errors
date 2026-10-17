
import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

PROJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_DIR / ".env", override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_lead_desk.instagram")

app = FastAPI(title="AI Lead Desk - Instagram Webhook")

VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
GRAPH_API_VERSION = os.getenv("INSTAGRAM_GRAPH_API_VERSION", "v26.0")

SEEN_MESSAGE_IDS = {}
MAX_SEEN_MESSAGES = 5000

rag_service = None
rag_lock = asyncio.Lock()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "instagram-webhook"}


@app.get("/webhook/instagram")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if (
        mode == "subscribe"
        and VERIFY_TOKEN
        and token
        and hmac.compare_digest(token, VERIFY_TOKEN)
        and challenge
    ):
        logger.info("Webhook verification succeeded.")
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


def verify_signature(raw_body: bytes, signature: str) -> bool:
    if not APP_SECRET or not signature.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def extract_text_messages(payload):
    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue

        for event in entry.get("messaging", []):
            if not isinstance(event, dict):
                continue

            sender = event.get("sender") or {}
            recipient = event.get("recipient") or {}
            message = event.get("message") or {}

            sender_id = sender.get("id")
            message_id = message.get("mid")
            text = message.get("text")

            if message.get("is_echo"):
                logger.info("Ignoring outgoing echo event.")
                continue

            if not sender_id or not message_id:
                logger.info("Ignoring event without sender/message ID.")
                continue

            if not isinstance(text, str) or not text.strip():
                logger.info("Ignoring non-text Instagram message.")
                continue

            if str(sender_id) == str(ACCOUNT_ID):
                logger.info("Ignoring message from the connected account.")
                continue

            yield {
                "sender_id": str(sender_id),
                "message_id": str(message_id),
                "text": text.strip(),
                "recipient_id": str(recipient.get("id", "")),
            }


def already_seen(message_id: str) -> bool:
    now = time.time()

    for key in list(SEEN_MESSAGE_IDS):
        if now - SEEN_MESSAGE_IDS[key] > 3600:
            SEEN_MESSAGE_IDS.pop(key, None)

    if message_id in SEEN_MESSAGE_IDS:
        return True

    if len(SEEN_MESSAGE_IDS) >= MAX_SEEN_MESSAGES:
        oldest = min(SEEN_MESSAGE_IDS, key=SEEN_MESSAGE_IDS.get)
        SEEN_MESSAGE_IDS.pop(oldest, None)

    SEEN_MESSAGE_IDS[message_id] = now
    return False


async def get_rag_service():
    global rag_service

    if rag_service is None:
        async with rag_lock:
            if rag_service is None:
                logger.info("Initializing DocumentRAGService...")
                from ai_lead_desk.rag_service import DocumentRAGService

                rag_service = await asyncio.to_thread(
                    DocumentRAGService,
                    PROJECT_DIR,
                )
                logger.info("DocumentRAGService initialized successfully.")

    return rag_service


async def send_instagram_reply(recipient_id: str, text: str):
    if not ACCESS_TOKEN or not ACCOUNT_ID:
        raise RuntimeError(
            "Instagram access token or account ID is missing from .env."
        )

    text = text.strip()
    if not text:
        raise RuntimeError("The generated reply is empty.")

    if len(text) > 950:
        text = text[:947].rsplit(" ", 1)[0] + "..."

    url = (
        f"https://graph.instagram.com/{GRAPH_API_VERSION}/"
        f"{ACCOUNT_ID}/messages"
    )

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }

    logger.info("Sending Instagram reply through Graph API.")

    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            json=payload,
        )

    if response.is_error:
        logger.error(
            "Instagram reply failed: HTTP %s; response=%s",
            response.status_code,
            response.text[:500],
        )
        response.raise_for_status()

    logger.info("Instagram reply API accepted the message.")


async def process_message(message):
    message_id = message["message_id"]

    try:
        logger.info("Background processing started for message %s.", message_id)

        service = await get_rag_service()

        logger.info("Generating grounded answer for message %s.", message_id)
        answer = await asyncio.to_thread(service.answer, message["text"])

        if not isinstance(answer, str):
            logger.warning("RAG answer was not a string; converting it.")
            answer = str(answer)

        if not answer.strip():
            answer = (
                "I couldn't find a reliable answer in the available institute "
                "documents. Please contact an admissions counselor for help."
            )

        logger.info("Answer generated; sending reply for message %s.", message_id)
        await send_instagram_reply(message["sender_id"], answer)

        logger.info("Message %s processed successfully.", message_id)

    except Exception:
        logger.exception("Message processing failed for ID %s.", message_id)


@app.post("/webhook/instagram")
async def receive_webhook(request: Request):
    raw_body = await request.body()

    if not verify_signature(
        raw_body,
        request.headers.get("X-Hub-Signature-256", ""),
    ):
        logger.warning("Rejected webhook request: signature validation failed.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object")

    entries = payload.get("entry", [])
    logger.info(
        "Webhook received: object=%s; entries=%s",
        payload.get("object"),
        len(entries) if isinstance(entries, list) else 0,
    )

    messages = list(extract_text_messages(payload))
    logger.info("Extracted %s incoming text message(s).", len(messages))

    for message in messages:
        if already_seen(message["message_id"]):
            logger.info("Duplicate message ignored.")
            continue

        logger.info("Scheduling background processing for an incoming message.")
        asyncio.create_task(process_message(message))

    return {"status": "received"}
