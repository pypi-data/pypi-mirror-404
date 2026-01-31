import os
import json
import subprocess
from pathlib import Path

class PythonProgramGenerator:
    def __init__(self, project_name: str):
        self.project_name = project_name

    def generate(self, prompt: str):
        print(f"Generating project: {self.project_name}")
        print(f"Prompt: {prompt}")

# =========================
# LLM Architecture Reasoner
# =========================
class ArchitectureReasoner:
    """
    Replace reason() with OpenAI / local LLM call if needed.
    """
    def reason(self, prompt: str) -> dict:
        prompt = prompt.lower()

        architecture = {
            "pattern": "layered",
            "async": "fastapi" in prompt,
            "db_layer": "repository",
            "service_layer": True
        }

        if "monolith" in prompt:
            architecture["pattern"] = "monolith"
        if "microservice" in prompt:
            architecture["pattern"] = "microservice"

        return architecture


# =========================
# Integration Conflict Detection
# =========================
class ConflictDetector:
    CONFLICTS = [
        ("flask", "fastapi"),
        ("sqlite", "postgresql+async"),
    ]

    def detect(self, framework, integrations):
        conflicts = []
        for a, b in self.CONFLICTS:
            if a in integrations and b in integrations:
                conflicts.append((a, b))
        return conflicts

    def auto_fix(self, conflicts, integrations):
        for a, b in conflicts:
            integrations.remove(a)
        return integrations


# =========================
# Docker + CI Generator
# =========================
class InfraGenerator:
    def dockerfile(self):
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
        )

    def github_actions(self):
        return (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v3\n"
            "      - uses: actions/setup-python@v4\n"
            "        with:\n"
            "          python-version: '3.11'\n"
            "      - run: pip install -r requirements.txt\n"
            "      - run: python -m compileall app\n"
        )


# =========================
# Self-Healing Validator
# =========================
class SelfHealingValidator:
    def heal(self, project_path, deps, env_vars):
        fixed = []

        req = project_path / "requirements.txt"
        env = project_path / ".env.example"

        req_text = req.read_text() if req.exists() else ""
        for d in deps:
            if d not in req_text:
                req_text += f"\n{d}"
                fixed.append(f"Added dependency: {d}")

        req.write_text(req_text.strip())

        env_text = env.read_text() if env.exists() else ""
        for v in env_vars:
            if v not in env_text:
                env_text += f"\n{v}="
                fixed.append(f"Added env var: {v}")

        env.write_text(env_text.strip())

        return fixed

class ProjectUpgrader:
    def upgrade(self, project_path, target_version):
        current = self._read_version(project_path)

        if current == "1.0" and target_version == "2.0":
            self._apply_v2(project_path)

    def _apply_v2(self, project_path):
        print("Applying v2 architecture changes...")
        # AST refactor
        # Add async services
        # Update CI
