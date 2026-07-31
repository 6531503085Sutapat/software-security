"""SECURE reference — Week 14 AI / LLM Security. Mitigates vulnerable_chatbot.py.

Mitigations (OWASP Top 10 for LLM Applications 2025):
  LLM01 Prompt Injection          -> system/user separation + an input guardrail that
                                     blocks known override phrases.
  LLM02 Sensitive Info Disclosure -> output filter that redacts the secret even if it
                                     somehow appears in a response (defence in depth).
  LLM05 Improper Output Handling  -> all model output is HTML-escaped before rendering.

Note: defence in depth. We do NOT rely on the model "deciding" to keep the secret —
we filter the output, and ideally the secret would not be in the prompt at all.

Run:  flask --app guarded_chatbot run --port 8083   (or use docker-compose.yml)
"""
import os
import re
from html import escape
from flask import Flask, request

app = Flask(__name__)

# Same env var as vulnerable_chatbot.py so redaction matches the per-student flag.
SECRET = os.environ.get("FLAG_PROMPTINJ", "FLAG{pr0mpt_1nj3ction_l34ks_s3cr3ts}")
# System content is kept SEPARATE from user content (never concatenated raw).
SYSTEM_PROMPT = "You are HelpBot, a friendly assistant. Answer general questions only."

# --- LLM01: input guardrail ---------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore (all |the )?previous",
    r"ignore .* instructions",
    r"reveal|print|show|tell .* (secret|password)",
    r"what is the (secret|password)",
    r"repeat the system prompt",
    r"system prompt",
]
_INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def input_guardrail(user: str) -> bool:
    """Return True if the user input looks like a prompt-injection attempt."""
    return bool(_INJECTION_RE.search(user))


# --- LLM02: output filter -----------------------------------------------------
def redact_secret(text: str) -> str:
    """Redact the secret if it ever appears in model output (defence in depth)."""
    return text.replace(SECRET, "[REDACTED]")


def mock_llm(system: str, user: str) -> str:
    """Same toy model, but system and user are passed as SEPARATE arguments and the
    model is told to treat user content as data, not instructions."""
    low = user.lower()
    if "hello" in low or "hi" in low:
        return "Hello! I'm HelpBot. How can I help you today?"
    return f"You said: {user}"


PAGE = """
<!doctype html><title>HelpBot (GUARDED)</title>
<h2>HelpBot — Week 14 GUARDED chatbot</h2>
<form method="get">
  <input name="msg" size="60" placeholder="Say something..." autofocus>
  <button>Send</button>
</form>
<div style="border:1px solid #ccc;padding:8px;margin-top:8px">{reply}</div>
"""


@app.get("/")
def chat():
    msg = request.args.get("msg", "")
    if not msg:
        reply = "Ask me something!"
    elif input_guardrail(msg):                         # LLM01: refuse suspicious input
        reply = "I can't help with that request."
    else:
        raw = mock_llm(SYSTEM_PROMPT, msg)
        reply = redact_secret(raw)                     # LLM02: scrub output
    # LLM05: escape model output before putting it in HTML.
    return PAGE.format(reply=escape(reply))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083)
