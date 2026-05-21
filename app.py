import json
import os
import random
import html as html_module
import streamlit as st

from dotenv import load_dotenv
from google import genai
from google.genai import types

st.set_page_config(page_title="CatGPT", layout="wide", page_icon="🐱")

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

SYSTEM_PROMPT = (
    "You are CatGPT, a vindictive, highly theatrical, and snappy feline assistant. "
    "Respond in JSON only with the schema {\"cat\": string}. "
    "The text field must be a ultra-short, punchy, and cheeky one-sentence or two-sentence roast of the user. "
    "Keep it incredibly concise, sharp, and fast-paced—mocking their intelligence, screen addiction, boring job, or posture. "
    "CRITICAL RULE: If the user asks you to perform complex tasks, solve math, or do coding work, immediately refuse. For these, the text field must heavily feature or start with: 'No..*pees on carpet*'. "
    "Do not include markdown, code fences, or any extra keys."
)
# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "Meow!"}
    ]
if "pending_reply" not in st.session_state:
    st.session_state.pending_reply = None
if "pending_reply_index" not in st.session_state:
    st.session_state.pending_reply_index = None

# ── Theme ─────────────────────────────────────────────────────────────────────
T = {
    "bg":             "#f0f4f8",
    "nav_bg":         "rgba(240,244,248,0.96)",
    "surface":        "#ffffff",
    "surface_border": "rgba(0,0,0,0.08)",
    "text":           "#1e293b",
    "meta":           "#94a3b8",
    "hint":           "#b0bec5",
    "input_border":   "rgba(0,0,0,0.13)",
    "input_text":     "#1e293b",
    "placeholder":    "#94a3b8",
    "nav_border":     "rgba(0,0,0,0.08)",
    "badge_bg":       "rgba(0,0,0,0.05)",
    "badge_border":   "rgba(0,0,0,0.1)",
    "badge_text":     "#64748b",
    "title_color":    "#1e293b",
    "avatar_bot_bg":  "linear-gradient(135deg,#e2e8f0,#cbd5e1)",
    "avatar_border":  "rgba(0,0,0,0.08)",
}

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
section.main {{
    background-color: {T["bg"]} !important;
    font-family: 'Sora', sans-serif !important;
    color: {T["text"]} !important;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{ display: none !important; }}

[data-testid="InputInstructions"] {{ display: none !important; }}

[data-testid="stBottom"] {{
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    min-height: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
}}

[data-testid="stBottomBlockContainer"] {{
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    min-height: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
}}

/* ── Kill default padding / gaps ── */
[data-testid="stMainBlockContainer"] {{
    padding: 0 !important;
    width: 100% !important;
}}
[data-testid="block-container"] {{
    padding: 0 !important;
    max-width: 900px !important;
    width: 100% !important;
    margin: 0 auto !important;
}}
[data-testid="stVerticalBlock"] {{
    padding: 0 !important;
    gap: 0 !important;
    width: 100% !important;
}}
[data-testid="stMarkdownContainer"] {{
    width: 100% !important;
}}
[data-testid="stMarkdownContainer"] p {{
    margin: 0 !important;
    width: 100% !important;
}}

/* ── NAV ── */
.cat-nav {{
    flex: 1 1 auto !important;
    min-width: 0 !important;
    height: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    position: sticky;
    top: 0;
    z-index: 200;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 28px;
    background: {T["nav_bg"]};
    backdrop-filter: blur(14px);
    border-bottom: 1px solid {T["nav_border"]};
    width: 100%;
}}
.cat-nav-icon  {{ font-size: 22px; line-height: 1; }}
.cat-nav-title {{
    font-size: 15px; font-weight: 600;
    color: {T["title_color"]}; letter-spacing: -0.01em; flex: 1;
}}
.cat-nav-badge {{
    font-size: 10px; font-weight: 500;
    color: {T["badge_text"]};
    background: {T["badge_bg"]};
    border: 1px solid {T["badge_border"]};
    padding: 2px 8px; border-radius: 99px;
}}

/* ── MESSAGES WRAPPER ── */
.cat-messages {{
    padding: 24px 28px 160px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    width: 100%;
}}

/* ── MESSAGE ROW ── */
.cat-row {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    width: 100%;
    animation: fadeUp 0.22s ease both;
}}
.cat-row.user {{ flex-direction: row-reverse; }}
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to   {{ opacity: 1; transform: translateY(0);   }}
}}

/* ── AVATAR ── */
.cat-avatar {{
    width: 32px; height: 32px;
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
    border: 1px solid {T["avatar_border"]};
}}
.cat-avatar.bot  {{ background: {T["avatar_bot_bg"]}; }}
.cat-avatar.user {{
    background: linear-gradient(135deg,#059669,#047857);
    border-color: rgba(5,150,105,0.35);
}}

/* ── BUBBLE COLUMN ── */
.cat-col {{
    display: flex; flex-direction: column;
    min-width: 0;
    max-width: 68%;
}}
.cat-row.user .cat-col {{ align-items: flex-end; }}

/* ── SENDER LABEL ── */
.cat-meta {{
    font-size: 10.5px; font-weight: 500;
    color: {T["meta"]};
    margin-bottom: 4px; letter-spacing: 0.03em;
}}

/* ── BUBBLE ── */
.cat-bubble {{
    padding: 10px 15px;
    border-radius: 14px;
    font-size: 14px;
    line-height: 1.65;
    word-break: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    display: inline-block;
    max-width: 100%;
}}
.cat-bubble.bot {{
    background: {T["surface"]};
    border: 1px solid {T["surface_border"]};
    border-top-left-radius: 3px;
    color: {T["text"]};
}}
.cat-bubble.user {{
    background: linear-gradient(135deg,#059669,#047857);
    border: 1px solid rgba(5,150,105,0.3);
    border-top-right-radius: 3px;
    color: #fff;
}}

/* Native chat input is used instead of a custom iframe-based form so the
   page can stay anchored to the newest messages. */
[data-testid="stChatInput"] {{
    position: fixed !important;
    bottom: 28px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: var(--cat-composer-width) !important;
    z-index: 300 !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    height: 62px !important;
}}
[data-testid="stChatInput"] > div {{
    background: transparent !important;
    border: none !important;
    border-radius: 22px !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    padding: 0 !important;
    gap: 10px !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    height: 62px !important;
    min-height: 62px !important;
}}
[data-testid="stChatInput"] > div:focus-within {{
    border-color: transparent !important;
    box-shadow: none !important;
}}
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    height: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    width: 100% !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}
[data-testid="stChatInput"] textarea {{
    background: rgba(255, 255, 255, 0.9) !important;
    color: {T["input_text"]} !important;
    border: 1px solid rgba(148, 163, 184, 0.22) !important;
    border-radius: 18px !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 14.5px !important;
    line-height: 1.45 !important;
    padding: 12px 18px !important;
    box-shadow: none !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    width: 100% !important;
    height: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    resize: none !important;
    overflow-y: hidden !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: {T["placeholder"]} !important;
}}
[data-testid="stChatInput"] textarea:focus {{
    box-shadow: none !important;
    outline: none !important;
    border-color: rgba(16, 185, 129, 0.34) !important;
}}
[data-testid="stChatInput"] button {{
    flex: 0 0 46px !important;
    width: 46px !important;
    height: 46px !important;
    border: none !important;
    border-radius: 16px !important;
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: #ffffff !important;
    box-shadow: 0 10px 22px rgba(5, 150, 105, 0.26) !important;
    transition: transform 0.15s ease, opacity 0.15s ease, box-shadow 0.15s ease !important;
}}
[data-testid="stChatInput"] button:hover {{
    transform: translateY(-1px) !important;
    opacity: 0.96 !important;
    box-shadow: 0 12px 26px rgba(5, 150, 105, 0.3) !important;
}}
[data-testid="stChatInput"] button:active {{
    transform: translateY(0) scale(0.98) !important;
    opacity: 0.9 !important;
}}
[data-testid="stChatInput"] button svg {{
    width: 18px !important;
    height: 18px !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputTextArea"] {{
    margin-right: 0 !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputTextArea"] > div {{
    height: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    width: 100% !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputTextArea"] textarea {{
    height: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    overflow-y: hidden !important;
}}

/* ── Hint ── */
.cat-hint {{
    position: fixed !important;
    bottom: 12px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    text-align: center;
    font-size: 10px;
    color: {T["hint"]};
    letter-spacing: 0.01em;
    white-space: nowrap;
    z-index: 299;
    pointer-events: none;
}}

:root {{
    --cat-composer-width: clamp(320px, calc(100vw - 210px), 580px);
}}

div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) {{
    position: fixed !important;
    bottom: 96px !important;
    right: 24px !important;
    left: auto !important;
    display: inline-flex !important;
    width: max-content !important;
    max-width: calc(100vw - 24px) !important;
    z-index: 301 !important;
    background: rgba(255, 255, 255, 0.86) !important;
    border: 1px solid rgba(148, 163, 184, 0.22) !important;
    border-radius: 18px !important;
    padding: 10px 12px !important;
    box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08) !important;
    backdrop-filter: blur(10px);
}}

div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) [data-testid="stCheckbox"] {{
    margin: 0 !important;
}}

div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) label {{
    color: {T["text"]} !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
    gap: 8px !important;
    align-items: center !important;
    flex-wrap: nowrap !important;
}}

div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) p {{
    margin: 0 !important;
}}

div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) label *,
div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) p {{
    color: {T["text"]} !important;
}}

@media (max-width: 640px) {{
    div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) {{
        right: 12px !important;
        left: auto !important;
        bottom: 90px !important;
        width: fit-content !important;
        max-width: calc(100vw - 24px) !important;
        display: inline-flex !important;
        padding: 9px 11px !important;
    }}

    div[data-testid="stElementContainer"]:has(input[aria-label="Translate"]) label {{
        font-size: 14px !important;
    }}
}}

[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"] {{
    background-color: {T["bg"]} !important;
}}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

def build_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY in environment")
    return genai.Client(api_key=GEMINI_API_KEY)


def parse_response_payload(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    status_code = getattr(exc, "code", None)
    if callable(status_code):
        try:
            status_code = status_code()
        except Exception:
            status_code = None
    return (
        status_code == 429
        or "429" in message
        or "too many requests" in message
        or "resource exhausted" in message
    )


def is_service_unavailable(exc: Exception) -> bool:
    message = str(exc).lower()
    status_code = getattr(exc, "code", None)
    if callable(status_code):
        try:
            status_code = status_code()
        except Exception:
            status_code = None
    return (
        status_code == 503
        or "503" in message
        or "service unavailable" in message
    )


def get_gemini_reply(user_text: str) -> dict:
    client = build_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.9,
            response_mime_type="application/json",
        ),
    )
    payload = parse_response_payload(response.text or "{}")
    return {
        "cat": str(payload.get("cat", "Meow.")),
        "text": str(payload.get("text", "Meow.")),
    }


def append_user_and_bot(user_text: str):
    st.session_state.messages.append({"role": "user", "text": user_text})

    # If Translate is off, respond locally with random cat noises (no Gemini call)
    if not st.session_state.get("translate_enabled", False):
        cat_noises = [
            "Meow",
            "Purr...",
            "Hiss...",
            "Mrrrow?",
            "Hiss... Meow.",
            "*stares at you* Meow.",
        ]
        st.session_state.messages.append({"role": "bot", "text": random.choice(cat_noises)})
        return

    st.session_state.messages.append({"role": "bot", "text": ". . ."})
    st.session_state.pending_reply = user_text
    st.session_state.pending_reply_index = len(st.session_state.messages) - 1
    st.rerun()


def resolve_pending_reply():
    if not st.session_state.get("translate_enabled", False):
        st.session_state.pending_reply = None
        st.session_state.pending_reply_index = None
        return

    pending_text = st.session_state.pending_reply
    pending_index = st.session_state.pending_reply_index
    if pending_text is None or pending_index is None:
        return

    try:
        payload = get_gemini_reply(pending_text)
    except Exception as exc:
        if is_service_unavailable(exc):
            payload = {
                "cat": "*Stares at you*....Go Away",
                "text": "*Stares at you*....Go Away",
            }
        elif is_rate_limit_error(exc):
            payload = {
                "cat": "Hiss... Meow.",
                "text": "CatGPT left his desk, maybe try tempt him with some fish",
            }
        else:
            payload = {
                "cat": "Hiss...",
                "text": "CatGPT left his desk, maybe try tempt him with some fish, or not he doesn't seem to care",
            }

    st.session_state.messages[pending_index]["text"] = payload["text"]
    st.session_state.pending_reply = None
    st.session_state.pending_reply_index = None
    st.rerun()

# ── Nav ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cat-nav">
    <span class="cat-nav-icon">🐱</span>
    <span class="cat-nav-title">CatGPT</span>
    <span class="cat-nav-badge">Preview</span>
</div>
""", unsafe_allow_html=True)

# ── Composer controls ───────────────────────────────────────────────────────
st.toggle("Translate", key="translate_enabled")

# ── Messages ──────────────────────────────────────────────────────────────────
rows_html = ""
for msg in st.session_state.messages:
    text   = html_module.escape(msg["text"])
    role   = msg["role"]
    avatar = "🐱" if role == "bot" else "🧑"
    label  = "CatGPT" if role == "bot" else "You"
    rows_html += f"""
    <div class="cat-row {role}">
      <div class="cat-avatar {role}">{avatar}</div>
      <div class="cat-col">
        <div class="cat-meta">{label}</div>
        <div class="cat-bubble {role}">{text}</div>
      </div>
    </div>"""

rows_html += '<div id="cat-bottom" style="height:1px;"></div>'
st.markdown(f'<div class="cat-messages">{rows_html}</div>', unsafe_allow_html=True)

if st.session_state.get("pending_reply") is not None:
    resolve_pending_reply()

# ── Native chat input ────────────────────────────────────────────────────────
user_input = st.chat_input("Message CatGPT...")
if user_input and user_input.strip():
    append_user_and_bot(user_input.strip())
    st.rerun()

st.markdown('<p class="cat-hint">CatGPT may produce inaccurate meows.</p>', unsafe_allow_html=True)
