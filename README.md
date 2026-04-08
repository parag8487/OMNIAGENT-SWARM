<div align="center">

# OmniAgent Swarm

**A Multi-Agent Swarm Intelligence Engine for Predictive Simulation**

[![GitHub Stars](https://img.shields.io/github/stars/parag8487/OMNIAGENT-SWARM?style=flat-square&color=DAA520)](https://github.com/parag8487/OMNIAGENT-SWARM/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/parag8487/OMNIAGENT-SWARM?style=flat-square)](https://github.com/parag8487/OMNIAGENT-SWARM/network)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)

*Upload a document. Describe your prediction. Watch thousands of AI agents simulate the future.*

</div>

---

## Overview

**OmniAgent Swarm** is a next-generation AI prediction engine powered by multi-agent simulation. Given any seed document — a news article, policy draft, financial report, or even a novel — it automatically constructs a high-fidelity parallel digital world populated by thousands of intelligent agents. Each agent has its own personality, memory, and behavioral logic. They interact freely across simulated social media platforms, generating emergent group dynamics that reveal how complex scenarios might unfold.

> **Input:** Upload any document + describe your prediction in natural language.
>
> **Output:** A detailed prediction report + a fully interactive simulated world you can explore.

---

## Key Features

| Feature | Description |
|---|---|
| **GraphRAG Knowledge Extraction** | Automatically builds a knowledge graph from your documents using Zep Cloud, extracting entities, relationships, and temporal memory. |
| **AI-Generated Agent Personas** | LLM generates thousands of unique agents with distinct personalities, backgrounds, MBTI types, and behavioral patterns grounded in your source material. |
| **Dual-Platform Social Simulation** | Runs parallel simulations across Twitter-like and Reddit-like environments using the OASIS engine, modeling posts, likes, reposts, comments, and follows. |
| **ReportAgent with Tool Access** | An intelligent report generation agent uses 4 specialized tools — InsightForge, PanoramaSearch, QuickSearch, and InterviewSubAgent — to produce deep analytical reports. |
| **Deep Interaction Mode** | Chat directly with any simulated individual or the Report Agent. Send surveys to groups of agents to gather collective insights. |
| **Real-Time Graph Updates** | The knowledge graph updates dynamically during simulation, capturing evolving relationships and emerging facts. |

---

## Workflow

```
Document Upload → Graph Build → Environment Setup → Simulation → Report → Interaction
```

1. **Graph Build** — Seed extraction, text chunking, ontology generation, and GraphRAG construction via Zep Cloud.
2. **Environment Setup** — Entity extraction, persona generation, dual-platform config, and initial activation events.
3. **Simulation** — OASIS engine runs parallel Twitter + Reddit simulations with dynamic graph memory updates.
4. **Report Generation** — ReportAgent uses ReACT reasoning with tool calls to produce a structured prediction report.
5. **Deep Interaction** — Chat with any agent in the simulated world, or converse with the Report Agent for follow-up analysis.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vue.js 3, Vite, D3.js (force-directed graph), Vue I18n |
| **Backend** | Flask (Python 3.11+), Pydantic, Gunicorn |
| **LLM** | Google Gemini / OpenAI / Alibaba Qwen (OpenAI SDK compatible) |
| **Knowledge Graph** | Zep Cloud (GraphRAG, temporal memory, entity extraction) |
| **Simulation Engine** | OASIS (Open Agent Social Interaction Simulations) by CAMEL-AI |
| **Deployment** | Docker, Google Cloud Run |

---

## Quick Start

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| **Node.js** | 18+ | `node -v` |
| **Python** | 3.11 – 3.12 | `python --version` |
| **uv** | Latest | `uv --version` |

### 1. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

**Required keys:**

```env
# LLM API (any OpenAI-compatible endpoint)
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL_NAME=gemini-2.5-flash

# OR use Google Gemini directly
GEMINI_API_KEY=your_gemini_key

# Zep Cloud (free tier available at https://app.getzep.com/)
ZEP_API_KEY=your_zep_api_key
```

### 2. Install Dependencies

```bash
# One-command setup (root + frontend + backend)
npm run setup:all
```

Or step by step:

```bash
npm run setup          # Node dependencies (root + frontend)
npm run setup:backend  # Python dependencies (auto-creates venv)
```

### 3. Start Development Server

```bash
npm run dev
```

| Service | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:5001` |

Start individually:

```bash
npm run backend   # Backend only
npm run frontend  # Frontend only
```

### Docker Deployment

```bash
cp .env.example .env
docker compose up -d
```

### Google Cloud Run Deployment

```bash
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

---

## Project Structure

```
OMNIAGENT-SWARM/
├── frontend/                # Vue.js 3 frontend
│   ├── src/
│   │   ├── views/           # Home, MainView, Process pages
│   │   ├── components/      # GraphPanel, Step1-5, LanguageSwitcher
│   │   ├── api/             # Axios API clients
│   │   └── store/           # State management
│   └── public/
├── backend/                 # Flask backend
│   ├── app/
│   │   ├── api/             # REST endpoints (graph, simulation, report)
│   │   ├── services/        # Business logic
│   │   │   ├── ontology_generator.py
│   │   │   ├── graph_builder.py
│   │   │   ├── oasis_profile_generator.py
│   │   │   ├── simulation_config_generator.py
│   │   │   ├── simulation_manager.py
│   │   │   ├── report_agent.py
│   │   │   └── zep_tools.py
│   │   └── utils/           # LLM client, retry, locale, Zep paging
│   └── uploads/             # User uploads & simulation data
├── locales/                 # i18n (en.json, zh.json)
├── scripts/                 # OASIS simulation runner scripts
├── deploy_gcp.sh            # One-command GCP deployment
├── docker-compose.yml       # Docker deployment config
├── Dockerfile               # Container build
└── .env.example             # Environment variable template
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Vue.js Frontend                    │
│  Home ─→ GraphPanel ─→ Step1-5 Components           │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│                  Flask Backend                       │
│  /api/graph/*  │  /api/simulation/*  │  /api/report/*│
├─────────────────────────────────────────────────────┤
│              Service Layer                           │
│  OntologyGen │ GraphBuilder │ SimManager │ ReportAgent│
└──────┬───────────┬──────────────┬───────────┬───────┘
       │           │              │           │
   ┌───▼───┐  ┌────▼────┐  ┌─────▼────┐  ┌───▼────┐
   │  LLM  │  │Zep Cloud│  │  OASIS   │  │ Tools  │
   │Provider│  │(GraphRAG│  │ Engine   │  │InsightF│
   │Gemini/ │  │ Memory) │  │(Twitter/ │  │Panorama│
   │OpenAI  │  │         │  │ Reddit)  │  │Quick/  │
   │        │  │         │  │          │  │Interview│
   └────────┘  └─────────┘  └──────────┘  └────────┘
```

---

## Acknowledgments

OmniAgent Swarm's simulation engine is powered by **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)** by the CAMEL-AI team. We thank them for their open-source contributions.

---

## License

This project is licensed under the [AGPL-3.0 License](LICENSE).