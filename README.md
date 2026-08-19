# Project Atlas

Project Atlas is an enterprise-grade AI Infrastructure Operations Platform.

Its purpose is to help infrastructure teams understand complex environments, analyze operational problems, assess risk, and generate explainable recommendations without allowing AI to perform unauthorized infrastructure changes.

Atlas is not a traditional monitoring tool and it is not an autonomous operator. It is designed as an intelligent decision-support platform that can correlate infrastructure data, vendor knowledge, operational history, topology, health checks, and human-approved workflows.

The project has an approved documentation baseline (initial `1.0.0 Approved` baseline on 2026-08-03 for all 47 governed documents; individual documents may carry a later version after subsequent approved revisions — see [`docs/README.md`](docs/README.md))

---

## Executive Summary

Modern enterprise infrastructure spans storage systems, SAN switches, virtualization platforms, operating systems, backup platforms, directory services, network services, and vendor-specific tools. These domains are often managed through separate consoles, APIs, scripts, runbooks, and operational knowledge.

Project Atlas aims to create a unified AI-assisted operations platform for this environment. It uses modular MCP connectors, an infrastructure knowledge graph, retrieval-augmented generation, AI agents, policy controls, and enterprise governance to help engineers investigate incidents, understand impact, and prepare safe remediation plans.

Atlas is built for enterprise environments from the beginning. Security, RBAC, LDAP and Active Directory integration, audit logging, Syslog, SIEM integration, explainability, approval workflows, and reproducible deployment are core requirements, not optional later additions.

---

## Core Principle

> **AI assists. Humans decide.**

Atlas may analyze, correlate, explain, recommend, prepare plans, estimate impact, and propose rollback steps. It must not execute operationally risky actions without explicit human approval and policy control.

---

## Product Vision

Atlas is the AI-powered operating platform that understands enterprise infrastructure, reasons about operational problems, and assists engineers in making safe, explainable, and informed decisions.

Key capabilities include:

- Infrastructure discovery and relationship mapping
- Infrastructure knowledge graph (`ATLAS-026`)
- Vendor and operational knowledge management (`ATLAS-015` / `ATLAS-027`)
- Health checks and scheduled assessments (`ATLAS-023`)
- Root cause analysis (`ATLAS-042`)
- Change impact analysis (`ATLAS-044`)
- Risk scoring and service interruption estimation
- Recommendation and rollback planning (`ATLAS-043`)
- Human-controlled approval workflows (`ATLAS-037`)
- Enterprise audit and compliance evidence (`ATLAS-032`)

---

## Development Status

- **Documentation Baseline**: initial `1.0.0 Approved` on 2026-08-03 (47 governed documents, 78 ADRs at baseline; ADRs are added over time — see `docs/adr/README.md` for the current count); documents are versioned independently after the baseline — see each document's `Version` field
- **Implementation Status**: MVP-001 through MVP-005 completed (`ATLAS-IMP-001` through `ATLAS-IMP-005`) — the full MVP vertical slice in `docs/002_Product_Requirements.md` Section 10. Runnable backend (FastAPI; local + LDAP/AD authentication per ADR-079; RBAC; audit log; a real read-only SAN fabric connector, simulator, and inventory/graph reconciliation; one knowledge source with placeholder local embeddings; scheduled connector health checks; an investigation/RCA/change-impact/recommendation workflow with a human approval gate and a DLP guardrail; syslog audit export; backup/restore and SBOM/release-manifest scripts) and a matching React 19 + Vite frontend. RCA and recommendation generation are documented rule-engine placeholders pending ATLAS-041 (no local/private AI model is configured — open in Section 16). Verified against real PostgreSQL: 27/27 backend tests passing, mypy strict and ruff clean, frontend typecheck/lint clean. See [`docs/implementation/IMPLEMENTATION_TRACKER.md`](docs/implementation/IMPLEMENTATION_TRACKER.md).

---

## Repository Structure

```text
AGENTS.md          AI development rules and instruction precedence
README.md          Main project overview and setup instructions
docs/              Product, architecture, platform, security, AI, and development documents
backend/           FastAPI backend modular-monolith API, models, and Alembic migrations
frontend/          React 19 + TypeScript + Vite operations workspace shell
scripts/           Bootstrap, dev server, quality-check, and admin-bootstrap scripts
docker-compose.yml PostgreSQL 18 for local development
pyproject.toml     Python project dependencies and tooling configuration
.env.example       Template for local environment configuration
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+ (for the frontend; not required to run the backend alone)
- Docker & Docker Compose (for local PostgreSQL 18), or a PostgreSQL 18 instance reachable via `ATLAS_DATABASE_URL`

### Local Quickstart

1. **Bootstrap dependencies**:
   ```cmd
   scripts\bootstrap.cmd
   ```
2. **Start PostgreSQL, run migrations, and launch dev servers**:
   ```cmd
   scripts\dev.cmd
   ```
   - **Web Workspace Shell**: `http://localhost:5173`
   - **Interactive API Documentation**: `http://localhost:8000/docs`
   - **System Health Endpoint**: `http://localhost:8000/api/health`
3. **Create the first local administrator** (ATLAS-030 Section 11 bootstrap):
   ```cmd
   scripts\bootstrap_admin.cmd
   ```
   Prints a one-time generated password; you must change it on first login.
4. **Development identity (ADR-003)**: with `ATLAS_ENABLE_DEVELOPMENT_IDENTITY=true` (the `.env.example` default) and `ATLAS_ENVIRONMENT` in `development`/`test`, use "Continue as Local Operator" on the login page. It grants only `identity.self.read` — it is not an administrator.
5. **Run quality checks**:
   ```cmd
   scripts\check.cmd
   ```

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the documentation lifecycle, review and approval workflow, versioning policy, and pull request expectations.
