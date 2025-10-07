# 📄 Scalable AI Research Paper Analyzer
A scalable AI-powered system that analyzes research papers (PDF or text) and generates summaries with key insights using the Groq LLM. Built with FastAPI, this project supports queued processing, concurrency control, and rate-limiting to handle high-demand analysis workloads.

---

## 📜 Features  

✅ PDF & text analysis  
✅ Automatic summarization with key insights extraction  
✅ Task queue & concurrency control  
✅ Rate limiting to prevent overload  
✅ Extensible & modular architecture

---

## ⚙️ Project Structure

├── agent.py               # Background processing & Groq LLM integration  
├── main.py                # FastAPI app entry point  
├── models.py              # Pydantic models for request/response  
├── requirements.txt       # Project dependencies  
├── .env                   # Environment variables  
├── README.md              # Project documentation  

---

## 📦 Installation
### 1. Clone the repository  

git clone https://github.com/imran-sony/scalable-ai-agent.git  
cd scalable-ai-agent

### 2. Create and activate a virtual environment  

python -m venv .venv  
.venv\Scripts\activate

### 3. Install dependencies  

pip install -r requirements.txt  

### 4. Create .env file  

GROQ_API_KEY=your_groq_api_key  
MAX_QUEUE_SIZE=1000   # Maximum number of pending tasks  
BATCH_SIZE=3  # Number of tasks processed at once  
CONCURRENCY_LIMIT=1  # Maximum concurrent workers  

---

## 🚀 Running the Server  

uvicorn main:app --reload
Server runs at:
http://127.0.0.1:8000
