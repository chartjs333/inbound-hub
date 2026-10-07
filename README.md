# Inbound Hub

Universal inbound coordination service for external sources such as Email, Telegram, folders and future adapters.

## Purpose

Inbound Hub:
- watches configured sources;
- converts source-specific input into a normalized inbound event;
- classifies intent and resolves project context;
- produces sprint proposals;
- submits proposals to nginx-qa through a versioned API;
- publishes operator-facing notifications, including Telegram;
- keeps source ingestion separate from sprint execution.

nginx-qa remains responsible for pending-sprints, review, Play/Start, managed start-from-git and execution.

## Planned architecture

```text
Email / Telegram / Folder / Other adapters
                 |
          Normalized Event
                 |
        Inbound Coordinator
                 |
      Classification / Routing
                 |
          Sprint Proposal
                 |
          nginx-qa API
                 |
          Pending Sprints
                 |
         Operator Review / Play
```

## Technology

Initial implementation: Python.

Planned components:
- FastAPI service API
- asyncio background workers
- typed event/config models
- SQLite initially, PostgreSQL-ready persistence boundary
- Windows background service
- small Windows tray controller
- versioned Markdown + YAML communication profiles

## Status

Architecture/bootstrap repository. No live credentials or production configuration belong in Git.
