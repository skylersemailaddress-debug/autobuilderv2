from __future__ import annotations

import json
from dataclasses import dataclass

from ir.model import AppIR


@dataclass(frozen=True)
class GeneratedTemplate:
    path: str
    content: str


def _json_pretty(payload: dict[str, object]) -> str:
  return f"{json.dumps(payload, indent=2, sort_keys=True)}\n"


def _frontend_package_json() -> str:
    return _json_pretty(
        {
            "name": "frontend",
            "private": True,
            "version": "0.1.0",
            "scripts": {
                "dev": "next dev -p 3000",
                "build": "next build",
                "start": "next start -p 3000",
                "test:shell": "node tests/shell-check.js",
            },
            "dependencies": {
                "next": "14.2.5",
                "react": "18.3.1",
                "react-dom": "18.3.1",
            },
        }
    )


def _frontend_tsconfig_json() -> str:
    return _json_pretty(
        {
            "compilerOptions": {
                "target": "ES2020",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": False,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
            "exclude": ["node_modules"],
        }
    )


def _frontend_status_seed(ir: AppIR) -> str:
    return _json_pretty(
        {
            "appIdentity": ir.app_identity,
            "status": "idle",
            "lastCommand": "",
            "lastResponse": "Ready",
            "surface": "workspace",
        }
    )


def _frontend_shell_page(ir: AppIR) -> str:
    return f'''"use client";

import {{ useState }} from "react";
import {{ EnterpriseShell }} from "../components/enterprise-shell";
import {{ EnterpriseStatePanel }} from "../components/enterprise-states";

type ApiResponse = {{
  status: string;
  data?: {{
    command?: string;
    result?: string;
  }};
  error?: {{
    code: string;
    message: string;
  }};
  command: string;
  result: string;
}};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function HomePage() {{
  const [command, setCommand] = useState("");
  const [status, setStatus] = useState("idle");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function runCommand() {{
    const normalized = command.trim();
    if (!normalized) {{
      setStatus("empty");
      setResponse("");
      return;
    }}

    setIsLoading(true);
    setStatus("processing");
    setResponse("Contacting backend...");

    try {{
      const res = await fetch(`${{API_BASE}}/api/workspace/execute`, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ command: normalized }}),
      }});

      if (!res.ok) {{
        throw new Error(`API request failed with status ${{res.status}}`);
      }}

      const payload = (await res.json()) as ApiResponse;
      setStatus(payload.status);
      setResponse(payload.data?.result ?? payload.result ?? "No response payload");
    }} catch (error) {{
      const message = error instanceof Error ? error.message : "Unknown error";
      setStatus("error");
      setResponse(message);
    }} finally {{
      setIsLoading(false);
    }}
  }}

  return (
    <div data-testid="workspace-shell">
      <EnterpriseShell
        appTitle="{ir.app_identity}"
        shellNote="Commercial workspace shell with deterministic enterprise UX states."
        statusLabel={{isLoading ? "processing" : status}}
      >
        <section className="command-panel" data-testid="command-surface">
          <label htmlFor="command-input">Command</label>
          <div className="command-row">
            <input
              id="command-input"
              value={{command}}
              onChange={{(event) => setCommand(event.target.value)}}
              placeholder="Type a command for backend execution"
            />
            <button type="button" onClick={{runCommand}}>
              Execute
            </button>
          </div>
          <p className="hint">Use settings/admin/activity routes for operator workflows.</p>
        </section>

        <section className="work-surface" data-testid="main-surface">
          <h2>Work Surface</h2>
          <p>Primary content area for task output, records, and operator-facing tools.</p>
          <div data-testid="response-state-region">
            <EnterpriseStatePanel
              state={{isLoading ? "loading" : (status as "idle" | "empty" | "ok" | "error" | "processing")}}
              message={{response}}
            />
          </div>
        </section>

        <aside className="status-panel" data-testid="status-panel">
          <h2>Status</h2>
          <p>
            <strong>State:</strong> {{isLoading ? "loading" : status}}
          </p>
          <p>
            <strong>Response:</strong> {{response || "No response yet"}}
          </p>
        </aside>
      </EnterpriseShell>
    </div>
  );
}}
'''


def _frontend_enterprise_shell_component() -> str:
    return '''import type { ReactNode } from "react";

type EnterpriseShellProps = {
  appTitle: string;
  shellNote: string;
  statusLabel: string;
  children: ReactNode;
};

export function EnterpriseShell({ appTitle, shellNote, statusLabel, children }: EnterpriseShellProps) {
  return (
    <main className="shell" data-testid="workspace-shell">
      <nav className="shell-navigation" data-testid="shell-navigation">
        <a href="/">Workspace</a>
        <a href="/settings">Settings</a>
        <a href="/admin">Admin</a>
        <a href="/activity">Activity</a>
      </nav>
      <header className="shell-header" data-testid="shell-header">
        <div>
          <h1>{appTitle}</h1>
          <p>{shellNote}</p>
        </div>
        <div className="status-pill" data-testid="status-notification">
          {statusLabel}
        </div>
      </header>
      <section className="shell-content">{children}</section>
    </main>
  );
}
'''


def _frontend_enterprise_states_component() -> str:
    return '''type EnterpriseState = "idle" | "loading" | "empty" | "ok" | "error" | "processing";

type EnterpriseStatePanelProps = {
  state: EnterpriseState;
  message: string;
};

export function EnterpriseStatePanel({ state, message }: EnterpriseStatePanelProps) {
  if (state === "loading" || state === "processing") {
    return (
      <section className="state-card state-loading" data-testid="loading-state">
        <h3>Loading</h3>
        <p>Processing your command and waiting for backend response.</p>
      </section>
    );
  }

  if (state === "empty" || (state === "idle" && !message)) {
    return (
      <section className="state-card state-empty" data-testid="empty-state">
        <h3>No Command Yet</h3>
        <p>Submit a command to populate this workspace response panel.</p>
      </section>
    );
  }

  if (state === "error") {
    return (
      <section className="state-card state-error" data-testid="error-state">
        <h3>Request Error</h3>
        <p>{message || "An unexpected error occurred."}</p>
      </section>
    );
  }

  return (
    <section className="state-card state-success" data-testid="success-state">
      <h3>Response</h3>
      <p>{message || "Command processed successfully."}</p>
    </section>
  );
}
'''


def _frontend_settings_page() -> str:
    return '''export default function SettingsPage() {
  return (
    <main className="surface-page" data-testid="settings-surface">
      <h1>Settings Surface</h1>
      <p>Operator configuration placeholders for profile, environment, and notification preferences.</p>
    </main>
  );
}
'''


def _frontend_admin_page() -> str:
    return '''export default function AdminPage() {
  return (
    <main className="surface-page" data-testid="admin-surface">
      <h1>Admin Surface</h1>
      <p>Enterprise admin workflows placeholder for user management, policy controls, and escalations.</p>
    </main>
  );
}
'''


def _frontend_activity_page() -> str:
    return '''export default function ActivityPage() {
  return (
    <main className="surface-page" data-testid="activity-surface">
      <h1>Activity Surface</h1>
      <p>Audit and operational activity placeholder with deterministic timeline structure.</p>
    </main>
  );
}
'''


def _frontend_layout() -> str:
    return '''import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Autobuilder Commercial Starter",
  description: "React/Next workspace shell generated by AutobuilderV2",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
'''


def _frontend_css() -> str:
    return ''':root {
  --bg: #f4f3ef;
  --panel: #ffffff;
  --ink: #171412;
  --muted: #5a5049;
  --accent: #0f6b8f;
  --accent-strong: #0a4f69;
  --border: #d7cfc8;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: radial-gradient(circle at 10% 10%, #ffffff 0%, #f4f3ef 45%, #ece8df 100%);
  color: var(--ink);
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}

.shell {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: 2.1fr 1fr;
  grid-template-areas:
    "nav nav"
    "header header"
    "command status"
    "main status";
  min-height: 100vh;
  padding: 1.5rem;
}

.shell-navigation {
  grid-area: nav;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  display: flex;
  gap: 0.9rem;
  padding: 0.75rem 1rem;
}

.shell-navigation a {
  color: var(--accent-strong);
  font-weight: 600;
  text-decoration: none;
}

.shell-content {
  display: contents;
}

.shell-header {
  grid-area: header;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.shell-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.shell-header p {
  color: var(--muted);
  margin-top: 0.5rem;
}

.status-pill {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #e7f2f7;
  color: var(--accent-strong);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  padding: 0.35rem 0.75rem;
  text-transform: uppercase;
}

.command-panel,
.work-surface,
.status-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem;
}

.surface-page {
  max-width: 840px;
  margin: 2rem auto;
  padding: 1.2rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--panel);
}

.command-panel {
  grid-area: command;
}

.work-surface {
  grid-area: main;
}

.status-panel {
  grid-area: status;
}

.command-row {
  display: flex;
  gap: 0.65rem;
  margin-top: 0.5rem;
}

.hint {
  margin: 0.65rem 0 0;
  color: var(--muted);
  font-size: 0.88rem;
}

input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.6rem;
  font-size: 0.95rem;
}

button {
  border: 0;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  background: var(--accent);
  color: #ffffff;
  cursor: pointer;
}

button:hover {
  background: var(--accent-strong);
}

.state-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-top: 0.8rem;
  padding: 0.8rem;
}

.state-card h3 {
  margin: 0;
}

.state-card p {
  margin: 0.4rem 0 0;
}

.state-loading {
  background: #eef6fb;
}

.state-empty {
  background: #f8f5ef;
}

.state-error {
  background: #fff1ef;
  border-color: #f0c3b9;
}

.state-success {
  background: #eef8f2;
}

@media (max-width: 900px) {
  .shell {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "command"
      "main"
      "status";
  }

  .shell-navigation {
    overflow-x: auto;
  }

  .shell-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.5rem;
  }
}
'''


def _frontend_shell_check() -> str:
    return '''const fs = require("fs");
const path = require("path");

const shellPath = path.join(__dirname, "..", "app", "page.tsx");
const shellComponentPath = path.join(__dirname, "..", "components", "enterprise-shell.tsx");
const pageContent = fs.readFileSync(shellPath, "utf-8");
const shellContent = fs.readFileSync(shellComponentPath, "utf-8");

const requiredMarkers = [
  'data-testid="workspace-shell"',
  'data-testid="shell-navigation"',
  'data-testid="shell-header"',
  'data-testid="status-notification"',
  'data-testid="command-surface"',
  'data-testid="response-state-region"',
  '/api/workspace/execute',
];

for (const marker of requiredMarkers) {
  if (!pageContent.includes(marker) && !shellContent.includes(marker)) {
    throw new Error(`Missing required shell marker: ${marker}`);
  }
}

console.log("frontend shell check passed");
'''


def _backend_app() -> str:
    return '''from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.admin import router as admin_router
from api.audit import router as audit_router
from api.config import get_settings
from api.logging import configure_logging
from api.operator import router as operator_router
from api.responses import error_envelope, ok_envelope


class CommandRequest(BaseModel):
    command: str


app = FastAPI(title="Autobuilder Commercial Starter API")
configure_logging()
app.include_router(admin_router)
app.include_router(operator_router)
app.include_router(audit_router)


@app.exception_handler(Exception)
def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
  return JSONResponse(status_code=500, content=error_envelope("unhandled_error", str(exc)))


@app.get("/health")
def health() -> dict[str, object]:
  return ok_envelope(data={"status": "ok"})


@app.get("/ready")
def readiness() -> dict[str, object]:
    settings = get_settings()
  return ok_envelope(
    data={
      "status": "ready",
      "checks": {
        "database_url_configured": bool(settings.database_url),
        "cors_origin_configured": bool(settings.cors_origin),
      },
    }
  )


@app.get("/version")
def version() -> dict[str, object]:
    settings = get_settings()
  return ok_envelope(data={"version": settings.app_version, "env": settings.app_env})


@app.post("/api/workspace/execute")
def execute_workspace_command(payload: CommandRequest) -> dict[str, object]:
    sanitized = payload.command.strip() or "noop"
  return ok_envelope(
    data={
      "command": sanitized,
      "result": f"accepted command: {sanitized}",
      "state": "ok",
    }
  )
'''


def _backend_response_envelopes() -> str:
  return '''from __future__ import annotations


def ok_envelope(data: dict[str, object]) -> dict[str, object]:
  return {
    "status": "ok",
    "data": data,
    "error": None,
  }


def error_envelope(code: str, message: str) -> dict[str, object]:
  return {
    "status": "error",
    "data": None,
    "error": {
      "code": code,
      "message": message,
    },
  }
'''


def _backend_logging() -> str:
  return '''from __future__ import annotations

import logging


def configure_logging() -> None:
  logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
  )
'''


def _backend_admin_router() -> str:
  return '''from fastapi import APIRouter

from api.responses import ok_envelope

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/status")
def admin_status() -> dict[str, object]:
  return ok_envelope(data={"surface": "admin", "ready": True})
'''


def _backend_operator_router() -> str:
  return '''from fastapi import APIRouter

from api.responses import ok_envelope

router = APIRouter(prefix="/api/operator", tags=["operator"])


@router.get("/status")
def operator_status() -> dict[str, object]:
  return ok_envelope(data={"surface": "operator", "ready": True})
'''


def _backend_audit_router() -> str:
  return '''from fastapi import APIRouter

from api.responses import ok_envelope

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/activity")
def recent_activity() -> dict[str, object]:
  return ok_envelope(data={"surface": "audit", "entries": []})
'''


def _backend_config() -> str:
    return '''from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_version: str = "0.1.0"
    database_url: str = "postgresql://postgres:postgres@db:5432/app"
    cors_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
'''


def _backend_requirements() -> str:
    return "fastapi==0.115.0\nuvicorn==0.30.6\npydantic-settings==2.5.2\npytest==8.3.3\nhttpx==0.27.2\n"


def _backend_test() -> str:
    return '''from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
  payload = response.json()
  assert payload["status"] == "ok"
  assert payload["data"]["status"] == "ok"


def test_readiness_endpoint() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
  payload = response.json()
  assert payload["status"] == "ok"
  assert payload["data"]["status"] == "ready"


def test_version_endpoint() -> None:
    response = client.get("/version")
    assert response.status_code == 200
  assert "version" in response.json()["data"]


def test_workspace_execute_shape() -> None:
    response = client.post("/api/workspace/execute", json={"command": "refresh dashboard"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
  assert payload["data"]["command"] == "refresh dashboard"
  assert "accepted command" in payload["data"]["result"]


def test_operator_and_admin_routes_exist() -> None:
  assert client.get("/api/admin/status").status_code == 200
  assert client.get("/api/operator/status").status_code == 200
  assert client.get("/api/audit/activity").status_code == 200
'''


def _enterprise_polish_doc() -> str:
  return '''# Enterprise Polish Coverage

Generated package includes enterprise polish packs:

- loading state surface
- empty state surface
- error state surface
- settings surface
- admin/operator surface
- audit/activity surface
- shell navigation/header conventions
- status/notification conventions
'''


def _readiness_doc() -> str:
  return '''# Readiness

This generated app includes deterministic readiness endpoints and placeholder checks.

- GET /health
- GET /ready
- GET /version
- Operator/admin/audit placeholder routes
'''


def _proof_of_run_doc() -> str:
  return '''# Proof of Run

Expected local proof sequence:

1. docker compose up
2. frontend shell loads with deterministic states
3. backend endpoints return envelope responses
4. operator/admin/audit placeholders respond
'''


def _proof_report_json(ir: AppIR) -> str:
  return _json_pretty(
    {
      "appIdentity": ir.app_identity,
      "status": "pending",
      "checks": [
        "frontend_shell",
        "backend_health_ready_version",
        "operator_admin_audit_surfaces",
      ],
    }
  )


def _readiness_report_json() -> str:
  return _json_pretty(
    {
      "readiness_status": "pending",
      "readiness_reasons": ["run generated app validation"],
    }
  )


def _validation_summary_json() -> str:
  return _json_pretty(
    {
      "validation_status": "pending",
      "all_passed": False,
      "passed_count": 0,
      "failed_count": 0,
      "total_checks": 0,
      "failed_checks": [],
    }
  )


def _determinism_signature_json() -> str:
  return _json_pretty(
    {
      "verified": False,
      "build_signature_sha256": "",
      "proof_signature_sha256": "",
      "repeat_build_match_required": True,
    }
  )


def _package_artifact_summary_json() -> str:
  return _json_pretty(
    {
      "packaging_status": "pending",
      "release_bundle_paths": [
        "release/README.md",
        "release/deploy/DEPLOYMENT_NOTES.md",
        "release/runbook/OPERATOR_RUNBOOK.md",
        "release/proof/PROOF_BUNDLE.md",
      ],
      "notes": ["populate after build/ship packaging summarization"],
    }
  )


def _proof_readiness_bundle_json() -> str:
  return _json_pretty(
    {
      "bundle_status": "pending",
      "proof_report": ".autobuilder/proof_report.json",
      "readiness_report": ".autobuilder/readiness_report.json",
      "validation_summary": ".autobuilder/validation_summary.json",
      "determinism_signature": ".autobuilder/determinism_signature.json",
    }
  )


def _deployment_notes_doc() -> str:
  return '''# Deployment Notes

Supported deployment assumptions for this generated app:

- frontend: Next.js app served by `next dev` locally
- backend: FastAPI served by `uvicorn`
- database: Postgres 16
- orchestration: Docker Compose

## Local boot

```bash
docker compose up
```

## Startup assumptions

- frontend available at `http://localhost:3000`
- backend available at `http://localhost:8000`
- postgres available at `localhost:5432`
'''


def _startup_validation_doc() -> str:
  return '''# Startup and Validation

## Startup

```bash
docker compose up
```

## Validation

```bash
python cli/autobuilder.py validate-app --target <generated_repo> --repair --json
python cli/autobuilder.py proof-app --target <generated_repo> --repair --json
```

## Expected proof artifacts

- `.autobuilder/proof_report.json`
- `.autobuilder/readiness_report.json`
- `.autobuilder/validation_summary.json`
- `.autobuilder/determinism_signature.json`
'''


def _release_bundle_readme() -> str:
  return '''# Release Bundle

This folder contains handoff packaging assets for commercial deployment.

- `deploy/DEPLOYMENT_NOTES.md`: deployment assumptions and startup behavior
- `runbook/OPERATOR_RUNBOOK.md`: operator procedures
- `proof/PROOF_BUNDLE.md`: proof/readiness bundle index

Use alongside root README startup and validation instructions.
'''


def _release_deployment_notes() -> str:
  return '''# Deployment Assumptions

First-class stack:

- React/Next frontend
- FastAPI backend
- Postgres database
- Docker Compose deployment

## Startup contract

1. Configure `.env.example` and `backend/.env.example` values.
2. Run `docker compose up`.
3. Validate `GET /health`, `GET /ready`, and UI shell load.
'''


def _operator_runbook_doc() -> str:
  return '''# Operator Runbook

## Startup

1. Run `docker compose up`.
2. Verify backend `/health` and `/ready`.
3. Verify frontend workspace shell and operator surfaces.

## Validation

1. Run generated-app validation with repair.
2. Run proof-app certification.
3. Archive proof/readiness artifacts for handoff.
'''


def _release_proof_bundle_doc() -> str:
  return '''# Proof and Readiness Bundle

Bundle this section with release handoff:

- `.autobuilder/proof_report.json`
- `.autobuilder/readiness_report.json`
- `.autobuilder/validation_summary.json`
- `.autobuilder/determinism_signature.json`
- `.autobuilder/package_artifact_summary.json`
- `.autobuilder/proof_readiness_bundle.json`
'''


def _docker_compose() -> str:
    return '''services:
  frontend:
    image: node:20
    working_dir: /workspace/frontend
    command: sh -c "npm install && npm run dev"
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./:/workspace
    depends_on:
      - backend

  backend:
    image: python:3.12-slim
    working_dir: /workspace/backend
    command: sh -c "pip install -r requirements.txt && uvicorn api.main:app --host 0.0.0.0 --port 8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/app
      APP_ENV: local
      APP_VERSION: 0.1.0
      CORS_ORIGIN: http://localhost:3000
    ports:
      - "8000:8000"
    volumes:
      - ./:/workspace
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
'''


def _root_readme(ir: AppIR) -> str:
    return f'''# {ir.app_identity}

Commercial starter application generated by AutobuilderV2.

## Included stack

- Frontend: React/Next workspace shell
- Backend: FastAPI API service
- Database assumptions: Postgres environment wiring
- Deployment: Docker Compose for local startup

## Starter structure

- One command input surface in frontend shell
- One main content/work surface
- One status/response panel
- Operator/admin placeholders under docs and api routes

## Local run

1. Start everything:

```bash
docker compose up
```

2. Open frontend at http://localhost:3000
3. API health endpoint: http://localhost:8000/health

## Backend tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

## Frontend shell check

```bash
cd frontend
npm install
npm run test:shell
```
'''


def _generated_readme() -> str:
    return '''# Generated Assets

This directory records deterministic metadata about the generated starter app.

- ir.json: normalized internal representation used for generation
- build_plan.json: intended structures and modules
- generation_summary.json: emitted files and validation plan
'''


def _build_validation_plan() -> list[str]:
    return [
    "required_repo_structure_present",
    "frontend_shell_essentials_present",
    "backend_endpoint_essentials_present",
    "env_config_essentials_present",
    "docker_deployment_essentials_present",
    "proof_readiness_artifacts_present",
    "packaging_deployment_bundle_present",
    "enterprise_polish_surface_presence",
        "backend_pytest_endpoints",
        "frontend_shell_structure_check",
        "docker_compose_service_boot",
        "manual_smoke_health_and_ready",
    ]


def generate_first_class_templates(ir: AppIR) -> list[GeneratedTemplate]:
    return [
        GeneratedTemplate(path="README.md", content=_root_readme(ir)),
        GeneratedTemplate(path=".env.example", content=(
            "APP_ENV=local\n"
            "APP_VERSION=0.1.0\n"
            "DATABASE_URL=postgresql://postgres:postgres@db:5432/app\n"
            "CORS_ORIGIN=http://localhost:3000\n"
            "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n"
        )),
        GeneratedTemplate(path="docker-compose.yml", content=_docker_compose()),
        GeneratedTemplate(path="frontend/package.json", content=_frontend_package_json()),
        GeneratedTemplate(path="frontend/tsconfig.json", content=_frontend_tsconfig_json()),
        GeneratedTemplate(path="frontend/next-env.d.ts", content='/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n\n'),
        GeneratedTemplate(path="frontend/next.config.js", content='/** @type {import("next").NextConfig} */\nconst nextConfig = {};\n\nmodule.exports = nextConfig;\n'),
        GeneratedTemplate(path="frontend/app/layout.tsx", content=_frontend_layout()),
        GeneratedTemplate(path="frontend/app/page.tsx", content=_frontend_shell_page(ir)),
        GeneratedTemplate(path="frontend/app/settings/page.tsx", content=_frontend_settings_page()),
        GeneratedTemplate(path="frontend/app/admin/page.tsx", content=_frontend_admin_page()),
        GeneratedTemplate(path="frontend/app/activity/page.tsx", content=_frontend_activity_page()),
        GeneratedTemplate(path="frontend/app/globals.css", content=_frontend_css()),
        GeneratedTemplate(path="frontend/components/enterprise-shell.tsx", content=_frontend_enterprise_shell_component()),
        GeneratedTemplate(path="frontend/components/enterprise-states.tsx", content=_frontend_enterprise_states_component()),
        GeneratedTemplate(path="frontend/tests/shell-check.js", content=_frontend_shell_check()),
        GeneratedTemplate(path="frontend/public/.gitkeep", content=""),
        GeneratedTemplate(path="frontend/status.seed.json", content=_frontend_status_seed(ir)),
        GeneratedTemplate(path="backend/requirements.txt", content=_backend_requirements()),
        GeneratedTemplate(path="backend/api/__init__.py", content=""),
        GeneratedTemplate(path="backend/api/main.py", content=_backend_app()),
        GeneratedTemplate(path="backend/api/config.py", content=_backend_config()),
        GeneratedTemplate(path="backend/api/responses.py", content=_backend_response_envelopes()),
        GeneratedTemplate(path="backend/api/logging.py", content=_backend_logging()),
        GeneratedTemplate(path="backend/api/admin.py", content=_backend_admin_router()),
        GeneratedTemplate(path="backend/api/operator.py", content=_backend_operator_router()),
        GeneratedTemplate(path="backend/api/audit.py", content=_backend_audit_router()),
        GeneratedTemplate(path="backend/tests/test_endpoints.py", content=_backend_test()),
        GeneratedTemplate(path="backend/.env.example", content=(
            "APP_ENV=local\n"
            "APP_VERSION=0.1.0\n"
            "DATABASE_URL=postgresql://postgres:postgres@db:5432/app\n"
            "CORS_ORIGIN=http://localhost:3000\n"
        )),
        GeneratedTemplate(path="db/schema.sql", content=(
            "CREATE TABLE IF NOT EXISTS users (\n"
            "  id SERIAL PRIMARY KEY,\n"
            "  email TEXT NOT NULL UNIQUE,\n"
            "  role TEXT NOT NULL DEFAULT 'user'\n"
            ");\n"
        )),
        GeneratedTemplate(path="docs/OPERATOR.md", content=(
            "# Operator Notes\n\n"
            "- Add admin routes under backend/api/admin.py\n"
            "- Add privileged workspace actions behind role checks\n"
            "- Keep execution actions auditable\n"
        )),
        GeneratedTemplate(path="docs/ENTERPRISE_POLISH.md", content=_enterprise_polish_doc()),
        GeneratedTemplate(path="docs/READINESS.md", content=_readiness_doc()),
        GeneratedTemplate(path="docs/PROOF_OF_RUN.md", content=_proof_of_run_doc()),
        GeneratedTemplate(path="docs/DEPLOYMENT.md", content=_deployment_notes_doc()),
        GeneratedTemplate(path="docs/STARTUP_VALIDATION.md", content=_startup_validation_doc()),
        GeneratedTemplate(path="release/README.md", content=_release_bundle_readme()),
        GeneratedTemplate(path="release/deploy/DEPLOYMENT_NOTES.md", content=_release_deployment_notes()),
        GeneratedTemplate(path="release/runbook/OPERATOR_RUNBOOK.md", content=_operator_runbook_doc()),
        GeneratedTemplate(path="release/proof/PROOF_BUNDLE.md", content=_release_proof_bundle_doc()),
        GeneratedTemplate(path=".autobuilder/README.md", content=_generated_readme()),
        GeneratedTemplate(path=".autobuilder/proof_report.json", content=_proof_report_json(ir)),
        GeneratedTemplate(path=".autobuilder/readiness_report.json", content=_readiness_report_json()),
        GeneratedTemplate(path=".autobuilder/validation_summary.json", content=_validation_summary_json()),
        GeneratedTemplate(path=".autobuilder/determinism_signature.json", content=_determinism_signature_json()),
        GeneratedTemplate(path=".autobuilder/package_artifact_summary.json", content=_package_artifact_summary_json()),
        GeneratedTemplate(path=".autobuilder/proof_readiness_bundle.json", content=_proof_readiness_bundle_json()),
    ]


def first_class_validation_plan() -> list[str]:
    return _build_validation_plan()
