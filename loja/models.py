"""The catalog is persisted in JSON through loja.catalog.repository.

Django owns auth, sessions and permissions in SQLite. No product ORM models or
schema migrations are introduced by this structural refactor.
"""
