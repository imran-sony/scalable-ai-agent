import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Depends,
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from models import AnalysisRequest, AnalysisResponse, InputType
from agent import analyzer, ResearchPaperAnalyzer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="AI Research Paper Analyzer")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_analyzer():
    if analyzer.task is None or analyzer.task.done():
        await analyzer.start_worker()
    return analyzer

@app.on_event("startup")
async def startup_event():
    await analyzer.start_worker()
    logger.info("Worker started")

@app.post("/analyze/file")
@limiter.limit("10/minute")
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    prompt: Optional[str] = None,
    analyzer_dep: ResearchPaperAnalyzer = Depends(get_analyzer)
):
    if not file or file.content_type != "application/pdf":
        raise HTTPException(400, "Provide a PDF file with 'application/pdf' content type.")

    req = AnalysisRequest(
        input_type=InputType.PDF,
        prompt=prompt or "Summarize the research paper and extract 3 key insights.",
        content=analyzer_dep.extract_pdf_text(await file.read())
    )

    try:
        task_id = await analyzer_dep.enqueue(req)
        logger.info(f"PDF analysis task queued: {task_id}")
        return {"task_id": task_id, "status": "queued"}
    except Exception as e:
        logger.exception("Error enqueueing PDF analysis")
        raise HTTPException(503, str(e))

@app.post("/analyze/text")
@limiter.limit("10/minute")
async def analyze_text(
    request: Request,
    content: str,
    prompt: Optional[str] = None,
    analyzer_dep: ResearchPaperAnalyzer = Depends(get_analyzer)
):
    if not content:
        raise HTTPException(400, "Provide text content for analysis.")

    req = AnalysisRequest(
        input_type=InputType.TEXT,
        prompt=prompt or "Summarize the text and extract 3 key insights.",
        content=content
    )

    try:
        task_id = await analyzer_dep.enqueue(req)
        logger.info(f"Text analysis task queued: {task_id}")
        return {"task_id": task_id, "status": "queued"}
    except Exception as e:
        logger.exception("Error enqueueing text analysis")
        raise HTTPException(503, str(e))

@app.get("/result/{task_id}", response_model=AnalysisResponse)
async def get_result(
    task_id: str,
    analyzer_dep: ResearchPaperAnalyzer = Depends(get_analyzer),
):
    result = analyzer_dep.get_result(task_id)
    if result is None:
        raise HTTPException(404, "Result not ready or not found.")
    logger.info(f"Result fetched: {task_id}")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
