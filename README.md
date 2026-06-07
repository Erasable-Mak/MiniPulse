# MiniPulse: Agentic CRM Orchestration

MiniPulse is an enterprise-grade, asynchronous AI orchestration platform designed to seamlessly bridge Slack events and HubSpot CRM capabilities. Engineered with a decoupled microservice architecture, it leverages advanced large language models (LLMs) to provide real-time, agentic CRM insights directly within Slack workspaces.

## Architectural Overview

The system is built on a decoupled, multi-service architecture utilizing FastAPI, containerized via Docker Compose. The separation of concerns ensures high availability, independent scaling, and strict fault isolation.

### System Architecture

```mermaid
graph TD
    subgraph Slack Ecosystem
        User[Slack User]
        Workspace[Slack API / Events]
    end

    subgraph "MiniPulse Microservices (Docker Compose)"
        Adapter[Slack Adapter<br/>Port 3000]
        AI[AI Service<br/>Port 8000]
    end

    subgraph External APIs
        Groq[Groq API<br/>llama-3.1-8b-instant]
        HubSpot[HubSpot API<br/>CRM Data]
    end

    User -- "@MiniPulse" --> Workspace
    Workspace -- "Webhook Event (HMAC Secured)" --> Adapter
    Adapter -. "Sync 200 OK (< 3s)" .-> Workspace
    Adapter -- "Async Task Hand-off" --> AI
    
    AI <-->|Chat Context & Function Calling| Groq
    AI <-->|CRM Search & Metrics| HubSpot
    
    AI -- "Final Answer" --> Adapter
    Adapter -- "chat.postMessage" --> Workspace
```

### Execution Flow

```mermaid
sequenceDiagram
    participant U as Slack User
    participant S as Slack API
    participant SA as Slack Adapter
    participant AI as AI Service
    participant LLM as Groq LLM
    participant CRM as HubSpot CRM

    U->>S: @MiniPulse "How many qualified deals?"
    S->>SA: Webhook Event (POST /slack/events)
    Note over SA: Validates HMAC-SHA256 Signature
    SA-->>S: 200 OK (Instant Acknowledgment)
    
    SA-)AI: Async Task: POST /api/query
    
    activate AI
    AI->>LLM: Chat Completion Request + Tools
    LLM-->>AI: Tool Call (count_deals_by_stage)
    
    AI->>CRM: Search API (Filters: dealstage=qualifiedtobuy)
    CRM-->>AI: Aggregated Deals Response
    
    AI->>LLM: Tool Result (count=5, total=$50k)
    LLM-->>AI: Natural Language Answer
    deactivate AI
    
    AI-)SA: Forward Slack Response Payload
    SA->>S: chat.postMessage API Call
    S->>U: "You have 5 qualified deals worth $50,000."
```

### Project Structure

```text
MiniPulse/
├── docker-compose.yml       # Multi-container orchestration
├── .env.example             # Environment variable template
├── services/
│   ├── ai-service/          # Core intelligence engine (Port 8000)
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── ai_enums.py
│   │       ├── config.py
│   │       ├── logging.py
│   │       ├── main.py
│   │       ├── memory.py
│   │       ├── models.py
│   │       ├── orchestrator.py
│   │       ├── clients/     # HubSpot API integrations
│   │       │   ├── __init__.py
│   │       │   └── hubspot.py
│   │       └── tools/       # Tool-calling definitions
│   │           ├── __init__.py
│   │           ├── contacts.py
│   │           ├── deals.py
│   │           └── registry.py
│   └── slack-adapter/       # Edge-facing API gateway (Port 3000)
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── app/
│           ├── __init__.py
│           ├── config.py
│           ├── logging.py
│           ├── main.py
│           ├── slack_enums.py
│           ├── handlers/    # Slack event dispatching
│           │   └── events.py
│           └── middleware/  # Cryptographic signature validation
│               └── signature.py
└── tests/                   # Pytest test suites
    ├── __init__.py
    ├── conftest.py
    ├── ai_service/
    │   ├── __init__.py
    │   ├── test_thread_memory.py
    │   └── test_tools.py
    └── slack_adapter/
        └── test_signature.py
```

### 1. Decoupled Microservices
- **Slack Adapter (`minipulse-slack-adapter-1` | Port 3000)**: A lightweight, edge-facing API gateway responsible for securely ingesting Slack events, validating cryptographic signatures, and managing the asynchronous handoff to the AI backend.
- **AI Backend Service (`minipulse-ai-service-1` | Port 8000)**: The core intelligence engine. It orchestrates the LLM tool-calling loop, manages conversational thread memory, and interfaces directly with the HubSpot CRM APIs.

### 2. Webhook Concurrency & Asynchronicity
Slack mandates a strict 3-second response deadline for all webhooks. To meet this SLA and prevent retry storms, the Slack Adapter employs immediate synchronous acknowledgment. Upon receiving a valid event payload, the adapter immediately returns an HTTP `200 OK` while concurrently offloading the heavy lifting (LLM inference and CRM lookups) to an `asyncio` background task.

### 3. Security Instincts: Cryptographic Verification
Zero-trust security is implemented at the edge. The Slack Adapter strictly validates all incoming webhook traffic using HMAC-SHA256 signature verification.
- Validates the `X-Slack-Signature` against the computed HMAC digest using the configured Slack Signing Secret.
- Inspects the `X-Slack-Request-Timestamp` to mitigate replay attacks, aggressively rejecting any payload older than the configured 5-minute threshold.

### 4. Agentic LLM Orchestration
Powered by the `llama-3.1-8b-instant` model hosted on Groq (chosen because Groq offers free API usage), the AI Service operates as an autonomous agent. The architecture is model-agnostic and can easily be configured to use the `Anthropic Claude API` instead.
- **Thread Memory**: Contextual awareness is maintained via a thread-safe, in-memory store utilizing TTL expirations and FIFO queue evictions (`max_messages`), ensuring multi-turn conversational consistency.
- **Guardrails**: Strict system prompts establish rigid operational boundaries, explicitly deflecting out-of-scope requests (e.g., general knowledge, weather) and enforcing professional, CRM-focused behavior.

### 5. Tool-Calling Architecture
The orchestrator dynamically maps user intent to execute registered HubSpot tools. Execution flows asynchronously through predefined schemas:
- `search_deals`: Queries active deals by name, minimum amount, and stage parameters.
- `count_deals_by_stage`: Aggregates active deals based on internal enum-mapped stage representations.
- `get_recent_deals_closed`: Retrieves pipeline wins bounded by a temporal 30-day cutoff.
- `get_contact_by_email`: Performs exact-match CRM contact resolution.

### 6. Observability & Tracing
Operational visibility is treated as a first-class citizen via structured JSON logging powered by `structlog` across all microservices. Log payloads consistently inject contextual metadata-including `request_id`, `thread_ts`, `tool_name`, `duration_ms`, and execution statuses-enabling deterministic debugging and log aggregation.

---

## Environment Setup & Deployment

The repository utilizes Docker Compose for deterministic local execution. 

### Prerequisites
- Docker & Docker Desktop
- ngrok (for local webhook exposure)
- A configured `.env` file in the project root containing required secrets:
  ```env
  SLACK_BOT_TOKEN=xoxb-your-bot-token
  SLACK_SIGNING_SECRET=your-signing-secret
  # Groq provides free API access, but you can swap to Claude API if preferred
  GROQ_API_KEY=gsk_your_actual_key
  HUBSPOT_ACCESS_TOKEN=pat-your-access-token
  AI_SERVICE_URL=http://ai-service:8000
  ```

### 1. Build and Run the Microservices

Execute the following PowerShell command to build and detach the containerized stack:

```powershell
docker-compose -f D:\Project_Assesments\MiniPulse\docker-compose.yml up -d --build
```

### 2. Expose the Webhook via ngrok

To route live Slack events to your local adapter running on port 3000, start an ngrok tunnel from your executable directory:

```powershell
.\ngrok.exe http 3000
```

*Configure your Slack App's Event Subscriptions Request URL to use the generated ngrok HTTPS domain appended with `/slack/events` (e.g., `https://your-url.ngrok-free.app/slack/events`).*

---

## Local Development (pyenv / venv)

If you prefer to run or test the services locally without Docker, you can use `pyenv` and standard Python virtual environments.

1. **Ensure Python 3.11.9 is installed**:
   ```powershell
   pyenv install 3.11.9
   pyenv local 3.11.9
   python --version
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -e ./services/ai-service
   pip install -e ./services/slack-adapter
   pip install pytest pytest-asyncio httpx respx
   ```

4. **Run the services locally**:
   In terminal 1 (AI Service):
   ```powershell
   cd services\ai-service
   uvicorn app.main:app --port 8000 --reload
   ```
   In terminal 2 (Slack Adapter):
   ```powershell
   cd services\slack-adapter
   uvicorn app.main:app --port 3000 --reload
   ```

---

## Testing & Verification

To verify container cross-communication, tool schema parsing, and mock logic, execute the unit testing suites within the containers:

```powershell
# Run tests for the Slack Adapter service
docker compose -f D:\Project_Assesments\MiniPulse\docker-compose.yml exec slack-adapter pytest

# Run tests for the AI Backend engine
docker compose -f D:\Project_Assesments\MiniPulse\docker-compose.yml exec ai-service pytest
```
