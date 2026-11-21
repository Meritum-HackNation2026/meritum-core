"""behave hooks: every scenario starts from a clean context.

Steps call meritum_core's public API with in-process fakes only; nothing here
talks to a database, a provider or another service (AGENTS.md: no e2e in CI).
"""
