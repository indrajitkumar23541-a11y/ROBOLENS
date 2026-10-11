# ROBOLENS 👁️🤖
> **Every Action Teaches AI.**

ROBOLENS is a smartphone-powered robotics training data platform designed to transform real-world human demonstrations into structured, quality-controlled datasets for robotics research and Physical AI development.

---

## 🚀 Key Architectural Pillars

- **📱 Mobile-Only Experience:** Built exclusively with Flutter for Android and iOS. No browser-based product interface or web dashboard.
- **⚡ Asynchronous & Durable Processing:** Long-running media inspection, frame extraction, and PyTorch AI action segmentation run asynchronously via background workers and durable workflow orchestration (Temporal).
- **🔒 Direct-to-Object-Storage Uploads:** Large video recordings are uploaded directly to private S3-compatible storage (MinIO / AWS S3) via short-lived presigned URLs, keeping API servers responsive.
- **🎯 Provenance & Verified Quality:** Clear separation between `AI_GENERATED` candidate annotations and `HUMAN_VERIFIED` review results. Ordinary RGB video limitations are documented transparently.
- **📦 Reproducible Datasets:** Versioned, immutable releases compatible with robotics learning standards (such as LeRobot / RLDS).

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Mobile Application** | Flutter + Dart | Cross-platform Android & iOS contributor experience |
| **Backend API** | Python + FastAPI | REST APIs under `/api/v1`, Auth, Task & Submission lifecycle |
| **Relational Database** | PostgreSQL 16 | Relational business metadata, users, consents, audit trails |
| **Cache & Coordination** | Redis 7 | Rate limiting, session caching, temporary state |
| **Media Storage** | S3 / MinIO | Raw videos, extracted frames, dataset archives |
| **Workflow Engine** | Temporal | Resilient, retryable, long-running processing workflows |
| **Video & AI Processing**| OpenCV, FFmpeg, PyTorch | Video validation, technical metrics, action segmentation |
| **Containers & DevOps** | Docker & Docker Compose | Local reproducible infrastructure and deployments |

---

## 📂 Project Structure

```text
ROBOLENS/
├── Docs/                      # Comprehensive System Architecture, PRD & Specs
│   ├── Architecture/          # System Architecture & Service Communication
│   ├── Backend/               # Database Schema & API Specifications
│   ├── Processing/            # Video & AI Processing Pipeline
│   ├── Infrastructure/        # Deployment & Scaling Architecture
│   └── Security/              # Privacy & Security Guidelines
│
├── infra/                     # Infrastructure configuration
│   ├── docker-compose.yml     # PostgreSQL, Redis, MinIO (with auto-buckets), Temporal
│   └── .env.example           # Environment template
│
├── backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/            # /auth, /tasks, /submissions, /datasets, /health
│   │   ├── core/              # Config, Security (Argon2id + JWT), Database engine
│   │   ├── models/            # SQLAlchemy ORM models (13 tables)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Direct-to-S3 service, Presigned URLs, Verification
│   │   └── main.py            # FastAPI entry point & exception handlers
│   ├── alembic/               # Database migrations (001_initial_schema.py)
│   ├── tests/                 # Pytest automated test suite (100% pass)
│   └── requirements.txt
│
├── workers/                   # AI & Video Processing Workers
│   ├── activities/            # OpenCV video validation, AI action segmentation, Quality gates
│   ├── workflows/             # Video processing pipeline orchestrator
│   └── requirements.txt
│
└── mobile/                    # Flutter Mobile Application
    ├── lib/
    │   ├── core/              # Networking, Token storage, API constants
    │   ├── features/          # Task discovery, Direct S3 streaming upload, Submissions, Profile
    │   └── main.dart          # 4-Tab Contributor Experience UI
    └── pubspec.yaml
```

---

## ⚡ Quickstart

### 1. Start Local Infrastructure
Ensure Docker Desktop is running, then start the backing services:
```bash
docker compose -f infra/docker-compose.yml up -d
```
This spins up:
- **PostgreSQL** at `localhost:5432`
- **Redis** at `localhost:6379`
- **MinIO** at `localhost:9000` (Console at `localhost:9001`)
- **Temporal** at `localhost:7233` (Web UI at `localhost:8233`)

### 2. Run Backend API
```bash
# Activate virtual environment
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate  # Linux/macOS

# Start FastAPI server
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Visit the interactive Swagger API documentation at:  
👉 **http://localhost:8000/api/v1/docs**

### 3. Run Backend Test Suite
```bash
python -m pytest -c backend/pytest.ini backend/tests -v
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
