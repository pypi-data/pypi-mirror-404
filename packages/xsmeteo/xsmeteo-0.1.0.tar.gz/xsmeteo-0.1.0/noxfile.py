from __future__ import annotations

import nox

nox.options.sessions = ["lint", "type_check", "tests"]


@nox.session
def lint(session: nox.Session) -> None:
    """Run linting checks."""
    session.install("ruff")
    session.run("ruff", "check", "src")
    session.run("ruff", "format", "--check", "src")


@nox.session
def type_check(session: nox.Session) -> None:
    """Run type checking."""
    session.install("mypy", "msgspec", "httpx", "pytest")
    session.run("mypy", "src")


@nox.session
def tests(session: nox.Session) -> None:
    """Run tests."""
    session.install("pytest", "pytest-asyncio", "httpx", "msgspec")
    session.install(".")
    session.run("pytest", "tests")
