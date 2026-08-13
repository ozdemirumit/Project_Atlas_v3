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
- **Implementation Status**: Not started. No implementation task has been opened yet; see [`docs/implementation/IMPLEMENTATION_TRACKER.md`](docs/implementation/IMPLEMENTATION_TRACKER.md).

---

## Repository Structure

```text
AGENTS.md          AI development rules and instruction precedence
README.md          Main project overview and setup instructions
docs/              Product, architecture, platform, security, AI, and development documents
```

The architecture documents (`docs/010`-`docs/016`) and development contracts (`docs/050`-`docs/059`) describe a planned `backend/` (FastAPI), `frontend/` (React 19 + TypeScript + Vite), `scripts/`, `docker-compose.yml`, and `pyproject.toml`. None of these exist yet — they will be created when an implementation task is explicitly opened.

---

## Getting Started

There is no runnable implementation yet. Once an implementation task is opened, this section will describe prerequisites and local quickstart steps consistent with `docs/038_Deployment_and_Bootstrap.md` and the accepted ADRs (`ADR-001`, `ADR-002`, `ADR-003`).

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the documentation lifecycle, review and approval workflow, versioning policy, and pull request expectations.
