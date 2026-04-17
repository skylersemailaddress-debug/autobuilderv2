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


def _backend_app(include_security: bool, include_commerce: bool) -> str:
  security_enabled = "True" if include_security else "False"
  commerce_enabled = "True" if include_commerce else "False"

  security_imports = ""
  security_router_include = ""
  security_dep = ""
  security_fields = ""
  if include_security:
    security_imports = (
      "from api.auth import router as auth_router\\n"
      "from api.security import router as security_router\\n"
      "from security.auth_dependency import AuthContext, require_auth_context\\n"
    )
    security_router_include = (
      "app.include_router(auth_router)\\n"
      "app.include_router(security_router)\\n"
    )
    security_dep = "auth: AuthContext = Depends(require_auth_context),"
    security_fields = (
      '            "actor": auth.actor,\\n'
      '            "role": auth.role,\\n'
    )

  commerce_imports = ""
  commerce_router_include = ""
  if include_commerce:
    commerce_imports = (
      "from api.billing_admin import router as billing_admin_router\\n"
      "from api.billing_webhooks import router as billing_router\\n"
      "from api.plans import router as plans_router\\n"
    )
    commerce_router_include = (
      "app.include_router(plans_router)\\n"
      "app.include_router(billing_router)\\n"
      "app.include_router(billing_admin_router)\\n"
    )

  return '''from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.admin import router as admin_router
from api.audit import router as audit_router
from api.config import get_settings
from api.logging import configure_logging
from api.operator import router as operator_router
from api.responses import error_envelope, ok_envelope
__SECURITY_IMPORTS____COMMERCE_IMPORTS__


class CommandRequest(BaseModel):
  command: str


SECURITY_ENABLED = __SECURITY_ENABLED__
COMMERCE_ENABLED = __COMMERCE_ENABLED__

app = FastAPI(title="Autobuilder Commercial Starter API")
configure_logging()
app.include_router(admin_router)
app.include_router(operator_router)
app.include_router(audit_router)
__SECURITY_ROUTER_INCLUDE____COMMERCE_ROUTER_INCLUDE__


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
        "security_scaffold_enabled": SECURITY_ENABLED,
        "commerce_scaffold_enabled": COMMERCE_ENABLED,
      },
    }
  )


@app.get("/version")
def version() -> dict[str, object]:
  settings = get_settings()
  return ok_envelope(data={"version": settings.app_version, "env": settings.app_env})


@app.post("/api/workspace/execute")
def execute_workspace_command(
  payload: CommandRequest,
  __SECURITY_DEP__
) -> dict[str, object]:
  sanitized = payload.command.strip() or "noop"
  return ok_envelope(
    data={
__SECURITY_FIELDS__            "command": sanitized,
      "result": f"accepted command: {sanitized}",
      "state": "ok",
    }
  )
'''.replace("__SECURITY_IMPORTS__", security_imports).replace(
    "__COMMERCE_IMPORTS__", commerce_imports
  ).replace("__SECURITY_ROUTER_INCLUDE__", security_router_include).replace(
    "__COMMERCE_ROUTER_INCLUDE__", commerce_router_include
  ).replace("__SECURITY_DEP__", security_dep).replace(
    "__SECURITY_FIELDS__", security_fields
  ).replace("__SECURITY_ENABLED__", security_enabled).replace(
    "__COMMERCE_ENABLED__", commerce_enabled
  )


def _backend_auth_dependency(ir: AppIR) -> str:
    roles = [str(role.get("name") or role.get("role") or "") for role in ir.auth_roles or []]
    normalized_roles = sorted({role for role in roles if role}) or ["admin", "member", "viewer"]
    role_literal = ", ".join([f'"{role}"' for role in normalized_roles])
    return f'''from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException


ALLOWED_ROLES = [{role_literal}]


@dataclass(frozen=True)
class AuthContext:
  actor: str
  role: str
  token_present: bool


def require_auth_context(
  authorization: str | None = Header(default=None),
  x_actor: str | None = Header(default=None),
  x_role: str | None = Header(default=None),
) -> AuthContext:
  if not authorization:
    raise HTTPException(status_code=401, detail="Missing Authorization header")
  if not authorization.lower().startswith("bearer "):
    raise HTTPException(status_code=401, detail="Authorization header must use Bearer token")
  role = (x_role or "member").strip().lower()
  if role not in ALLOWED_ROLES:
    raise HTTPException(status_code=403, detail="Role not allowed")
  actor = (x_actor or "unknown_actor").strip() or "unknown_actor"
  return AuthContext(actor=actor, role=role, token_present=True)
'''


def _backend_rbac_roles(ir: AppIR) -> str:
    role_names = [str(role.get("name") or role.get("role") or "") for role in ir.auth_roles or []]
    normalized = sorted({name for name in role_names if name}) or ["admin", "member", "viewer"]
    enum_members = "\n".join([f'    {name.upper().replace("-", "_")} = "{name}"' for name in normalized])
    policy_entries = "\n".join(
        [
            f'    "{name}": ["read:workspace", "execute:workspace"],'
            for name in normalized
        ]
    )
    return f'''from __future__ import annotations

from enum import Enum


class Role(str, Enum):
{enum_members}


ROLE_POLICIES: dict[str, list[str]] = {{
{policy_entries}
}}


def is_allowed(role: str, permission: str) -> bool:
  return permission in ROLE_POLICIES.get(role, [])
'''


def _backend_auth_router() -> str:
    return '''from fastapi import APIRouter, Depends

from api.responses import ok_envelope
from security.auth_dependency import AuthContext, require_auth_context

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/session")
def validate_session(auth: AuthContext = Depends(require_auth_context)) -> dict[str, object]:
  return ok_envelope(
    data={
      "authenticated": True,
      "actor": auth.actor,
      "role": auth.role,
      "token_present": auth.token_present,
    }
  )
'''


def _backend_plans_router(enabled: bool) -> str:
    commerce_enabled = "True" if enabled else "False"
    return '''from fastapi import APIRouter

from api.responses import ok_envelope

router = APIRouter(prefix="/api/plans", tags=["billing"])

COMMERCE_ENABLED = __COMMERCE_ENABLED__


@router.get("")
def list_plans() -> dict[str, object]:
  return ok_envelope(
    data={
      "plans": [
        {"id": "free", "price_usd": 0},
        {"id": "pro", "price_usd": 29},
        {"id": "enterprise", "price_usd": None},
      ],
      "enabled": COMMERCE_ENABLED,
      "note": "Plan catalogue scaffold only; live billing provider integration required.",
    }
  )
'''.replace("__COMMERCE_ENABLED__", commerce_enabled)


def _backend_billing_webhooks_router(enabled: bool) -> str:
    commerce_enabled = "True" if enabled else "False"
    return '''from fastapi import APIRouter, Header, HTTPException

from api.responses import ok_envelope

router = APIRouter(prefix="/api/billing", tags=["billing"])

COMMERCE_ENABLED = __COMMERCE_ENABLED__


@router.post("/webhooks")
def billing_webhook(
  payload: dict[str, object],
  x_signature: str | None = Header(default=None),
) -> dict[str, object]:
  if not x_signature:
    raise HTTPException(status_code=400, detail="Missing webhook signature header")
  return ok_envelope(
    data={
      "received": True,
      "enabled": COMMERCE_ENABLED,
      "event_type": str(payload.get("event_type", "unknown")),
      "idempotency_key": str(payload.get("id", "")),
      "note": "Webhook handler scaffold only; add provider signature verification.",
    }
  )
'''.replace("__COMMERCE_ENABLED__", commerce_enabled)


def _backend_entitlements_service() -> str:
    return '''from __future__ import annotations


class EntitlementsService:
  def check_entitlement(self, user_id: str, feature_id: str) -> bool:
    # Scaffold contract only: wire to subscription provider and entitlement store.
    _ = (user_id, feature_id)
    return True

  def get_limits(self, subscription_id: str) -> dict[str, int | None]:
    _ = subscription_id
    return {"api_calls_per_month": None, "seats": None}

  def record_usage(self, subscription_id: str, metric: str, amount: int) -> dict[str, object]:
    _ = (subscription_id, metric, amount)
    return {"recorded": True, "source": "scaffold"}
'''


def _should_include_commerce_scaffolds(ir: AppIR) -> bool:
  if ir.app_type in {"saas_web_app", "workspace_app", "internal_tool", "api_service", "workflow_system", "copilot_chat_app"}:
    return True
  tokens = " ".join(
    [
      *(str(item) for item in ir.acceptance_criteria),
      *(str(route.get("path", "")) for route in ir.api_routes),
      *(str(workflow.get("name", "")) for workflow in ir.workflows),
    ]
  ).lower()
  return any(word in tokens for word in ["billing", "payment", "subscription", "plan", "commerce", "stripe"])


def _should_include_security_scaffolds(ir: AppIR) -> bool:
  if ir.app_type in {"saas_web_app", "workspace_app", "internal_tool", "api_service", "workflow_system", "copilot_chat_app"}:
    return True
  tokens = " ".join(
    [
      *(str(item) for item in ir.acceptance_criteria),
      *(str(route.get("path", "")) for route in ir.api_routes),
      *(str(role.get("name", "")) for role in ir.auth_roles),
    ]
  ).lower()
  return any(word in tokens for word in ["auth", "rbac", "role", "security", "authorization"])


def _backend_security_router() -> str:
  return '''from fastapi import APIRouter

from api.responses import ok_envelope

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/contract")
def security_contract_surface() -> dict[str, object]:
  return ok_envelope(
    data={
      "auth_dependency": "enabled",
      "rbac_placeholder": "enabled",
      "note": "Security scaffold only; integrate provider-backed auth and policy engine.",
    }
  )
'''


def _backend_billing_admin_router() -> str:
  return '''from fastapi import APIRouter

from api.responses import ok_envelope

router = APIRouter(prefix="/api/admin/billing", tags=["billing_admin"])


@router.get("/overview")
def billing_overview() -> dict[str, object]:
  return ok_envelope(
    data={
      "status": "scaffold",
      "surfaces": ["subscriptions", "invoices", "plans", "usage"],
      "note": "Billing admin scaffold only; wire to payment provider and data store.",
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
    response = client.post(
        "/api/workspace/execute",
        json={"command": "refresh dashboard"},
        headers={"Authorization": "Bearer local-token", "X-Actor": "tester", "X-Role": "admin"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["command"] == "refresh dashboard"
    assert payload["data"]["actor"] == "tester"
    assert payload["data"]["role"] == "admin"
    assert "accepted command" in payload["data"]["result"]


def test_operator_and_admin_routes_exist() -> None:
    assert client.get("/api/admin/status").status_code == 200
    assert client.get("/api/operator/status").status_code == 200
    assert client.get("/api/audit/activity").status_code == 200
  assert client.get("/api/security/contract").status_code == 200
  assert client.get("/api/plans").status_code == 200
  assert client.get("/api/admin/billing/overview").status_code == 200
  assert client.post(
    "/api/billing/webhooks",
    json={"id": "evt_1", "event_type": "invoice.paid"},
    headers={"X-Signature": "sig"},
  ).status_code == 200
'''


def _operator_notes_doc() -> str:
  return '''# Operator Notes

This generated app is intended for the first-class commercial lane:

- frontend: React/Next
- backend: FastAPI
- database: Postgres
- deployment: Docker Compose

## Canonical operator flow

1. Start services with `docker compose up`.
2. Verify `/health`, `/ready`, and `/version`.
3. Run generated-app validation and repair if needed.
4. Run proof-app certification.
5. Archive `.autobuilder/*report*.json` and release bundle docs.

## Admin and audit placeholders

- `backend/api/admin.py`
- `backend/api/operator.py`
- `backend/api/audit.py`
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
    if ir.app_type == "mobile_app":
        return mobile_lane_templates(ir)
    if ir.app_type == "game_app":
        return game_lane_templates(ir)
    if ir.app_type == "realtime_system":
        return realtime_lane_templates(ir)
    if ir.app_type == "enterprise_agent_system":
        return enterprise_agent_lane_templates(ir)
    include_security = _should_include_security_scaffolds(ir)
    include_commerce = _should_include_commerce_scaffolds(ir)

    templates = [
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
        GeneratedTemplate(path="backend/api/main.py", content=_backend_app(include_security, include_commerce)),
        GeneratedTemplate(path="backend/api/auth.py", content=_backend_auth_router()),
        GeneratedTemplate(path="backend/api/security.py", content=_backend_security_router()),
        GeneratedTemplate(path="backend/api/config.py", content=_backend_config()),
        GeneratedTemplate(path="backend/api/responses.py", content=_backend_response_envelopes()),
        GeneratedTemplate(path="backend/api/logging.py", content=_backend_logging()),
        GeneratedTemplate(path="backend/api/admin.py", content=_backend_admin_router()),
        GeneratedTemplate(path="backend/api/operator.py", content=_backend_operator_router()),
        GeneratedTemplate(path="backend/api/audit.py", content=_backend_audit_router()),
        GeneratedTemplate(path="backend/api/billing_admin.py", content=_backend_billing_admin_router()),
        GeneratedTemplate(path="backend/api/plans.py", content=_backend_plans_router(include_commerce)),
        GeneratedTemplate(path="backend/api/billing_webhooks.py", content=_backend_billing_webhooks_router(include_commerce)),
        GeneratedTemplate(path="backend/security/auth_dependency.py", content=_backend_auth_dependency(ir)),
        GeneratedTemplate(path="backend/security/rbac.py", content=_backend_rbac_roles(ir)),
        GeneratedTemplate(path="backend/security/__init__.py", content=""),
        GeneratedTemplate(path="backend/services/entitlements.py", content=_backend_entitlements_service()),
        GeneratedTemplate(path="backend/services/__init__.py", content=""),
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
        GeneratedTemplate(path="docs/OPERATOR.md", content=_operator_notes_doc()),
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

    return templates


def first_class_validation_plan() -> list[str]:
    return _build_validation_plan()


def _mobile_readiness_doc() -> str:
  return '''# Mobile Lane Readiness

Generated mobile lane includes:

- route-aware navigation shell
- auth-ready guard scaffolds
- local/offline store placeholder
- API client and state controller scaffolds

Run validation:

```bash
python cli/autobuilder.py validate-app --target <generated_mobile_repo> --json
```
'''


def _mobile_operator_doc() -> str:
  return '''# Mobile Operator Notes

- Verify Home, Settings, Admin, and Activity surfaces are reachable from the navigation scaffold.
- Wire auth providers and token exchange in `lib/auth/auth_guard.dart` and backend auth routes.
- Wire storage adapters in `lib/data/local_store.dart` for offline sync.
'''


def _realtime_readiness_doc() -> str:
  return '''# Realtime Lane Readiness

Generated realtime lane includes:

- bounded websocket gateway scaffold
- stream/event channel contracts
- world-state projection and alert/action path scaffolds
- sensor connector surface with deterministic event shape

Run validation:

```bash
python cli/autobuilder.py validate-app --target <generated_realtime_repo> --json
```
'''


def _enterprise_readiness_doc() -> str:
  return '''# Enterprise-Agent Lane Readiness

Generated enterprise-agent lane includes:

- multi-role task routing scaffold
- workflow and approval service scaffolds
- memory/state store with briefing/reporting surfaces
- operator-facing enterprise API endpoints

Run validation:

```bash
python cli/autobuilder.py validate-app --target <generated_enterprise_repo> --json
```
'''


def _game_readiness_doc() -> str:
  return '''# Game Lane Readiness

Generated game lane is bounded but materially scaffolded:

- scene organization for main and HUD
- input mapping and update loop scaffolds
- game-state and HUD controller surfaces
- run/export guidance for local prototyping

Run validation:

```bash
python cli/autobuilder.py validate-app --target <generated_game_repo> --json
```
'''


def _realtime_backend_app() -> str:
  return '''from __future__ import annotations

from fastapi import FastAPI

from api.admin import router as admin_router
from api.audit import router as audit_router
from api.operator import router as operator_router
from api.realtime import router as realtime_router
from api.responses import ok_envelope

app = FastAPI(title="Autobuilder Realtime Lane API")
app.include_router(admin_router)
app.include_router(operator_router)
app.include_router(audit_router)
app.include_router(realtime_router)


@app.get("/health")
def health() -> dict[str, object]:
  return ok_envelope(data={"status": "ok", "lane": "realtime"})


@app.get("/ready")
def ready() -> dict[str, object]:
  return ok_envelope(data={"status": "ready", "stream_contract": "bounded"})
'''


def _enterprise_backend_app() -> str:
  return '''from __future__ import annotations

from fastapi import FastAPI

from api.admin import router as admin_router
from api.audit import router as audit_router
from api.enterprise import router as enterprise_router
from api.operator import router as operator_router
from api.responses import ok_envelope

app = FastAPI(title="Autobuilder Enterprise Agent Lane API")
app.include_router(admin_router)
app.include_router(operator_router)
app.include_router(audit_router)
app.include_router(enterprise_router)


@app.get("/health")
def health() -> dict[str, object]:
  return ok_envelope(data={"status": "ok", "lane": "enterprise_agent"})


@app.get("/ready")
def ready() -> dict[str, object]:
  return ok_envelope(data={"status": "ready", "workflow_contract": "multi_role"})
'''


def mobile_lane_templates(ir: AppIR) -> list[GeneratedTemplate]:
    return [
        GeneratedTemplate(path="pubspec.yaml", content=(
            "name: mobile_app\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\n"
      "dependencies:\n  flutter:\n    sdk: flutter\n  http: ^1.0.0\n  shared_preferences: ^2.2.3\n"
        )),
    GeneratedTemplate(path="lib/app.dart", content=(
      "import 'package:flutter/material.dart';\n"
      "import 'navigation/app_router.dart';\n"
      "import 'state/app_state.dart';\n"
      "\n"
      "class MobileLaneApp extends StatelessWidget {\n"
      "  const MobileLaneApp({super.key});\n"
      "\n"
      "  @override\n"
      "  Widget build(BuildContext context) {\n"
      "    return MaterialApp(\n"
      "      title: 'Autobuilder Mobile Lane',\n"
      "      initialRoute: AppRouter.homeRoute,\n"
      "      routes: AppRouter.routes,\n"
      "      builder: (_, child) => AppStateScope(child: child ?? const SizedBox.shrink()),\n"
      "    );\n"
      "  }\n"
      "}\n"
    )),
        GeneratedTemplate(path="lib/main.dart", content=(
      "import 'package:flutter/material.dart';\n"
      "import 'app.dart';\n"
      "\n"
      "void main() => runApp(const MobileLaneApp());\n"
        )),
    GeneratedTemplate(path="lib/navigation/app_router.dart", content=(
      "import 'package:flutter/widgets.dart';\n"
      "\n"
      "import '../screens/activity_screen.dart';\n"
      "import '../screens/admin_screen.dart';\n"
      "import '../screens/home_screen.dart';\n"
      "import '../screens/settings_screen.dart';\n"
      "\n"
      "class AppRouter {\n"
      "  static const homeRoute = '/';\n"
      "  static const settingsRoute = '/settings';\n"
      "  static const adminRoute = '/admin';\n"
      "  static const activityRoute = '/activity';\n"
      "\n"
      "  static final routes = <String, WidgetBuilder>{\n"
      "    homeRoute: (_) => const HomeScreen(),\n"
      "    settingsRoute: (_) => const SettingsScreen(),\n"
      "    adminRoute: (_) => const AdminScreen(),\n"
      "    activityRoute: (_) => const ActivityScreen(),\n"
      "  };\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/screens/home_screen.dart", content=(
      "import 'package:flutter/material.dart';\n"
      "\n"
      "class HomeScreen extends StatelessWidget {\n"
      "  const HomeScreen({super.key});\n"
      "\n"
      "  @override\n"
      "  Widget build(BuildContext context) {\n"
      "    return const Scaffold(body: Center(child: Text('Home')));\n"
      "  }\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/screens/settings_screen.dart", content=(
      "import 'package:flutter/material.dart';\n"
      "\n"
      "class SettingsScreen extends StatelessWidget {\n"
      "  const SettingsScreen({super.key});\n"
      "\n"
      "  @override\n"
      "  Widget build(BuildContext context) {\n"
      "    return const Scaffold(body: Center(child: Text('Settings')));\n"
      "  }\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/screens/admin_screen.dart", content=(
      "import 'package:flutter/material.dart';\n"
      "\n"
      "class AdminScreen extends StatelessWidget {\n"
      "  const AdminScreen({super.key});\n"
      "\n"
      "  @override\n"
      "  Widget build(BuildContext context) {\n"
      "    return const Scaffold(body: Center(child: Text('Admin')));\n"
      "  }\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/screens/activity_screen.dart", content=(
      "import 'package:flutter/material.dart';\n"
      "\n"
      "class ActivityScreen extends StatelessWidget {\n"
      "  const ActivityScreen({super.key});\n"
      "\n"
      "  @override\n"
      "  Widget build(BuildContext context) {\n"
      "    return const Scaffold(body: Center(child: Text('Activity')));\n"
      "  }\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/auth/auth_guard.dart", content=(
      "class AuthGuard {\n"
      "  bool hasValidSessionToken(String? token) => token != null && token.isNotEmpty;\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/state/app_state.dart", content=(
      "import 'package:flutter/widgets.dart';\n"
      "\n"
      "class AppStateScope extends InheritedWidget {\n"
      "  const AppStateScope({required super.child, super.key});\n"
      "\n"
      "  @override\n"
      "  bool updateShouldNotify(covariant AppStateScope oldWidget) => false;\n"
      "}\n"
    )),
    GeneratedTemplate(path="lib/data/local_store.dart", content=(
      "class LocalStore {\n"
      "  Future<void> persistDraft(String key, String payload) async {\n"
      "    _ = (key, payload);\n"
      "  }\n"
      "}\n"
        )),
        GeneratedTemplate(path="lib/services/api_client.dart", content=(
      "class ApiClient {\n"
      "  final String baseUrl;\n"
      "  ApiClient(this.baseUrl);\n"
      "\n"
      "  Uri endpoint(String path) => Uri.parse('$baseUrl$path');\n"
      "}\n"
    )),
    GeneratedTemplate(path="backend/api/__init__.py", content=""),
    GeneratedTemplate(path="backend/api/main.py", content=_backend_app(True, False)),
    GeneratedTemplate(path="backend/api/auth.py", content=_backend_auth_router()),
    GeneratedTemplate(path="backend/api/security.py", content=_backend_security_router()),
    GeneratedTemplate(path="backend/security/__init__.py", content=""),
    GeneratedTemplate(path="backend/security/auth_dependency.py", content=_backend_auth_dependency(ir)),
    GeneratedTemplate(path="backend/security/rbac.py", content=_backend_rbac_roles(ir)),
    GeneratedTemplate(path="backend/api/mobile.py", content=(
      "from fastapi import APIRouter\n\n"
      "from api.responses import ok_envelope\n\n"
      "router = APIRouter(prefix='/api/mobile', tags=['mobile'])\n\n"
      "@router.get('/bootstrap')\n"
      "def mobile_bootstrap() -> dict[str, object]:\n"
      "    return ok_envelope(data={'surface': 'mobile', 'status': 'scaffold'})\n"
    )),
    GeneratedTemplate(path="docs/READINESS.md", content=_mobile_readiness_doc()),
    GeneratedTemplate(path="docs/OPERATOR.md", content=_mobile_operator_doc()),
    GeneratedTemplate(path="release/runbook/OPERATOR_RUNBOOK.md", content=_operator_runbook_doc()),
    GeneratedTemplate(path="release/proof/PROOF_BUNDLE.md", content=_release_proof_bundle_doc()),
    GeneratedTemplate(path="release/deploy/DEPLOYMENT_NOTES.md", content=_release_deployment_notes()),
    GeneratedTemplate(path="release/README.md", content=_release_bundle_readme()),
    GeneratedTemplate(path="docker-compose.yml", content=_docker_compose()),
    GeneratedTemplate(path="README.md", content=_root_readme(ir)),
    GeneratedTemplate(path=".env.example", content=(
      "APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\nCORS_ORIGIN=http://localhost:3000\nNEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n"
    )),
    GeneratedTemplate(path="backend/requirements.txt", content=_backend_requirements()),
    GeneratedTemplate(path="backend/.env.example", content=(
      "APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\nCORS_ORIGIN=http://localhost:3000\n"
        )),
        GeneratedTemplate(path=".autobuilder/README.md", content="# Mobile App — AutobuilderV2\n"),
        GeneratedTemplate(path=".autobuilder/ir.json", content=_json_pretty(ir.to_dict())),
        GeneratedTemplate(path=".autobuilder/determinism_signature.json", content=_determinism_signature_json()),
        GeneratedTemplate(path=".autobuilder/proof_report.json", content=_proof_report_json(ir)),
        GeneratedTemplate(path=".autobuilder/readiness_report.json", content=_readiness_report_json()),
        GeneratedTemplate(path=".autobuilder/validation_summary.json", content=_validation_summary_json()),
        GeneratedTemplate(path=".autobuilder/package_artifact_summary.json", content=_package_artifact_summary_json()),
        GeneratedTemplate(path=".autobuilder/proof_readiness_bundle.json", content=_proof_readiness_bundle_json()),
    ]


def mobile_lane_validation_plan() -> list[str]:
  return [
    "mobile_structure",
    "mobile_markers",
    "navigation_flows",
    "api_client_present",
    "flutter_pubspec_valid",
    "mobile_auth_scaffold",
    "mobile_state_surface",
    "mobile_offline_store_surface",
    "mobile_operator_surfaces",
  ]


def game_lane_templates(ir: AppIR) -> list[GeneratedTemplate]:
    return [
        GeneratedTemplate(path="project.godot", content=(
            "; Engine configuration file.\n[application]\nconfig/name=\"GameApp\"\n"
            "run/main_scene=\"res://scenes/Main.tscn\"\n"
        )),
        GeneratedTemplate(path="scenes/Main.tscn", content=(
            "[gd_scene load_steps=2 format=3]\n[node name=\"Main\" type=\"Node2D\"]\n"
        )),
    GeneratedTemplate(path="scenes/HUD.tscn", content=(
      "[gd_scene load_steps=2 format=3]\n[node name=\"HUD\" type=\"CanvasLayer\"]\n"
    )),
        GeneratedTemplate(path="scripts/main.gd", content=(
      "extends Node2D\n\nfunc _ready() -> void:\n\tprint('game lane initialized')\n"
      "\nfunc _process(_delta: float) -> void:\n\tpass\n"
        )),
        GeneratedTemplate(path="scripts/player.gd", content=(
      "extends CharacterBody2D\n\nvar speed := 120.0\n\nfunc _physics_process(_delta: float) -> void:\n\tpass\n"
    )),
    GeneratedTemplate(path="scripts/input_map.gd", content=(
      "extends Node\n\nfunc configure_default_input_map() -> void:\n\t# bounded scaffold: map actions in project settings\n\tpass\n"
    )),
    GeneratedTemplate(path="scripts/game_state.gd", content=(
      "extends Node\n\nvar score: int = 0\nvar health: int = 100\n\nfunc reset() -> void:\n\tscore = 0\n\thealth = 100\n"
    )),
    GeneratedTemplate(path="scripts/hud.gd", content=(
      "extends CanvasLayer\n\nfunc set_status(_score: int, _health: int) -> void:\n\tpass\n"
    )),
    GeneratedTemplate(path="docs/READINESS.md", content=_game_readiness_doc()),
    GeneratedTemplate(path="docs/EXPORT_AND_RUN.md", content=(
      "# Export and Run Guidance\n\n"
      "1. Open `project.godot` in Godot 4.x.\n"
      "2. Verify Main and HUD scenes load.\n"
      "3. Configure export presets for desktop/mobile as needed.\n"
      "4. Treat runtime networking and assets as operator extension work.\n"
    )),
    GeneratedTemplate(path="release/proof/PROOF_BUNDLE.md", content=_release_proof_bundle_doc()),
    GeneratedTemplate(path="release/runbook/OPERATOR_RUNBOOK.md", content=_operator_runbook_doc()),
    GeneratedTemplate(path="README.md", content=_root_readme(ir)),
    GeneratedTemplate(path="docker-compose.yml", content=_docker_compose()),
    GeneratedTemplate(path="backend/requirements.txt", content=_backend_requirements()),
    GeneratedTemplate(path="backend/api/__init__.py", content=""),
    GeneratedTemplate(path="backend/api/main.py", content=_backend_app(False, False)),
    GeneratedTemplate(path="backend/api/game.py", content=(
      "from fastapi import APIRouter\n\n"
      "from api.responses import ok_envelope\n\n"
      "router = APIRouter(prefix='/api/game', tags=['game'])\n\n"
      "@router.get('/state')\n"
      "def game_state() -> dict[str, object]:\n"
      "    return ok_envelope(data={'status': 'scaffold', 'mode': 'bounded_prototype'})\n"
        )),
        GeneratedTemplate(path=".autobuilder/README.md", content="# Game App — AutobuilderV2\n"),
        GeneratedTemplate(path=".autobuilder/ir.json", content=_json_pretty(ir.to_dict())),
        GeneratedTemplate(path=".autobuilder/determinism_signature.json", content=_determinism_signature_json()),
        GeneratedTemplate(path=".autobuilder/proof_report.json", content=_proof_report_json(ir)),
        GeneratedTemplate(path=".autobuilder/readiness_report.json", content=_readiness_report_json()),
        GeneratedTemplate(path=".autobuilder/validation_summary.json", content=_validation_summary_json()),
        GeneratedTemplate(path=".autobuilder/package_artifact_summary.json", content=_package_artifact_summary_json()),
        GeneratedTemplate(path=".autobuilder/proof_readiness_bundle.json", content=_proof_readiness_bundle_json()),
    ]


def game_lane_validation_plan() -> list[str]:
  return [
    "game_structure",
    "game_markers",
    "scene_flow",
    "godot_project_valid",
    "scripts_present",
    "hud_surface_present",
    "game_state_surface_present",
    "game_export_guidance_present",
  ]


def realtime_lane_templates(ir: AppIR) -> list[GeneratedTemplate]:
    return [
        GeneratedTemplate(path="frontend/lib/realtime-client.ts", content=(
      "// Realtime client\n"
      "export type StreamEvent = { channel: string; event: string; payload: Record<string, unknown> };\n"
      "\n"
      "export class RealtimeClient {\n"
      "  private socket: WebSocket | null = null;\n"
      "  constructor(private url: string) {}\n"
      "\n"
      "  connect(onEvent: (event: StreamEvent) => void): void {\n"
      "    this.socket = new WebSocket(this.url);\n"
      "    this.socket.onmessage = (msg) => {\n"
      "      try { onEvent(JSON.parse(msg.data) as StreamEvent); } catch { /* bounded scaffold */ }\n"
      "    };\n"
      "  }\n"
      "}\n"
    )),
    GeneratedTemplate(path="frontend/lib/alert-actions.ts", content=(
      "export function classifyAlert(eventType: string): 'notify' | 'escalate' | 'ignore' {\n"
      "  if (eventType.includes('critical')) return 'escalate';\n"
      "  if (eventType.includes('warning')) return 'notify';\n"
      "  return 'ignore';\n"
      "}\n"
        )),
        GeneratedTemplate(path="backend/connectors/sensors.py", content=(
      "from __future__ import annotations\n\n"
      "class SensorConnector:\n"
      "    def connect(self) -> None:\n"
      "        return None\n"
      "\n"
      "    def fetch_snapshot(self) -> dict[str, object]:\n"
      "        return {'source': 'sensor', 'status': 'stub', 'value': 0}\n"
        )),
    GeneratedTemplate(path="backend/realtime/channels.py", content=(
      "CHANNELS = ['ops.events', 'ops.alerts', 'ops.actions']\n"
    )),
    GeneratedTemplate(path="backend/realtime/events.py", content=(
      "from __future__ import annotations\n\n"
      "def normalize_event(raw: dict[str, object]) -> dict[str, object]:\n"
      "    return {\n"
      "        'channel': str(raw.get('channel', 'ops.events')),\n"
      "        'event': str(raw.get('event', 'unknown')),\n"
      "        'payload': dict(raw.get('payload', {})),\n"
      "    }\n"
    )),
        GeneratedTemplate(path="backend/realtime/world_state.py", content=(
      "from __future__ import annotations\n\n"
      "class WorldState:\n"
      "    def __init__(self) -> None:\n"
      "        self._state: dict[str, object] = {}\n"
      "\n"
      "    def apply_event(self, event: dict[str, object]) -> dict[str, object]:\n"
      "        key = str(event.get('event', 'unknown'))\n"
      "        self._state[key] = event.get('payload', {})\n"
      "        return self._state\n"
    )),
    GeneratedTemplate(path="backend/realtime/ws_gateway.py", content=(
      "from __future__ import annotations\n\n"
      "class RealtimeGateway:\n"
      "    def publish(self, channel: str, payload: dict[str, object]) -> dict[str, object]:\n"
      "        return {'published': True, 'channel': channel, 'payload': payload}\n"
    )),
    GeneratedTemplate(path="backend/services/alerts.py", content=(
      "from __future__ import annotations\n\n"
      "def route_alert(event: dict[str, object]) -> str:\n"
      "    name = str(event.get('event', ''))\n"
      "    if 'critical' in name:\n"
      "        return 'escalate'\n"
      "    if 'warning' in name:\n"
      "        return 'notify'\n"
      "    return 'ignore'\n"
        )),
        GeneratedTemplate(path="backend/api/__init__.py", content=""),
    GeneratedTemplate(path="backend/api/main.py", content=_realtime_backend_app()),
    GeneratedTemplate(path="backend/api/realtime.py", content=(
      "from fastapi import APIRouter\n\n"
      "from api.responses import ok_envelope\n"
      "from connectors.sensors import SensorConnector\n"
      "from realtime.events import normalize_event\n"
      "from realtime.world_state import WorldState\n\n"
      "router = APIRouter(prefix='/api/realtime', tags=['realtime'])\n"
      "_sensor = SensorConnector()\n"
      "_world = WorldState()\n\n"
      "@router.post('/ingest')\n"
      "def ingest(event: dict[str, object]) -> dict[str, object]:\n"
      "    normalized = normalize_event(event)\n"
      "    world = _world.apply_event(normalized)\n"
      "    return ok_envelope(data={'accepted': True, 'world_state_keys': sorted(world.keys())})\n"
    )),
        GeneratedTemplate(path="backend/api/admin.py", content=_backend_admin_router()),
        GeneratedTemplate(path="backend/api/operator.py", content=_backend_operator_router()),
        GeneratedTemplate(path="backend/api/audit.py", content=_backend_audit_router()),
        GeneratedTemplate(path="backend/api/config.py", content=_backend_config()),
        GeneratedTemplate(path="backend/api/responses.py", content=_backend_response_envelopes()),
        GeneratedTemplate(path="backend/api/logging.py", content=_backend_logging()),
        GeneratedTemplate(path="backend/requirements.txt", content=_backend_requirements()),
        GeneratedTemplate(path="docs/READINESS.md", content=_realtime_readiness_doc()),
        GeneratedTemplate(path="release/proof/PROOF_BUNDLE.md", content=_release_proof_bundle_doc()),
        GeneratedTemplate(path="release/runbook/OPERATOR_RUNBOOK.md", content=_operator_runbook_doc()),
        GeneratedTemplate(path="release/deploy/DEPLOYMENT_NOTES.md", content=_release_deployment_notes()),
        GeneratedTemplate(path="release/README.md", content=_release_bundle_readme()),
        GeneratedTemplate(path="docker-compose.yml", content=_docker_compose()),
        GeneratedTemplate(path="README.md", content=_root_readme(ir)),
        GeneratedTemplate(path=".env.example", content=(
          "APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\nCORS_ORIGIN=http://localhost:3000\nNEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n"
        )),
        GeneratedTemplate(path="backend/.env.example", content=(
          "APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\nCORS_ORIGIN=http://localhost:3000\n"
        )),
        GeneratedTemplate(path=".autobuilder/README.md", content="# Realtime System — AutobuilderV2\n"),
        GeneratedTemplate(path=".autobuilder/ir.json", content=_json_pretty(ir.to_dict())),
        GeneratedTemplate(path=".autobuilder/determinism_signature.json", content=_determinism_signature_json()),
        GeneratedTemplate(path=".autobuilder/proof_report.json", content=_proof_report_json(ir)),
        GeneratedTemplate(path=".autobuilder/readiness_report.json", content=_readiness_report_json()),
        GeneratedTemplate(path=".autobuilder/validation_summary.json", content=_validation_summary_json()),
        GeneratedTemplate(path=".autobuilder/package_artifact_summary.json", content=_package_artifact_summary_json()),
        GeneratedTemplate(path=".autobuilder/proof_readiness_bundle.json", content=_proof_readiness_bundle_json()),
    ]


def realtime_lane_validation_plan() -> list[str]:
  return [
    "realtime_structure",
    "realtime_markers",
    "channel_integrity",
    "world_state_present",
    "connector_present",
    "realtime_ws_gateway_present",
    "realtime_alert_action_path_present",
    "realtime_operator_surface_present",
  ]


def enterprise_agent_lane_templates(ir: AppIR) -> list[GeneratedTemplate]:
    return [
        GeneratedTemplate(path="backend/agent/runtime.py", content=(
      "from __future__ import annotations\n\n"
      "class AgentRuntime:\n"
      "    def run(self, task: str, actor_role: str = 'member') -> dict[str, object]:\n"
      "        return {'status': 'completed', 'task': task, 'actor_role': actor_role}\n"
        )),
        GeneratedTemplate(path="backend/agent/task_router.py", content=(
      "from __future__ import annotations\n\n"
      "ROLE_QUEUE = {'admin': 'priority', 'operator': 'operations', 'member': 'standard'}\n\n"
      "class TaskRouter:\n"
      "    def route(self, task: str, role: str) -> str:\n"
      "        queue = ROLE_QUEUE.get(role, 'standard')\n"
      "        return f'{queue}:{task}'\n"
        )),
        GeneratedTemplate(path="backend/agent/audit.py", content=(
      "class AuditService:\n"
      "    def record(self, event: dict[str, object]) -> None:\n"
      "        _ = event\n"
      "        return None\n"
    )),
    GeneratedTemplate(path="backend/agent/briefing.py", content=(
      "from __future__ import annotations\n\n"
      "def build_briefing(summary: str, pending: list[str]) -> dict[str, object]:\n"
      "    return {'summary': summary, 'pending_items': pending, 'status': 'scaffold'}\n"
        )),
        GeneratedTemplate(path="frontend/components/workflow-board.tsx", content=(
      "// Workflow board component\n"
      "export function WorkflowBoard() {\n"
      "  return <div data-testid=\"workflow-board\">workflow board scaffold</div>;\n"
      "}\n"
        )),
        GeneratedTemplate(path="backend/workflows/router.py", content=(
      "from __future__ import annotations\n\n"
      "WORKFLOW_BY_ROLE = {\n"
      "    'admin': ['approve_change', 'view_reports'],\n"
      "    'operator': ['triage_alert', 'resume_mission'],\n"
      "    'member': ['submit_task'],\n"
      "}\n\n"
      "class WorkflowRouter:\n"
      "    def route_for_role(self, role: str) -> list[str]:\n"
      "        return WORKFLOW_BY_ROLE.get(role, ['submit_task'])\n"
    )),
    GeneratedTemplate(path="backend/workflows/approvals.py", content=(
      "from __future__ import annotations\n\n"
      "def requires_approval(action: str) -> bool:\n"
      "    return action in {'deploy', 'delete', 'billing_change', 'role_grant'}\n"
        )),
        GeneratedTemplate(path="backend/memory/state_store.py", content=(
      "from __future__ import annotations\n\n"
      "class StateStore:\n"
      "    def __init__(self) -> None:\n"
      "        self._store: dict[str, dict[str, object]] = {}\n"
      "\n"
      "    def write(self, key: str, payload: dict[str, object]) -> None:\n"
      "        self._store[key] = payload\n"
      "\n"
      "    def read(self, key: str) -> dict[str, object]:\n"
      "        return self._store.get(key, {})\n"
        )),
        GeneratedTemplate(path="backend/api/__init__.py", content=""),
    GeneratedTemplate(path="backend/api/main.py", content=_enterprise_backend_app()),
    GeneratedTemplate(path="backend/api/enterprise.py", content=(
      "from fastapi import APIRouter\n\n"
      "from agent.briefing import build_briefing\n"
      "from api.responses import ok_envelope\n"
      "from memory.state_store import StateStore\n"
      "from workflows.router import WorkflowRouter\n\n"
      "router = APIRouter(prefix='/api/enterprise', tags=['enterprise'])\n"
      "_router = WorkflowRouter()\n"
      "_state = StateStore()\n\n"
      "@router.get('/briefing/{role}')\n"
      "def briefing(role: str) -> dict[str, object]:\n"
      "    tasks = _router.route_for_role(role)\n"
      "    return ok_envelope(data=build_briefing(f'role={role}', tasks))\n\n"
      "@router.post('/report/{run_id}')\n"
      "def report(run_id: str, payload: dict[str, object]) -> dict[str, object]:\n"
      "    _state.write(run_id, payload)\n"
      "    return ok_envelope(data={'stored': True, 'run_id': run_id})\n"
    )),
        GeneratedTemplate(path="backend/api/admin.py", content=_backend_admin_router()),
        GeneratedTemplate(path="backend/api/operator.py", content=_backend_operator_router()),
        GeneratedTemplate(path="backend/api/audit.py", content=_backend_audit_router()),
        GeneratedTemplate(path="backend/api/config.py", content=_backend_config()),
        GeneratedTemplate(path="backend/api/responses.py", content=_backend_response_envelopes()),
        GeneratedTemplate(path="backend/api/logging.py", content=_backend_logging()),
        GeneratedTemplate(path="backend/requirements.txt", content=_backend_requirements()),
        GeneratedTemplate(path="docs/READINESS.md", content=_enterprise_readiness_doc()),
        GeneratedTemplate(path="release/proof/PROOF_BUNDLE.md", content=_release_proof_bundle_doc()),
        GeneratedTemplate(path="release/runbook/OPERATOR_RUNBOOK.md", content=_operator_runbook_doc()),
        GeneratedTemplate(path="release/deploy/DEPLOYMENT_NOTES.md", content=_release_deployment_notes()),
        GeneratedTemplate(path="release/README.md", content=_release_bundle_readme()),
        GeneratedTemplate(path="docker-compose.yml", content=_docker_compose()),
        GeneratedTemplate(path="README.md", content=_root_readme(ir)),
        GeneratedTemplate(path=".env.example", content=(
          "APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\nCORS_ORIGIN=http://localhost:3000\nNEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n"
        )),
        GeneratedTemplate(path="backend/.env.example", content=(
          "APP_ENV=local\nAPP_VERSION=0.1.0\nDATABASE_URL=postgresql://postgres:postgres@db:5432/app\nCORS_ORIGIN=http://localhost:3000\n"
        )),
        GeneratedTemplate(path=".autobuilder/README.md", content="# Enterprise Agent System — AutobuilderV2\n"),
        GeneratedTemplate(path=".autobuilder/ir.json", content=_json_pretty(ir.to_dict())),
        GeneratedTemplate(path=".autobuilder/determinism_signature.json", content=_determinism_signature_json()),
        GeneratedTemplate(path=".autobuilder/proof_report.json", content=_proof_report_json(ir)),
        GeneratedTemplate(path=".autobuilder/readiness_report.json", content=_readiness_report_json()),
        GeneratedTemplate(path=".autobuilder/validation_summary.json", content=_validation_summary_json()),
        GeneratedTemplate(path=".autobuilder/package_artifact_summary.json", content=_package_artifact_summary_json()),
        GeneratedTemplate(path=".autobuilder/proof_readiness_bundle.json", content=_proof_readiness_bundle_json()),
    ]


def enterprise_agent_lane_validation_plan() -> list[str]:
  return [
    "enterprise_structure",
    "enterprise_markers",
    "approval_flows",
    "audit_service_present",
    "task_router_present",
    "multi_role_workflow_surface",
    "memory_state_surface",
    "enterprise_reporting_surface",
  ]


def get_lane_validation_plan(app_type: str) -> list[str]:
    if app_type == "mobile_app":
        return mobile_lane_validation_plan()
    if app_type == "game_app":
        return game_lane_validation_plan()
    if app_type == "realtime_system":
        return realtime_lane_validation_plan()
    if app_type == "enterprise_agent_system":
        return enterprise_agent_lane_validation_plan()
    return _build_validation_plan()
