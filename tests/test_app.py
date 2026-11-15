from __future__ import annotations

from pathlib import Path

import app


class FakeSupabaseResult:
    def __init__(self, data):
        self.data = data


class FakeSupabaseQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.action = "select"
        self.payload = None
        self.filters = []
        self.ordering = []
        self.limit_value = None

    def select(self, *_args, **_kwargs):
        if self.action == "select":
            self.action = "select"
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def delete(self):
        self.action = "delete"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self.ordering.append((column, desc))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])
        if self.action == "insert":
            inserted = dict(self.payload)
            inserted["id"] = self.client.next_id
            self.client.next_id += 1
            rows.append(inserted)
            return FakeSupabaseResult([inserted])

        matches = [
            row for row in rows
            if all(row.get(column) == value for column, value in self.filters)
        ]
        if self.action == "update":
            for row in matches:
                row.update(self.payload)
            return FakeSupabaseResult(matches)
        if self.action == "delete":
            self.client.tables[self.table_name] = [row for row in rows if row not in matches]
            return FakeSupabaseResult(matches)

        for column, descending in reversed(self.ordering):
            matches.sort(key=lambda row: row.get(column) or "", reverse=descending)
        if self.limit_value is not None:
            matches = matches[:self.limit_value]
        return FakeSupabaseResult(matches)


class FakeSupabaseClient:
    def __init__(self):
        self.tables = {"obras": [], "movimentos_financeiros": [], "tarefas": []}
        self.next_id = 1
        self.queried_tables = []

    def table(self, table_name):
        self.queried_tables.append(table_name)
        return FakeSupabaseQuery(self, table_name)


def test_finance_and_tasks_are_saved_to_supabase_for_active_work(monkeypatch):
    client = FakeSupabaseClient()
    monkeypatch.setattr(app, "get_data_client", lambda: client)
    monkeypatch.setattr(app.st, "session_state", {"active_work_id": None})

    work_id = app.create_or_update_work(
        nome="Obra segura",
        cliente="Cliente",
        local="Lisboa",
        gestor="João",
        data_inicio="2026-11-01",
        data_fim="2026-12-01",
        valor_obra=12000,
        tipo_iva="Com IVA",
        iva=23,
        status="Em execução",
    )
    app.add_financial_entry("Receita", "Adiantamento", "Pagamentos", 1500, "2026-11-02")
    app.add_financial_entry("Despesa", "Cimento", "Materiais", 500, "2026-11-03")
    task_id = app.add_task(
        "Preparar fundação", "Escavação e nivelamento", "João", "Alta",
        "2026-11-05", "2026-11-08",
    )

    summary = app.get_financial_summary()
    tasks = app.get_tasks()
    assert work_id == 1
    assert summary == {"receitas": 1500.0, "despesas": 500.0, "saldo": 1000.0, "registos": 2}
    assert task_id == 4
    assert tasks[0]["titulo"] == "Preparar fundação"
    assert all(row["obra_id"] == work_id for row in client.tables["movimentos_financeiros"])
    assert client.tables["tarefas"][0]["obra_id"] == work_id
    assert "obras" in client.queried_tables
    assert "movimentos_financeiros" in client.queried_tables
    assert "tarefas" in client.queried_tables


def test_translation_keys_cover_required_languages():
    assert app.translate_text("dashboard", "pt") == "Dashboard"
    assert app.translate_text("dashboard", "es") == "Panel"
    assert app.translate_text("dashboard", "en") == "Dashboard"
    assert app.translate_text("dashboard", "de") == "Übersicht"
    assert app.translate_text("dashboard", "fr") == "Tableau de bord"


def test_session_role_comes_from_app_metadata_and_defaults_to_info():
    from types import SimpleNamespace

    manager_session = SimpleNamespace(
        user=SimpleNamespace(app_metadata={"role": "manager"})
    )
    builder_session = SimpleNamespace(
        user=SimpleNamespace(app_metadata={"role": "builder"})
    )
    info_session = SimpleNamespace(
        user=SimpleNamespace(app_metadata={"role": "info"})
    )
    user_metadata_only = SimpleNamespace(
        user=SimpleNamespace(
            app_metadata={},
            user_metadata={"role": "manager"},
        )
    )
    unknown_role = SimpleNamespace(
        user=SimpleNamespace(app_metadata={"role": "admin"})
    )

    assert app.get_session_role(manager_session) == "manager"
    assert app.get_session_role(builder_session) == "builder"
    assert app.get_session_role(info_session) == "info"
    assert app.get_session_role(user_metadata_only) == "info"
    assert app.get_session_role(unknown_role) == "info"


def test_role_menu_permissions():
    assert app.get_menu_options("manager", "en") == [
        "Obras", "Dashboard", "Configuration", "Finance", "Planning", "Reports"
    ]
    assert app.get_menu_options("builder", "en") == [
        "Obras", "Dashboard", "Planning"
    ]
    assert app.get_menu_options("info", "en") == ["Obras", "Dashboard"]


def test_username_login_exchanges_credentials_and_sets_session(monkeypatch):
    request = {}
    auth_calls = []

    class SuccessfulResponse:
        is_success = True
        status_code = 200

        @staticmethod
        def json():
            return {"access_token": "access", "refresh_token": "refresh"}

    class FakeAuth:
        @staticmethod
        def set_session(access_token, refresh_token):
            auth_calls.append((access_token, refresh_token))

    class FakeClient:
        auth = FakeAuth()

    def fake_post(url, headers, json, timeout):
        request.update(url=url, headers=headers, json=json, timeout=timeout)
        return SuccessfulResponse()

    monkeypatch.setattr(
        app,
        "get_supabase_config",
        lambda: ("https://example.supabase.co", "publishable-key"),
    )
    monkeypatch.setattr(app.httpx, "post", fake_post)

    authenticated, message = app.authenticate_username_password(FakeClient(), "  joao  ", "password-value")
    assert authenticated is True
    assert message == ""
    assert request["url"] == "https://example.supabase.co/functions/v1/username-login"
    assert request["headers"]["apikey"] == "publishable-key"
    assert request["json"] == {"username": "joao", "password": "password-value"}
    assert auth_calls == [("access", "refresh")]


def test_missing_username_function_is_reported_clearly(monkeypatch):
    class MissingFunctionResponse:
        is_success = False
        status_code = 404

    monkeypatch.setattr(
        app,
        "get_supabase_config",
        lambda: ("https://example.supabase.co", "publishable-key"),
    )
    monkeypatch.setattr(app.httpx, "post", lambda *_args, **_kwargs: MissingFunctionResponse())

    authenticated, message = app.authenticate_username_password(object(), "joao", "password")

    assert authenticated is False
    assert "username-login" in message
    assert "deploy" in message


def test_supabase_config_reads_key_from_windows_credential(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.setattr(app, "read_windows_credential", lambda: "credential-key")

    assert app.get_supabase_config() == (
        "https://example.supabase.co",
        "credential-key",
    )


def test_reads_domain_password_credential(monkeypatch):
    import sys
    from types import SimpleNamespace

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setitem(
        sys.modules,
        "keyring",
        SimpleNamespace(get_password=lambda *_args: None),
    )

    def fake_cred_read(target, credential_type, _flags):
        if target == app.SUPABASE_CREDENTIAL_TARGET and credential_type == 2:
            return {"CredentialBlob": "credential-key".encode("utf-16-le")}
        raise OSError("Credential not found")

    monkeypatch.setitem(
        sys.modules,
        "win32cred",
        SimpleNamespace(
            CRED_TYPE_GENERIC=1,
            CRED_TYPE_DOMAIN_PASSWORD=2,
            CredRead=fake_cred_read,
        ),
    )

    assert app.read_windows_credential() == "credential-key"


def test_supabase_connection_uses_authenticated_data_client(monkeypatch):
    client = FakeSupabaseClient()
    monkeypatch.setattr(app, "get_data_client", lambda: client)
    connected, message = app.test_supabase_connection()

    assert connected is True
    assert "autenticada" in message
    assert client.queried_tables == ["obras"]


def test_supabase_connection_fails_closed_when_authenticated_query_fails(monkeypatch):
    class BrokenClient:
        @staticmethod
        def table(_table_name):
            raise RuntimeError("permission denied")

    monkeypatch.setattr(app, "get_data_client", lambda: BrokenClient())

    connected, message = app.test_supabase_connection()

    assert connected is False
    assert "políticas RLS" in message


def test_multi_work_crud_and_active_selection_uses_supabase(monkeypatch):
    client = FakeSupabaseClient()
    session_state = {"active_work_id": None}
    monkeypatch.setattr(app, "get_data_client", lambda: client)
    monkeypatch.setattr(app.st, "session_state", session_state)

    work_id_a = app.create_or_update_work(
        nome="Obra A",
        cliente="Cliente A",
        local="Lisboa",
        gestor="Ana",
        data_inicio="2026-11-10",
        data_fim="2026-12-10",
        valor_obra=25000,
        tipo_iva="Com IVA",
        iva=23,
        status="Planeamento",
    )
    work_id_b = app.create_or_update_work(
        nome="Obra B",
        cliente="Cliente B",
        local="Porto",
        gestor="Bento",
        data_inicio="2026-11-15",
        data_fim="2026-12-15",
        valor_obra=40000,
        tipo_iva="Sem IVA",
        iva=0,
        status="Em execução",
    )

    assert work_id_a > 0
    assert work_id_b > 0

    app.set_active_work(work_id_b)
    active = app.get_active_work()
    assert active["nome"] == "Obra B"

    works = app.list_works()
    assert len(works) == 2
    assert {item["nome"] for item in works} == {"Obra A", "Obra B"}
    assert session_state["active_work_id"] == work_id_b

    app.delete_work(work_id_a)
    works_after = app.list_works()
    assert len(works_after) == 1
    assert works_after[0]["nome"] == "Obra B"
    assert "configuracao_obra" not in client.tables


def test_app_has_no_local_sqlite_storage():
    assert not hasattr(app, "DB_PATH")
    assert not hasattr(app, "get_connection")
    assert not hasattr(app, "init_db")


def test_database_migrations_do_not_grant_anonymous_data_access():
    migration_dir = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
    initial_schema = (migration_dir / "20261111_initial_schema.sql").read_text(encoding="utf-8").lower()
    hardening = (migration_dir / "20261115_secure_authenticated_access.sql").read_text(encoding="utf-8").lower()
    usernames = (migration_dir / "20261112_usernames.sql").read_text(encoding="utf-8").lower()

    assert "to anon" not in initial_schema
    assert "from public, anon" in hardening
    assert "from public, anon, authenticated" in usernames
    assert "grant select on table public.user_profiles to authenticated" not in usernames
