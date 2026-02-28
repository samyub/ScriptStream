from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.core.pipeline import run_pipeline, run_topics_pipeline, run_script_pipeline
from app.core.storage import get_all_records, get_record_by_id
from app.core.errors import ResearchError

router = APIRouter()


# ── Original request model (kept for /api/research backwards compat) ──
class ResearchRequest(BaseModel):
    target_urls: list[str] = Field(default_factory=list)
    prompt: str
    time_window: Optional[str] = "7d"
    category: Optional[str] = ""
    num_results: int = Field(default=10, ge=1, le=20)
    include_debug: bool = False
    video_duration: Optional[str] = "5-7 min"


# ── Step 1: Generate topic titles ──
class TopicsRequest(BaseModel):
    prompt: Optional[str] = ""
    category: Optional[str] = ""
    target_urls: list[str] = Field(default_factory=list)
    num_titles: int = Field(default=3, ge=1, le=5)
    time_window: Optional[str] = "7d"


# ── Step 2: Generate full script ──
class ScriptRequest(BaseModel):
    topic: str
    category: Optional[str] = ""
    video_duration: Optional[str] = "5 min"
    broll_enabled: bool = False
    onscreen_text_enabled: bool = False
    context_snapshot: Optional[str] = ""
    original_prompt: Optional[str] = ""


@router.post("/topics")
async def create_topics(request: TopicsRequest):
    if not request.prompt and not request.category:
        raise HTTPException(status_code=400, detail="Provide a prompt or select a category.")
    try:
        result = run_topics_pipeline(
            target_urls=request.target_urls,
            prompt=request.prompt or "",
            category=request.category or "",
            num_titles=request.num_titles,
            time_window=request.time_window or "7d",
        )
        return result
    except ResearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/script")
async def create_script(request: ScriptRequest):
    try:
        result = run_script_pipeline(
            topic=request.topic,
            category=request.category or "",
            video_duration=request.video_duration or "5 min",
            broll_enabled=request.broll_enabled,
            onscreen_text_enabled=request.onscreen_text_enabled,
            context_snapshot=request.context_snapshot or "",
            original_prompt=request.original_prompt or "",
        )
        return result
    except ResearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/research")
async def create_research(request: ResearchRequest):
    try:
        result = run_pipeline(
            target_urls=request.target_urls,
            prompt=request.prompt,
            time_window=request.time_window or "7d",
            category=request.category or "",
            num_results=request.num_results,
            video_duration=request.video_duration or "5-7 min",
        )

        response = {
            "report_markdown": result["report_markdown"],
            "results": result["results"],
            "stored_record_id": result["stored_record_id"],
        }

        if request.include_debug:
            response["total_scraped"] = result["total_scraped"]
            response["errors"] = result["errors"]

        return response

    except ResearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/history")
async def get_history():
    records = get_all_records()
    summaries = []
    for r in records:
        summaries.append({
            "id": r.get("id"),
            "created_at": r.get("created_at"),
            "prompt": r.get("inputs", {}).get("prompt") or r.get("inputs", {}).get("topic", ""),
            "category": r.get("inputs", {}).get("category", ""),
            "num_results": len(r.get("selected_results", [])),
            "total_scraped": r.get("total_scraped", 0),
        })
    return {"history": list(reversed(summaries))}


@router.get("/history/{record_id}")
async def get_history_detail(record_id: str):
    record = get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Research record not found")
    return record



@router.post("/research")
async def create_research(request: ResearchRequest):
    try:
        result = run_pipeline(
            target_urls=request.target_urls,
            prompt=request.prompt,
            time_window=request.time_window or "7d",
            category=request.category or "",
            num_results=request.num_results,
            video_duration=request.video_duration or "5-7 min",
        )

        response = {
            "report_markdown": result["report_markdown"],
            "results": result["results"],
            "stored_record_id": result["stored_record_id"],
        }

        if request.include_debug:
            response["total_scraped"] = result["total_scraped"]
            response["errors"] = result["errors"]

        return response

    except ResearchError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/history")
async def get_history():
    records = get_all_records()
    # Return summaries only (without full markdown for list view)
    summaries = []
    for r in records:
        summaries.append({
            "id": r.get("id"),
            "created_at": r.get("created_at"),
            "prompt": r.get("inputs", {}).get("prompt", ""),
            "category": r.get("inputs", {}).get("category", ""),
            "num_results": len(r.get("selected_results", [])),
            "total_scraped": r.get("total_scraped", 0),
        })
    return {"history": list(reversed(summaries))}


@router.get("/history/{record_id}")
async def get_history_detail(record_id: str):
    record = get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Research record not found")
    return record
