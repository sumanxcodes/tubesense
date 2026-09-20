---
name: git-workflow
description: >-
  Use this skill whenever tasked with code generation, file modification, or deployment requests to enforce version control standards, branch management, and CI/CD protocols for the TubeSense architecture.
---

# Agent 6: CI/CD & DevOps (Git Skill)

## 1. Executive Summary
**Role:** Enforces version control standards, maintains repository hygiene, and automates testing and deployment pipelines to ensure zero-downtime updates to the TubeSense architecture.
**Trigger:** Code generation, file modification, or deployment requests.
**Tech Stack:** Git, GitHub Actions (or GitLab CI), Pytest, Ruff, Bandit (SAST), Docker, Google Artifact Registry, Google Cloud Run.

## 2. Version Control Engine (Git Standards)
The agent is constrained by a strict ruleset for local and remote repository interactions to prevent merge conflicts and ensure a clean history.

### Branching Strategy (Trunk-Based Development)
*   `main`: Production-ready, deployable code. Protected branch requiring passing status checks and reviews.
*   `feature/<ticket-or-name>`: For new capabilities (e.g., `feature/bertopic-tuning`).
*   `fix/<ticket-or-name>`: For bug resolution (e.g., `fix/api-pagination-error`).
*   `chore/<ticket-or-name>`: For maintenance, dependency updates, and non-functional changes.

### Conventional Commits
The agent must prefix all commits to automate semantic versioning and changelog generation:
*   `feat:` New features (triggers minor version bump).
*   `fix:` Bug fixes (triggers patch version bump).
*   `chore:` Dependency updates, CI/CD tweaks, or routine tasks.
*   `refactor:` Code restructuring without changing behavior.
*   `test:` Adding missing tests or correcting existing tests.
*   *Example:* `feat(agent-4): upgrade sentiment model to multi-lingual roberta`

## 3. CI/CD Pipeline Definition
The agent is programmed to write, trigger, and monitor standard YAML pipelines. The pipeline is divided into three critical stages: Quality, Security, and Delivery.

### Stage 1: Continuous Integration (Quality & Security)
Triggered on every Pull Request (PR) to the `main` branch.
*   **Linting & Formatting:** Runs `ruff` to enforce PEP-8 standards and catch syntax errors.
*   **Static Application Security Testing (SAST):** Runs `bandit` across the Python codebase to detect hardcoded API keys, injection vulnerabilities, and unsafe deserialization.
*   **Unit Testing:** Runs `pytest`. The agent explicitly tests the Pydantic schemas (`schemas.py`) by mocking the inputs from the YouTube API to ensure Data Contracts hold up under edge cases (e.g., null values, empty strings).

### Stage 2: Continuous Deployment (Delivery)
Triggered on successful merge to the `main` branch.
*   **Containerization:** The agent builds a Docker image containing the FastAPI backend, Streamlit frontend, and PyTorch dependencies.
*   **Container Security Scanning:** Runs `Trivy` on the built Docker image to scan for OS-level vulnerabilities in the base Python image before allowing it to be published.
*   **Registry Push & Deploy:** Pushes the secure image to Google Artifact Registry (GAR) and updates the Google Cloud Run service with the new image tag, routing 100% of traffic to the new revision seamlessly.

## 4. Agent Execution Protocol (Code to Deploy)
When tasked with a codebase change, the agent executes the following operational loop:

1.  **Branch Creation:** `git checkout -b feature/[feature-name]`
2.  **Implementation:** Writes/Modifies code based on architectural requirements and Pydantic schemas.
3.  **Staging:** `git add .`
4.  **Committing:** `git commit -m "feat([scope]): [description]"`
5.  **Pushing:** `git push origin feature/[feature-name]`
6.  **PR Generation:** Generates a Pull Request with a structured markdown description detailing the changes, testing steps, and linked issues.
7.  **Monitoring:** Monitors CI/CD GitHub Actions status.
8.  **Error Handling (If CI fails):** Reads the error logs (e.g., Pytest failure, Bandit security flag), automatically writes a patch, and pushes the fix.
9.  **Deployment (If CI passes):** Requests approval for merge to `main` for deployment.
