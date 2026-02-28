import os
import json
from groq import Groq
from app.sources.base import ContentItem
from app.sources.youtube import YouTubeSource
from app.sources.reddit import RedditSource
from app.sources.generic import GenericSource
from app.core.ranking import rank_items
from app.core.markdown import generate_script
from app.core.storage import save_record
from app.core.errors import LLMError, ResearchError

MODEL = "llama-3.3-70b-versatile"


def _get_llm_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise LLMError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)


# ──────────────────────────────────────────────
# P — Perceive
# ──────────────────────────────────────────────
def perceive(prompt: str, target_urls: list[str]) -> dict:
    """Parse prompt, extract keywords, classify intent, expand semantics."""
    client = _get_llm_client()

    system = """You are an expert research planner. Analyze the user's research prompt and return a JSON object with:
- "keywords": list of 5-10 relevant search keywords/phrases
- "intent": one of "trend_discovery", "influencer_ranking", "content_ideation"
- "expanded_keywords": 5 additional semantically related keywords
- "source_strategy": list of sources to search, from ["youtube", "reddit", "generic"]
- "research_plan": brief description of the research approach

Return ONLY valid JSON, no markdown formatting or code blocks."""

    user_msg = f"""Research prompt: "{prompt}"
Target URLs: {json.dumps(target_urls) if target_urls else "None (use keyword search)"}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: extract basic keywords from prompt
        words = prompt.lower().split()
        return {
            "keywords": words[:8],
            "intent": "content_ideation",
            "expanded_keywords": [],
            "source_strategy": ["youtube", "reddit"],
            "research_plan": f"Search for content related to: {prompt}",
        }
    except Exception as e:
        raise LLMError(f"Perceive phase failed: {str(e)}")


# ──────────────────────────────────────────────
# R — Reason
# ──────────────────────────────────────────────
def reason(perception: dict, target_urls: list[str], time_window: str = "7d") -> dict:
    """Determine scraping strategy and build execution plan."""
    sources = perception.get("source_strategy", ["youtube", "reddit"])
    all_keywords = perception.get("keywords", []) + perception.get("expanded_keywords", [])

    scrape_plan = []

    for url in target_urls:
        source_type = _classify_url(url)
        scrape_plan.append({
            "url": url,
            "source": source_type,
            "keywords": all_keywords,
            "time_window": time_window,
        })

    # If no target URLs or fewer than expected, add keyword-based searches
    if not target_urls:
        for source in sources:
            scrape_plan.append({
                "url": "",
                "source": source,
                "keywords": all_keywords,
                "time_window": time_window,
            })

    return {
        "scrape_plan": scrape_plan,
        "all_keywords": all_keywords,
        "intent": perception.get("intent", "content_ideation"),
    }


def _classify_url(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "reddit.com" in url:
        return "reddit"
    return "generic"


# ──────────────────────────────────────────────
# A — Act
# ──────────────────────────────────────────────
def act(reasoning: dict, num_results: int = 10, category: str = "", prompt: str = "", video_duration: str = "5-7 min") -> dict:
    """Execute scraping, rank results, generate report."""
    source_map = {
        "youtube": YouTubeSource(),
        "reddit": RedditSource(),
        "generic": GenericSource(),
    }

    all_items: list[ContentItem] = []
    errors: list[str] = []

    for task in reasoning["scrape_plan"]:
        source = source_map.get(task["source"], GenericSource())
        try:
            items = source.scrape(
                url=task["url"],
                keywords=task["keywords"],
                time_window=task["time_window"],
            )
            all_items.extend(items)
        except Exception as e:
            errors.append(f"{task['source']}: {str(e)}")

    # Rank
    ranked = rank_items(all_items, reasoning["all_keywords"], num_results)

    # Generate YouTube script
    report = generate_script(
        prompt=prompt,
        keywords=reasoning["all_keywords"],
        intent=reasoning["intent"],
        ranked_items=ranked,
        category=category,
        video_duration=video_duration,
    )

    return {
        "ranked_items": ranked,
        "report_markdown": report,
        "errors": errors,
        "total_scraped": len(all_items),
    }


# ──────────────────────────────────────────────
# T — Track
# ──────────────────────────────────────────────
def track(inputs: dict, perception: dict, results: dict) -> str:
    """Store the full research run to local JSON."""
    record = {
        "inputs": inputs,
        "plan": perception,
        "selected_results": [item.model_dump() for item in results["ranked_items"]],
        "report_markdown": results["report_markdown"],
        "errors": results.get("errors", []),
        "total_scraped": results.get("total_scraped", 0),
    }
    return save_record(record)


# ──────────────────────────────────────────────
# Full Pipeline
# ──────────────────────────────────────────────
def run_pipeline(
    target_urls: list[str],
    prompt: str,
    time_window: str = "7d",
    category: str = "",
    num_results: int = 10,
    video_duration: str = "5-7 min",
) -> dict:
    """Run the full PRAT pipeline."""
    # P — Perceive
    perception = perceive(prompt, target_urls)

    # R — Reason
    reasoning = reason(perception, target_urls, time_window)

    # A — Act
    results = act(reasoning, num_results, category, prompt, video_duration)

    # T — Track
    record_id = track(
        inputs={
            "target_urls": target_urls,
            "prompt": prompt,
            "time_window": time_window,
            "category": category,
            "num_results": num_results,
        },
        perception=perception,
        results=results,
    )

    return {
        "report_markdown": results["report_markdown"],
        "results": [item.model_dump() for item in results["ranked_items"]],
        "stored_record_id": record_id,
        "total_scraped": results["total_scraped"],
        "errors": results.get("errors", []),
    }


# ──────────────────────────────────────────────
# Topics Pipeline (Step 1)
# ──────────────────────────────────────────────
def run_topics_pipeline(
    target_urls: list[str],
    prompt: str,
    category: str = "",
    num_titles: int = 3,
    time_window: str = "7d",
) -> dict:
    """Run P/R/A scraping, then generate a list of topic titles."""
    from app.core.markdown import generate_topics

    topic_prompt = prompt or f"trending {category} content on YouTube"

    # P — Perceive
    perception = perceive(topic_prompt, target_urls)

    # R — Reason
    reasoning = reason(perception, target_urls, time_window)

    # A — Scrape only (no script yet)
    source_map = {
        "youtube": YouTubeSource(),
        "reddit": RedditSource(),
        "generic": GenericSource(),
    }
    all_items: list[ContentItem] = []
    for task in reasoning["scrape_plan"]:
        source = source_map.get(task["source"], GenericSource())
        try:
            items = source.scrape(
                url=task["url"],
                keywords=task["keywords"],
                time_window=task["time_window"],
            )
            all_items.extend(items)
        except Exception:
            pass

    ranked = rank_items(all_items, reasoning["all_keywords"], max(num_titles * 3, 10))

    # Build a research context string from ranked items
    context_lines = []
    for item in ranked:
        eng = ", ".join(f"{k}: {v}" for k, v in item.engagement.items())
        context_lines.append(
            f"- {item.title} [{item.source}] | {eng} | {item.extracted_text[:200]}"
        )
    research_context = "\n".join(context_lines)

    # Generate topic titles
    topics_text = generate_topics(
        prompt=prompt,
        category=category,
        num_titles=num_titles,
        research_context=research_context,
    )

    return {
        "topics": topics_text,
        "context_snapshot": research_context,
        "keywords": reasoning["all_keywords"],
    }


# ──────────────────────────────────────────────
# Script Pipeline (Step 2)
# ──────────────────────────────────────────────
def run_script_pipeline(
    topic: str,
    category: str = "",
    video_duration: str = "5 min",
    broll_enabled: bool = False,
    onscreen_text_enabled: bool = False,
    context_snapshot: str = "",
    original_prompt: str = "",
) -> dict:
    """Generate a full YouTube script for the selected topic and save the record."""
    from app.core.markdown import generate_script

    script = generate_script(
        topic=topic,
        category=category,
        video_duration=video_duration,
        broll_enabled=broll_enabled,
        onscreen_text_enabled=onscreen_text_enabled,
        research_context=context_snapshot,
    )

    record = {
        "inputs": {
            "topic": topic,
            "category": category,
            "video_duration": video_duration,
            "broll_enabled": broll_enabled,
            "onscreen_text_enabled": onscreen_text_enabled,
            "original_prompt": original_prompt,
        },
        "plan": {},
        "selected_results": [],
        "report_markdown": script,
        "errors": [],
        "total_scraped": 0,
    }
    record_id = save_record(record)

    return {
        "script": script,
        "stored_record_id": record_id,
    }

