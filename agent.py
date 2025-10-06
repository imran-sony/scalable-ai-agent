import os
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Tuple, List
from uuid import uuid4
from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq
from models import AnalysisRequest, AnalysisResponse, InputType

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY must be set in .env")

client = Groq(api_key=GROQ_API_KEY)
logger = logging.getLogger(__name__)

class ResearchPaperAnalyzer:
    def __init__(self, max_queue_size: int = 1000, batch_size: int = 3, concurrency_limit: int = 1):
        self.queue: asyncio.Queue[Tuple[str, AnalysisRequest]] = asyncio.Queue(maxsize=max_queue_size)
        self.results: Dict[str, Optional[AnalysisResponse]] = {}
        self.executor = ThreadPoolExecutor(max_workers=concurrency_limit)
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.batch_size = batch_size
        self.task = None

    async def start_worker(self):
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self._worker_loop())
            logger.info("Analyzer worker started.")

    async def _worker_loop(self):
        while True:
            batch = []
            try:
                while len(batch) < self.batch_size:
                    try:
                        batch.append(await asyncio.wait_for(self.queue.get(), timeout=5.0))
                    except asyncio.TimeoutError:
                        break
                if batch:
                    await self._process_batch(batch)
            except Exception as e:
                logger.error(f"Worker loop error: {e}")

    async def _process_batch(self, batch: List[Tuple[str, AnalysisRequest]]):
        async with self.semaphore:
            for task_id, req in batch:
                summary = await self._generate_summary(req)
                self.results[task_id] = AnalysisResponse(
                    task_id=task_id,
                    summary=summary,
                    status="completed"
                )
                logger.info(f"Task {task_id} completed.")

    async def _generate_summary(self, req: AnalysisRequest) -> str:
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": req.prompt or "Summarize the research paper and extract 3 key insights."},
                    {"role": "assistant", "content": req.content}
                ],
                model="llama-3.3-70b-versatile"
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {e}"

    async def enqueue(self, req: AnalysisRequest) -> str:
        task_id = str(uuid4())
        try:
            await self.queue.put((task_id, req))
            self.results[task_id] = None
            logger.info(f"Enqueued task {task_id}")
            return task_id
        except asyncio.QueueFull:
            raise Exception("Queue is full, try again later.")

    def get_result(self, task_id: str) -> Optional[AnalysisResponse]:
        return self.results.get(task_id)

    def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        reader = PdfReader(pdf_bytes)
        return " ".join(page.extract_text() or "" for page in reader.pages)[:5000]  # Limit length

analyzer = ResearchPaperAnalyzer()
