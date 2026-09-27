# StaffPulse: Enterprise Employee Management System & CI/CD Pipeline

A production-grade, high-performance **Employee Management System** built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL/SQLite**, backed by a complete **end-to-end CI/CD pipeline** covering:
Git Commit → Automated Testing → SAST & Dependency Audits → Semantic Versioned Docker Artifacts → Trivy Container Scan → Kubernetes Deployment → Liveness/Readiness Probes & Prometheus Observability.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Developer / Git Push    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                        GitHub Actions Pipeline                         │
    ├───────────────────┬───────────────────┬────────────────────────────────┤
    │  1. Test & Style  │   2. Security     │  3. Build & Scan               │
    │  - ruff check     │   - bandit (SAST) │  - Semantic Version Tag        │
    │  - pytest --cov   │   - pip-audit     │  - Docker Build                │
    │  - Upload Report  │   - Dependency CVE│  - Trivy Scan (CRITICAL/HIGH)  │
    │                   │                   │  - Push to GHCR                │
    └───────────────────┴───────────────────┴───────────────┬────────────────┘
                                                            │
                                                            ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │  4. Kubernetes Deployment & Verification                               │
    │  - Spin up KIND cluster                                                │
    │  - Apply k8s manifests (Namespace, Secrets, PVC, Deployments, HPA)     │
    │  - Rollout status verification                                         │
    │  - Health checks: /health (Liveness) & /health/ready (Readiness)       │
    │  - Prometheus metrics validation: /metrics                             │
    └────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

- **FastAPI Core**: Async-capable, auto-generating OpenAPI Swagger docs at `/docs` and ReDoc at `/redoc`.
- **JWT Authentication & RBAC**:
  - Secure bcrypt password hashing.
  - JSON Web Tokens (JWT) with standard expiration and algorithm configurations.
  - **Role-Based Access Control**:
    - **Admin**: Full CRUD permissions (Create, Read, Update, Delete) + User management. The first registered user automatically becomes Admin.
    - **User**: Read-only directory access and statistical summaries.
- **Employee CRUD Engine**:
  - Full Name, Corporate Email, Department, Job Position, Salary, Phone Number, and Employment Status (`active`, `on_leave`, `terminated`).
  - Search filtering by name, email, position, and department.
  - Paginated retrieval and summary analytics (`/employees/stats/summary`).
- **Modern Responsive Web UI**:
  - Built-in dark glassmorphic dashboard served directly at `/`.
  - Dynamic KPI cards (Total Employees, Active %, Total Payroll, Average Salary, DB ping latency).
  - Search & filter toolbar, interactive Add/Edit modals, and live Observability viewer.
- **Monitoring & Observability**:
  - `/metrics` Prometheus endpoint exposing latency histograms, request counters, and process metrics via `prometheus-fastapi-instrumentator`.
  - Pre-configured `prometheus.yml` scrape configuration and Prometheus alert rules (`monitoring/alerts.yml`).
  - Pre-built Grafana dashboard JSON (`monitoring/grafana/dashboards/ems-dashboard.json`).
- **Kubernetes Probes**:
  - `/health` (Liveness): Validates FastAPI process responsiveness.
  - `/health/ready` (Readiness): Validates active database query execution before routing network traffic.
- **Enterprise Security Validation**:
  - **SAST**: `bandit` static security scanner.
  - **Dependency Audit**: `pip-audit` CVE database scanner.
  - **Container Security**: `trivy` container scanning for CRITICAL/HIGH CVEs in CI.
  - **Non-root Container User**: `appuser` (UID 1000).
  - **Security Headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.

---

## Directory Structure

```
├── .github/workflows/
│   └── ci-cd.yml                # End-to-end GitHub Actions pipeline
├── app/
│   ├── routers/
│   │   ├── auth.py              # Register, Login, Me, User management
│   │   ├── employees.py         # CRUD, filtering, search, analytics
│   │   └── health.py            # /health (Liveness) & /health/ready (Readiness)
│   ├── config.py                # 12-factor Pydantic settings
│   ├── database.py              # SQLAlchemy engine & session management
│   ├── dependencies.py          # Auth & DB dependency injection
│   ├── main.py                  # FastAPI app entrypoint, middleware, static files
│   ├── models.py                # User & Employee SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic v2 schemas and validators
│   └── security.py              # Bcrypt hashing & JWT utilities
├── k8s/
│   ├── namespace.yaml           # ems namespace
│   ├── postgres.yaml            # Postgres Secret, PVC, Deployment, Service
│   ├── app.yaml                 # EMS Deployment (2 replicas), Secret, Service
│   ├── ingress.yaml             # Ingress definition with path routing
│   └── hpa.yaml                 # HorizontalPodAutoscaler (CPU & Memory)
├── monitoring/
│   ├── alerts.yml               # Prometheus alert definitions
│   ├── prometheus.yml           # Prometheus scrape job configuration
│   └── grafana/                 # Automated datasource & dashboard provisioning
├── static/
│   ├── app.js                   # Client-side state, CRUD, & health polling
│   ├── index.html               # Single-page dashboard interface
│   └── style.css                # Glassmorphic dark UI design system
├── tests/
│   ├── conftest.py              # TestClient, in-memory SQLite isolation, fixtures
│   ├── test_auth.py             # Authentication & RBAC unit tests
│   ├── test_employees.py        # CRUD, validation, search & stats tests
│   ├── test_health.py           # Liveness/Readiness probe tests
│   └── test_metrics.py          # Prometheus exposition tests
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml           # App + PostgreSQL + Prometheus + Grafana
├── Dockerfile                   # Hardened multi-layer image with non-root user
├── pyproject.toml               # Ruff, pytest, and coverage configurations
├── requirements.txt             # Pinned production runtime dependencies
└── requirements-dev.txt         # Dev, test, and security tooling
```

---

## Local Development & Setup

### 1. Direct Python Run (Fastest)

```bash
# 1. Clone repository and install dependencies
pip install -r requirements-dev.txt

# 2. Configure environment (defaults to local SQLite)
cp .env.example .env

# 3. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Web Dashboard**: Open `http://localhost:8000`
- **Interactive Swagger Docs**: Open `http://localhost:8000/docs`
- **Prometheus Metrics**: Open `http://localhost:8000/metrics`
- **Health Check**: Open `http://localhost:8000/health`

### 2. Full Stack with Docker Compose (App + Postgres + Prometheus + Grafana)

```bash
docker compose up --build
```

Access services:
- **StaffPulse Web App**: `http://localhost:8000`
- **Prometheus UI**: `http://localhost:9090`
- **Grafana Dashboards**: `http://localhost:3000` (User: `admin` / Password: `admin`)

---

## Automated Testing & Security Verification

Run all test and security validation suites locally:

```bash
# 1. Run all unit & integration tests with coverage report
pytest --cov=app --cov-report=term-missing

# 2. Code formatting and linting
ruff check .

# 3. Static Application Security Testing (SAST)
bandit -r app

# 4. Dependency Vulnerability Audit
pip-audit -r requirements.txt
```

---

## Kubernetes Deployment Guide

Deploy manually to any standard Kubernetes cluster (Minikube, KIND, EKS, GKE, AKS):

```bash
# 1. Create Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Deploy PostgreSQL Database with PVC
kubectl apply -f k8s/postgres.yaml

# 3. Deploy StaffPulse Application
kubectl apply -f k8s/app.yaml

# 4. Deploy Ingress and Autoscaler
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# 5. Check Deployment Status
kubectl get pods -n ems -w

# 6. Access via Port-Forwarding
kubectl port-forward svc/ems-service 8080:80 -n ems
# Open http://localhost:8080 in your browser
```

---

## CI/CD Pipeline Breakdown

The workflow in `.github/workflows/ci-cd.yml` runs automatically on pushes and PRs:

1. **Lint & Test**:
   - Executes `ruff check .` for style and code sanity.
   - Runs `pytest --cov=app` achieving **>90% test coverage**.
   - Generates and uploads `coverage.xml` as a pipeline artifact.
2. **Security Validation**:
   - Runs `bandit` to identify code-level vulnerabilities (hardcoded credentials, unsafe bindings, etc.).
   - Runs `pip-audit` against the Python PyPI vulnerability database.
3. **Build, Scan & Version Artifact**:
   - Calculates a semantic version: `v1.0.<RUN_NUMBER>-<SHORT_SHA>`.
   - Builds container image using Buildx.
   - Executes **Trivy Container Scan** to block any builds containing `CRITICAL` or `HIGH` OS/library vulnerabilities.
   - Authenticates to **GHCR (GitHub Container Registry)** and pushes the versioned image and `latest` tag.
4. **Kubernetes Rollout & Verification**:
   - Spins up an ephemeral KIND Kubernetes cluster.
   - Loads the versioned image directly into the cluster.
   - Applies the manifests and watches rollout until all pods are ready.
   - Automatically probes `/health`, `/health/ready`, and verifies `/metrics` before marking the pipeline as passed.
