# 🛡️ Sentinel Framework

**Sentinel** is a production-ready, async-first Python framework designed for building "Agentic" AI applications. It bridges the gap between simple LLM scripts and complex, scalable backend systems.

Built on top of **FastAPI** and **Uvicorn**, Sentinel provides a structured "framework" experience (similar to Laravel, Next.js, or Django) specifically tailored for AI Agents.

---

## 📚 Table of Contents

1. [Key Features](#-key-features)
2. [Installation](#-installation)
3. [Quick Start](#-quick-start)
4. [Project Structure](#-project-structure)
5. [CLI Commands](#-cli-commands)
6. [Configuration](#-configuration)
7. [Core Concepts](#-core-concepts)
    - [Agents](#1-agents)
    - [Tools (Function Calling)](#2-tools-function-calling)
    - [Memory (Mem0)](#3-memory-persistent-context)
    - [Workflows (Pipelines)](#4-workflows-orchestration)
    - [Async Queues](#5-async-background-jobs)
8. [Observability & Dashboard](#-observability--dashboard)
9. [Deployment](#-deployment-docker)

---

## 🚀 Key Features

- **⚡ Async-First Core:** Non-blocking I/O ensures your API stays responsive even while LLMs are thinking.
- **🧠 Universal LLM Adapter:** Switch between **Google Gemini**, **OpenAI**, or **Ollama** just by changing a config file.
- **💾 Smart Memory:** Integrated **Mem0** support (Cloud & Local) gives agents long-term memory of user preferences.
- **🔌 Auto-Routing:** File-based routing system. Create a file in `app/http/` and it automatically becomes an API endpoint.
- **🛠️ Tool System:** Turn any Python function into a tool the Agent can "use" (e.g., get_weather, search_db).
- **⛓️ Workflows:** Orchestrate complex tasks by chaining multiple agents together (e.g., Researcher -> Writer -> Editor).
- **👷 Job Queue:** Built-in SQLite-backed background worker for handling long-running tasks without timeouts.
- **📊 Live Dashboard:** Monitor request latency, errors, and agent activity in real-time.

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Install via pip

```bash
pip install sentinel-framework

```

### Install from Source (Development)

```bash
git clone [https://github.com/iamaqdas/sentinel.git](https://github.com/iamaqdas/sentinel.git)
cd sentinel
pip install -e .

```

---

## ⚡ Quick Start

1. **Create a New Project**
Sentinel comes with a CLI tool to scaffold your application structure.

```bash
sentinel new my_agent_app
cd my_agent_app

```

1. **Setup Environment**
Create a `.env` file in the root directory:

```ini
# --- LLM Keys (Choose one) ---
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...

# --- Memory Key (Optional but recommended) ---
# Get free key at [https://mem0.ai](https://mem0.ai)
MEM0_API_KEY=m0-xxx...

```

1. **Run the Server**

```bash
python main.py

```

- **API:** `http://127.0.0.1:8000`
- **Dashboard:** `http://127.0.0.1:8000/dashboard`

---

## 📂 Project Structure

When you run `sentinel new`, the following structure is created. Understanding this is key to using the framework.

```text
my_agent_app/
├── .env                 # API Keys and Secrets (Do not commit to Git)
├── sentinel.yaml        # Main Configuration (LLM model, Memory settings)
├── main.py              # Application Entry Point
├── Dockerfile           # (Generated via CLI) for deployment
│
├── app/                 # YOUR CODE GOES HERE
│   ├── agents/          # Agent Logic definitions (e.g., writer.py, coder.py)
│   ├── http/            # API Routes (Auto-discovered)
│   │   ├── blog_routes.py   # -> /blog_routes/
│   │   └── user_routes.py   # -> /user_routes/
│   ├── workflows/       # Orchestration logic (Chaining agents)
│   └── tools/           # Python functions tools for Agents
│
└── config/              # Advanced configurations (optional)

```

---

## 💻 CLI Commands

Sentinel includes a CLI tool `sentinel` to help you manage your project.

| Command | Description |
| --- | --- |
| `sentinel new <name>` | Scaffolds a completely new Sentinel project in a folder named `<name>`. |
| `sentinel docker` | Generates a production-ready `Dockerfile` and `.dockerignore` in your project root. |
| `sentinel help` | Shows the help menu and available commands. |

---

## ⚙️ Configuration

### `sentinel.yaml`

This file controls the behavior of the framework components.

```yaml
app_name: "My Sentinel App"
version: "1.0.0"
debug: true

# --- Brain (LLM) ---
llm:
  provider: "gemini"  # Options: "openai", "gemini"
  model: "gemini-1.5-flash"
  # Base URL is optional, used for proxies or OpenAI-compatible endpoints
  # base_url: "..."

# --- Memory ---
memory:
  provider: "mem0"
  user_id: "default_user"  # Fallback user ID
  # API Key is read from .env automatically

```

---

## 🧠 Core Concepts

### 1. Agents

Agents are the primary workers. They inherit from `BaseAgent`.

**Example:** `app/agents/writer.py`

```python
from sentinel_core.agents.base import BaseAgent

class ContentWriterAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def _set_system_prompt(self, context_notes=None):
        # Define the personality here
        self.system_prompt = "You are an expert technical writer."
        # Context notes (Memory) are injected automatically if available
        if context_notes:
            self.system_prompt += f"\nUser Context: {context_notes}"
        
        self.history = [{"role": "system", "content": self.system_prompt}]

```

### 2. Tools (Function Calling)

You can give agents "hands" to perform actions. Define a standard Python function and register it.

```python
# 1. Define the function
def get_stock_price(symbol: str):
    """
    Fetches the current stock price for a given symbol (e.g., AAPL).
    """
    return f"The price of {symbol} is $150."

# 2. Register it in your Agent
agent = ContentWriterAgent(name="BrokerBot")
agent.register_tool(get_stock_price)

# 3. Use it
# If the user asks "What is Apple's price?", the Agent will automatically 
# execute get_stock_price("AAPL") and use the result.

```

### 3. Memory (Persistent Context)

Sentinel uses **Mem0** to store user facts. This happens automatically if `memory` is configured in `sentinel.yaml`.

- **Saving:** Every user interaction is saved to the cloud.
- **Retrieving:** Before answering, the Agent searches Memory for relevant context (e.g., "User likes concise answers") and injects it into the prompt.

### 4. Workflows (Orchestration)

Chain multiple agents together for complex tasks.

**Example:** `app/workflows/news_flow.py`

```python
from sentinel_core.workflows.engine import Workflow
from app.agents.researcher import ResearcherAgent
from app.agents.writer import ContentWriterAgent

async def run_pipeline(topic: str):
    # 1. Setup Agents
    researcher = ResearcherAgent(name="Sherlock")
    writer = ContentWriterAgent(name="Shakespeare")

    # 2. Create Flow
    flow = Workflow(name="News Generator")
    
    # 3. Define Steps (Output of Step 1 -> Input of Step 2)
    flow.add_step(researcher) # Finds facts
    flow.add_step(writer)     # Writes article based on facts

    # 4. Run
    return await flow.run(topic)

```

### 5. Async Background Jobs

For tasks that take longer than 30 seconds (e.g., generating a book), use the Queue system to prevent HTTP timeouts.

**Pushing a Job:**

```python
from sentinel_core.services.queue import QueueService

queue = QueueService.get_instance()
job_id = await queue.push({"topic": "Write a book about AI"})

```

*The built-in worker process handles this in the background automatically.*

---

## 📊 Observability & Dashboard

Sentinel includes a built-in Metrics Dashboard.

- **URL:** `http://127.0.0.1:8000/dashboard`
- **Features:**
- Average API Latency.
- Recent Requests log.
- Status Codes (200 vs 500 errors).

---

## 🐳 Deployment (Docker)

1. **Generate Configuration:**

```bash
sentinel docker

```

*(Creates `Dockerfile` & `.dockerignore`)*
2. **Build Image:**

```bash
docker build -t my_sentinel_app .

```

1. **Run Container:**

```bash
docker run -p 8000:8000 --env-file .env my_sentinel_app

```
