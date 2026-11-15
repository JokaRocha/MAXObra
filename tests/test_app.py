from __future__ import annotations

import app


def test_finance_and_tasks_work_with_sqlite(tmp_path, monkeypatch):
    test_db = tmp_path / "obra_manager_test.db"
    monkeypatch.setattr(app, "DB_PATH", test_db)

    app.init_db()

    app.add_financial_entry(
        tipo="Receita",
        descricao="Pagamento inicial",
        categoria="Adiantamento",
        valor=1500.00,
        data="2026-11-01",
        observacoes="Recebido",
    )
    app.add_financial_entry(
        tipo="Despesa",
        descricao="Compra de materiais",
        categoria="Materiais",
        valor=500.00,
        data="2026-11-02",
        observacoes="Cimento",
    )

    summary = app.get_financial_summary()
    assert summary["receitas"] == 1500.0
    assert summary["despesas"] == 500.0
    assert summary["saldo"] == 1000.0

    task_id = app.add_task(
        titulo="Preparar fundação",
        descricao="Executar escavação e nivelamento",
        responsavel="João",
        prioridade="Alta",
        data_inicio="2026-11-05",
        data_fim="2026-11-08",
        status="Pendente",
    )

    tasks = app.get_tasks()
    assert task_id > 0
    assert len(tasks) == 1
    assert tasks[0]["titulo"] == "Preparar fundação"
    assert tasks[0]["status"] == "Pendente"


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


def test_supabase_connection_uses_key_without_exposing_it(monkeypatch):
    request = {}

    class SuccessfulResponse:
        is_success = True
        status_code = 200

    def fake_get(url, params, headers, timeout):
        request.update(url=url, params=params, headers=headers, timeout=timeout)
        return SuccessfulResponse()

    monkeypatch.setattr(
        app,
        "get_supabase_config",
        lambda: ("https://example.supabase.co", "credential-key"),
    )
    monkeypatch.setattr(app.httpx, "get", fake_get)

    connected, message = app.test_supabase_connection()

    assert connected is True
    assert "credential-key" not in message
    assert request["url"] == "https://example.supabase.co/rest/v1/obras"
    assert request["params"] == {"select": "id", "limit": 1}
    assert request["headers"] == {"apikey": "credential-key"}


def test_missing_supabase_table_still_confirms_project_access(monkeypatch):
    class MissingTableResponse:
        is_success = False
        status_code = 404

        @staticmethod
        def json():
            return {"code": "PGRST205"}

    monkeypatch.setattr(
        app,
        "get_supabase_config",
        lambda: ("https://example.supabase.co", "credential-key"),
    )
    monkeypatch.setattr(app.httpx, "get", lambda *_args, **_kwargs: MissingTableResponse())

    connected, message = app.test_supabase_connection()

    assert connected is True
    assert "public.obras" in message


def test_multi_work_crud_and_active_selection(tmp_path, monkeypatch):
    test_db = tmp_path / "obra_manager_test.db"
    monkeypatch.setattr(app, "DB_PATH", test_db)

    app.init_db()

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

    app.delete_work(work_id_a)
    works_after = app.list_works()
    assert len(works_after) == 1
    assert works_after[0]["nome"] == "Obra B"
