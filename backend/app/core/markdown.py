import os
from groq import Groq
from app.core.errors import LLMError

MODEL = "llama-3.3-70b-versatile"


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise LLMError("GROQ_API_KEY environment variable is not set. Add your key to backend/.env")
    return Groq(api_key=api_key)


# ──────────────────────────────────────────────
# Step 1 — Generate Topic Titles
# ──────────────────────────────────────────────
def generate_topics(
    prompt: str,
    category: str,
    num_titles: int,
    research_context: str,
) -> str:
    """Generate a numbered list of compelling YouTube video topic titles."""
    client = _get_client()

    topic_source = prompt.strip() if prompt.strip() else f"trending topics in the {category} niche"
    tone = _get_tone_guidance(category, prompt)

    system_prompt = """You are an expert YouTube title strategist.
Your job is to generate compelling, publish-ready YouTube video titles based on research data.

RULES:
- Output ONLY the numbered list. No commentary, no explanation, no markdown headers.
- Titles must be clear, specific, and clickable — not clickbait, not vague.
- Each title should stand alone as a strong video concept.
- Match the tone and style appropriate to the category."""

    user_prompt = f"""Generate exactly {num_titles} YouTube video title(s) based on the following:

Topic focus: {topic_source}
Category: {category or "General"}
Tone guidance: {tone}

Research context (use this as your factual foundation):
{research_context or "No specific research data — use your knowledge of the niche."}

Output format (strictly follow this):
1. [Title here]
2. [Title here]
...

Output only the numbered list. Nothing else."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.75,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise LLMError(f"Failed to generate topics: {str(e)}")


# ──────────────────────────────────────────────
# Step 2 — Generate Full Script
# ──────────────────────────────────────────────
def generate_script(
    topic: str,
    category: str = "",
    video_duration: str = "5 min",
    broll_enabled: bool = False,
    onscreen_text_enabled: bool = False,
    research_context: str = "",
    # legacy compat params (ignored)
    prompt: str = "",
    keywords: list = None,
    intent: str = "",
    ranked_items: list = None,
    video_duration_legacy: str = "",
) -> str:
    """Generate a fully structured, ready-to-record YouTube video script."""
    client = _get_client()

    effective_topic = topic or prompt
    effective_duration = video_duration or video_duration_legacy or "5 min"
    tone = _get_tone_guidance(category, effective_topic)

    broll_instruction = (
        "\n- At relevant moments, add B-Roll suggestions in brackets like: [B-Roll: aerial shot of city skyline]"
        if broll_enabled else ""
    )
    onscreen_instruction = (
        "\n- At high-impact moments, add on-screen text cues in brackets like: [TEXT: '3 MILLION jobs gone by 2027']"
        if onscreen_text_enabled else ""
    )

    system_prompt = f"""You are an elite YouTube scriptwriter. Your scripts are used by top creators across every niche.

TONE: {tone}

SCRIPT FORMAT — use these exact section labels:
[HOOK]
(10–20 seconds of gripping spoken content)

[INTRODUCTION]
(Set up the video's promise and context)

[MAIN]
(The core content — depth scaled to video length)

[KEY INSIGHTS]
(The most memorable, shareable takeaways)

[CONCLUSION]
(Natural wrap-up. No forced "smash subscribe" unless it fits the tone)

CRITICAL RULES:
- Output ONLY the script. No meta commentary. No explanation of what you're doing.
- Write for spoken delivery. Natural rhythm. Varied sentence length.
- Use curiosity loops and open loops to hold viewer attention.
- Do NOT fabricate statistics — only reference facts from the research context provided.
- Target script length: {effective_duration} of spoken content.{broll_instruction}{onscreen_instruction}"""

    user_prompt = f"""Write a complete YouTube video script for the following topic:

Title: {effective_topic}
Category: {category or "General"}
Target length: {effective_duration}

Research context (base your facts on this):
{research_context or "No specific research data — draw on your knowledge of the topic."}

Remember: Output only the labeled script. Nothing else."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.72,
            max_tokens=6000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise LLMError(f"Failed to generate script: {str(e)}")


def _get_tone_guidance(category: str, prompt: str) -> str:
    """Return tone instructions based on category and prompt content."""
    cat = (category or "").lower()
    p = (prompt or "").lower()

    finance_signals = {"finance", "stock", "invest", "econom", "money", "budget", "crypto", "market"}
    entertainment_signals = {"gaming", "game", "movie", "film", "entertainment", "lifestyle", "pop", "celebrity", "music"}
    education_signals = {"education", "learn", "how to", "tutorial", "science", "history", "explain", "technology", "tech"}

    if cat in {"finance", "economics"} or any(s in p for s in finance_signals):
        return ("Informational, clear, confident, and authoritative — but still engaging and human. "
                "Structured delivery. Avoid hype. Speak to someone smart who wants to understand, not be sold to.")
    elif cat in {"gaming", "entertainment", "lifestyle"} or any(s in p for s in entertainment_signals):
        return ("Casual, energetic, conversational, and upbeat. High energy from the first second. "
                "Talk like you're catching up with a friend who loves this stuff.")
    elif cat in {"education", "technology"} or any(s in p for s in education_signals):
        return ("Clear, engaging, and accessible. Break complex ideas down simply. "
                "Keep it interesting — think Kurzgesagt or Veritasium energy.")
    else:
        return ("Neutral but engaging and conversational. Friendly but credible. "
                "Adjust naturally to however the topic feels as you write.")


# Backwards compatibility alias
generate_report = generate_script
