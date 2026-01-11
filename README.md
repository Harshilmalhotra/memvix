# Memvix

**Memvix** is a powerful, intelligent Telegram reminder bot designed to handle natural language queries, manage recurring reminders, and provide a seamless user experience. It leverages advanced NLP for date/time extraction and robust background processing for reliable notification delivery.

## 🚀 Features

*   **Natural Language Processing**: Understands complex date and time queries (e.g., "Remind me to call mom in 10 minutes", "Meeting every Monday at 10am") using [Rasa Duckling](https://github.com/facebook/duckling).
*   **Reliable Scheduling**: Uses a dedicated worker process and Redis/PostgreSQL to ensure reminders are delivered on time.
*   **Voice & Text Support**: (Implied by `DEEPGRAM_API_KEY`) Support for voice notes transcription and processing.
*   **Scalable Architecture**: Dockerized services for easy deployment and scaling.
*   **Automated CI/CD**: Seamless deployment pipeline using GitHub Actions.

## 🏗 Architecture

The system is built as a microservices-style architecture orchestrated with Docker Compose.

```mermaid
graph TD
    User((User)) <-->|Telegram| TG[Telegram Servers]
    TG <-->|Webhook| Ingress[Ingress/Ngrok]
    Ingress --> API[FastAPI Server]
    
    subgraph Core Services
        API <--> DB[(PostgreSQL)]
        API <--> Cache[(Redis)]
        API <--> NLP[Duckling NLP]
    end
    
    subgraph Admin Implementation
        Admin((Admin)) -->|Browser| API
        API -->|Render| MissionControl[HTML Dashboard]
        API -->|Broadcast| BroadcastTask[Background Broadcast]
    end
    
    subgraph Background Processing
        Worker[Reminder Worker] <--> DB
        Worker <--> Cache
        Worker -->|Send Message| TG
        BroadcastTask -->|Send Message| TG
    end
```

### Components

*   **API (FastAPI)**: Handles incoming webhooks from Telegram, processes user messages, and manages state.
*   **Worker**: A background process that polls/consumes scheduled tasks and sends out reminders when due.
*   **PostgreSQL**: Persistent storage for users, reminders, and transaction logs.
*   **Redis**: Caching layer and message broker for task queues.
*   **Duckling**: A Haskell-based parsing service for extracting structured data.
*   **Admin Dashboard (Mission Control)**: A web interface for tracking stats and broadcasting messages.
*   **Ngrok** (Local Dev): Tunnels localhost to the public internet.

## 📡 API Documentation

Access the interactive Swagger UI at: [http://localhost:8000/docs#/](http://localhost:8000/docs#/)

### Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| **GET** | `/admin/mission-control` | **Mission Control**: Web dashboard for stats & user tracking. |
| **GET** | `/admin/stats` | **Get Stats**: JSON response of total and active users. |
| **POST** | `/admin/broadcast` | **Broadcast Message**: Send a message to all users. payload: `{"message": "..."}` |
| **GET** | `/health` | **Health Check**: Service status. |

### Schemas

*   `HTTPValidationError`: Standard validation error response.
*   `ValidationError`: Details of the validation error.

## 🚇 Ngrok Status

When running locally with Docker, you can inspect the tunnel status and traffic.

*   **Dashboard**: [http://localhost:4040/status](http://localhost:4040/status)
*   **Get Public URL**:
    ```bash
    curl http://localhost:4040/api/tunnels | jq
    ```

## 🛠 Tech Stack

*   **Language**: Python 3.10+
*   **Framework**: FastAPI
*   **Database**: PostgreSQL 15
*   **Cache**: Redis 7
*   **NLP**: Rasa Duckling
*   **Containerization**: Docker & Docker Compose
*   **Deployment**: GitHub Actions, Oracle VM (Ubuntu)

## 🏁 Getting Started

### Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) & Docker Compose
*   Python 3.10+ (for local development without Docker)
*   A Telegram Bot Token (Get it from [@BotFather](https://t.me/BotFather))

### Configuration

Create a `.env` file in the root directory. You can copy `.env.example`:

```bash
cp .env.example .env
```

**Required Variables:**

```ini
APP_ENV=dev
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://remindz:remindz@postgres:5432/remindz
# Optional
DEEPGRAM_API_KEY=your_key
GEMINI_API_KEY=your_key
```

> **Note**: The project supports environment-specific overrides via `.env.local` and `.env.prod`.

### 💻 Local Deployment

#### Option 1: Full Docker (Recommended)

Run the entire stack with a single command. This includes the database, redis, API, worker, and ngrok.

```bash
# Build and start services
docker compose up --build
```

The system will:
1.  Start Postgres & Redis.
2.  Initialize the database (`db-init`).
3.  Start Ngrok and set up the Telegram Webhook (`webhook-init`).
4.  Start the API and Worker.

#### Option 2: Hybrid (Local Python + Docker for Infra)

If you want to debug Python code locally while keeping dependencies containerized.

1.  **Start Infrastructure**:
    ```bash
    docker compose -f docker-compose.infra.yml up -d
    ```

2.  **Start API**:
    ```bash
    # Ensure dependencies are installed
    pip install -r requirements.txt
    
    uvicorn app.main:app --reload
    ```

3.  **Start Worker**:
    ```bash
    python -m app.workers.reminder_worker
    ```

4.  **Setup Webhook** (if API is public/ngrok):
    ```bash
    python scripts/set_webhook.py
    ```

## ☁️ Deployment (Oracle VM)

This guide assumes you are deploying to an Oracle Cloud VM (e.g., Ubuntu/Oracle Linux), but applies to any VPS.

### 1. Server Setup

SSH into your Oracle VM instance:
```bash
ssh ubuntu@your-oracle-ip
```

**Install Dependencies:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER && newgrp docker

# Install Git
sudo apt install git -y
```

**Clone Repository:**
```bash
mkdir -p /home/ubuntu/memvix
git clone https://github.com/Harshilmalhotra/memvix.git /home/ubuntu/memvix
```

**Setup Secrets:**
Create the `.env` file on the server:
```bash
cd /home/ubuntu/memvix
nano .env
# Paste your production variables (APP_ENV=prod, etc.)
```

### 2. CI/CD Pipeline (GitHub Actions)

The project includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that automatically deploys changes when you push to `main`.

**Required GitHub Secrets:**
Go to your Repository Settings > Secrets and Variables > Actions > New Repository Secret.

| Secret Name | Description |
| :--- | :--- |
| `SSH_HOST` | The public IP of your Oracle VM |
| `SSH_USERNAME` | The SSH username (e.g., `ubuntu` or `opc`) |
| `SSH_KEY` | Your private SSH key (OpenSSH format). Ensure the public key is in `~/.ssh/authorized_keys` on the server. |
| `PROJECT_PATH` | Path to the repo on server, e.g., `/home/ubuntu/memvix` |

**Workflow Process:**
1.  Code is pushed to `main`.
2.  GitHub Action connects to your server via SSH.
3.  Pulls the latest code.
4.  Sets `APP_ENV=prod`.
5.  Rebuilds and restarts the Docker containers.

### 3. Manual Deployment (Fallback)

If you need to deploy manually without the CI/CD pipeline:

```bash
cd /home/ubuntu/memvix
git pull origin main
export APP_ENV=prod
docker compose -f docker-compose.yml up -d --build --remove-orphans
```

---

## 📜 License

[MIT License](LICENSE)
