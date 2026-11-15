from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import httpx
import streamlit as st
from login_page import render_login_page

load_dotenv()

LOGO_PATH = Path(__file__).resolve().parent / "img" / "logo_maxobra.png"
LANGUAGES = ["pt", "es", "en", "de", "fr"]
SUPABASE_CREDENTIAL_TARGET = "MAXObra-Supabase"
SUPABASE_CREDENTIAL_USERNAME = "SUPABASE_KEY"
ACCESS_ROLES = {"manager", "builder", "info"}


def render_app_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --obra-ink: #101713;
            --obra-muted: #a4b1a7;
            --obra-green: #2f9b75;
            --obra-green-dark: #24795c;
            --obra-gold: #f2bf18;
            --obra-paper: #111815;
            --obra-surface: #1b2420;
            --obra-field: #141c18;
            --obra-text: #edf2ed;
            --obra-line: #35443b;
        }
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(145deg, #101613 0%, #141c17 58%, #101713 100%);
            color: var(--obra-text);
            background-attachment: fixed;
        }
        [data-testid="stMain"] { color: var(--obra-text); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: #0c110e;
            border-right: 1px solid var(--obra-line);
        }
        [data-testid="stSidebar"] * { color: var(--obra-text); }
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            border-radius: 4px;
            padding: .35rem .5rem;
        }
        h1, h2, h3 { color: var(--obra-text); letter-spacing: 0; }
        h1 { font-weight: 750; }
        h1::after {
            content: "";
            display: block;
            width: 3rem;
            height: 3px;
            margin-top: .55rem;
            background: var(--obra-gold);
        }
        [data-testid="stCaptionContainer"] { color: var(--obra-muted); }
        .sidebar-role {
            margin: .55rem 0 1rem;
            padding: .35rem .5rem;
            color: var(--obra-gold);
            font-size: 1.05rem;
            font-weight: 700;
            text-align: center;
        }
        [data-testid="stMetric"] {
            background: var(--obra-surface);
            border: 1px solid var(--obra-line);
            border-top: 3px solid var(--obra-gold);
            border-radius: 4px;
            padding: 1rem 1.1rem;
        }
        [data-testid="stMetricLabel"] { color: var(--obra-muted); }
        [data-testid="stMetricValue"] { color: var(--obra-text); }
        [data-testid="stForm"] {
            background: rgba(27, 36, 32, .94);
            border: 1px solid var(--obra-line);
            border-radius: 5px;
            padding: 1.25rem;
        }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            background: var(--obra-field);
            color: var(--obra-text);
            border-radius: 4px;
            border-color: #46564b;
        }
        [data-testid="stSelectbox"] [role="combobox"] {
            background: var(--obra-field);
            color: var(--obra-text);
            border-color: #46564b;
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--obra-gold);
            box-shadow: 0 0 0 1px var(--obra-gold);
        }
        .stButton > button, [data-testid="stFormSubmitButton"] > button {
            min-height: 2.65rem;
            border-radius: 4px;
            font-weight: 650;
            transition: background-color .15s ease, border-color .15s ease, color .15s ease, transform .15s ease;
        }
        .stButton > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button[kind="primary"] {
            border: 1px solid var(--obra-gold);
            background: var(--obra-gold);
            color: var(--obra-ink);
        }
        [data-testid="stSidebar"] button[kind="primary"] * {
            color: var(--obra-ink);
        }
        .stButton > button[kind="secondary"],
        [data-testid="stFormSubmitButton"] > button[kind="secondary"] {
            border: 1px solid var(--obra-line);
            background: transparent;
            color: var(--obra-text);
        }
        .stButton > button[kind="primary"]:hover,
        [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background: #ffd84d;
            border-color: #ffd84d;
            color: var(--obra-ink);
            transform: translateY(-1px);
        }
        .stButton > button[kind="secondary"]:hover,
        [data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover {
            border-color: var(--obra-green);
            background: rgba(47, 155, 117, .12);
            color: var(--obra-text);
        }
        [data-testid="stSidebar"] .st-key-logout_button button {
            border-color: #75463f;
            color: #e6aaa1;
        }
        [data-testid="stSidebar"] .st-key-logout_button button:hover {
            border-color: #b75f52;
            background: rgba(183, 95, 82, .16);
            color: #ffc0b7;
        }
        [data-testid="stSidebar"] .st-key-logout_button button * {
            color: inherit;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--obra-line);
            border-radius: 4px;
            overflow: hidden;
        }
        [data-testid="stExpander"] details {
            background: var(--obra-surface);
            border-color: var(--obra-line);
        }
        [data-testid="stMain"] a { color: #f2bf18; }
        [data-testid="stAlert"] { border-radius: 4px; }
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] { padding: 1rem .75rem 2rem; }
            [data-testid="stForm"] { padding: .85rem; }
            [data-testid="stMetric"] { padding: .75rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def read_windows_credential() -> str | None:
    try:
        import keyring
    except Exception:
        keyring = None

    targets = [os.getenv("SUPABASE_URL"), SUPABASE_CREDENTIAL_TARGET]
    if keyring is not None:
        for target in targets:
            if not target:
                continue
            try:
                password = keyring.get_password(target, SUPABASE_CREDENTIAL_USERNAME)
            except Exception:
                continue
            if password:
                return password

    if os.name != "nt":
        return None

    try:
        import win32cred

        for target in targets:
            if not target:
                continue
            for credential_type in (
                win32cred.CRED_TYPE_GENERIC,
                win32cred.CRED_TYPE_DOMAIN_PASSWORD,
            ):
                try:
                    credential = win32cred.CredRead(target, credential_type, 0)
                except Exception:
                    continue
                blob = credential.get("CredentialBlob")
                if isinstance(blob, str) and blob:
                    return blob
                if isinstance(blob, bytes) and blob:
                    try:
                        return blob.decode("utf-16-le").rstrip("\x00")
                    except UnicodeDecodeError:
                        continue
    except Exception:
        return None
    return None


def get_supabase_config() -> tuple[str | None, str | None]:
    try:
        streamlit_url = st.secrets.get("SUPABASE_URL")
        streamlit_key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        streamlit_url = None
        streamlit_key = None

    url = os.getenv("SUPABASE_URL") or streamlit_url
    key = os.getenv("SUPABASE_KEY") or streamlit_key or read_windows_credential()
    return url, key


def get_supabase_auth_client():
    client = st.session_state.get("supabase_auth_client")
    if client is not None:
        return client

    url, key = get_supabase_config()
    if not url or not key:
        return None

    try:
        from supabase import create_client

        client = create_client(url, key)
    except Exception:
        return None

    st.session_state["supabase_auth_client"] = client
    return client


def post_username_auth_request(payload: dict) -> tuple[httpx.Response | None, str | None]:
    url, key = get_supabase_config()
    if not url or not key:
        return None, "A configuração do Supabase (URL/chave publishable) não está disponível."

    try:
        response = httpx.post(
            f"{url.rstrip('/')}/functions/v1/username-login",
            headers={"apikey": key, "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
    except httpx.RequestError:
        return None, "Não foi possível contactar o serviço de autenticação. Verifique a ligação à Internet."

    if response.status_code == 404:
        return None, "A função username-login ainda não está publicada no Supabase. É necessário fazer deploy da função."
    return response, None


def authenticate_username_password(client, username: str, password: str) -> tuple[bool, str]:
    response, error = post_username_auth_request(
        {"username": username.strip(), "password": password}
    )
    if error:
        return False, error

    try:
        if response is None or response.status_code == 401:
            return False, "Utilizador ou palavra-passe incorretos."
        if not response.is_success:
            return False, "O serviço de autenticação não conseguiu iniciar sessão."
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        if not access_token or not refresh_token:
            return False, "Resposta inválida do serviço de autenticação."
        client.auth.set_session(access_token, refresh_token)
        return True, ""
    except (ValueError, AttributeError):
        return False, "Não foi possível interpretar a resposta de autenticação."


def get_session_role(session) -> str:
    user = getattr(session, "user", None)
    app_metadata = getattr(user, "app_metadata", None) or {}
    role = app_metadata.get("role")
    return role if role in ACCESS_ROLES else "info"


def get_menu_options(role: str, language: str) -> list[str]:
    options = [
        "Obras",
        translate_text("dashboard", language),
        translate_text("configuration", language),
        translate_text("finance", language),
        translate_text("planning", language),
        translate_text("reports", language),
    ]
    if role == "manager":
        return options
    if role == "builder":
        return [options[0], options[1], options[4]]
    return options[:2]


def render_page_heading(title: str) -> None:
    st.title(title)


def test_supabase_connection() -> tuple[bool, str]:
    try:
        get_data_client().table("obras").select("id").limit(1).execute()
        return True, "Ligação autenticada ao Supabase estabelecida; as políticas RLS estão ativas para esta sessão."
    except Exception:
        return False, "Não foi possível consultar obras com esta sessão. Confirme schema, sessão e políticas RLS no Supabase."
LANGUAGE_LABELS = {
    "pt": "PT",
    "es": "ES",
    "en": "EN",
    "de": "DE",
    "fr": "FR",
}

TRANSLATIONS = {
    "menu": {"pt": "Menu", "es": "Menú", "en": "Menu", "de": "Menü", "fr": "Menu"},
    "dashboard": {"pt": "Dashboard", "es": "Panel", "en": "Dashboard", "de": "Übersicht", "fr": "Tableau de bord"},
    "configuration": {"pt": "Configuração", "es": "Configuración", "en": "Configuration", "de": "Konfiguration", "fr": "Configuration"},
    "finance": {"pt": "Financeiro", "es": "Finanzas", "en": "Finance", "de": "Finanzen", "fr": "Finance"},
    "planning": {"pt": "Planeamento", "es": "Planificación", "en": "Planning", "de": "Planung", "fr": "Planification"},
    "reports": {"pt": "Relatórios", "es": "Informes", "en": "Reports", "de": "Berichte", "fr": "Rapports"},
    "language": {"pt": "Idioma", "es": "Idioma", "en": "Language", "de": "Sprache", "fr": "Langue"},
    "title": {"pt": "Obra Manager", "es": "Gestor de obra", "en": "Construction Manager", "de": "Bauleiter", "fr": "Gestion de chantier"},
    "dashboard_title": {"pt": "Dashboard geral", "es": "Panel general", "en": "Overview", "de": "Gesamtübersicht", "fr": "Tableau général"},
    "project_summary": {"pt": "Resumo da obra", "es": "Resumen de la obra", "en": "Project summary", "de": "Projektübersicht", "fr": "Résumé du chantier"},
    "finance_summary": {"pt": "Finanças", "es": "Finanzas", "en": "Finance", "de": "Finanzen", "fr": "Finances"},
    "project_name": {"pt": "Nome da obra", "es": "Nombre de la obra", "en": "Project name", "de": "Projektname", "fr": "Nom du chantier"},
    "customer": {"pt": "Cliente", "es": "Cliente", "en": "Client", "de": "Kunde", "fr": "Client"},
    "location": {"pt": "Local", "es": "Ubicación", "en": "Location", "de": "Standort", "fr": "Lieu"},
    "manager": {"pt": "Gestor", "es": "Responsable", "en": "Manager", "de": "Verantwortlicher", "fr": "Gestionnaire"},
    "start_date": {"pt": "Data de início", "es": "Fecha de inicio", "en": "Start date", "de": "Startdatum", "fr": "Date de début"},
    "end_date": {"pt": "Data de fim", "es": "Fecha de fin", "en": "End date", "de": "Enddatum", "fr": "Date de fin"},
    "project_value": {"pt": "Valor da obra (€)", "es": "Valor de la obra (€)", "en": "Project value (€)", "de": "Projektwert (€)", "fr": "Valeur du chantier (€)"},
    "iva_type": {"pt": "Tipo de IVA", "es": "Tipo de IVA", "en": "VAT type", "de": "MwSt.-Typ", "fr": "Type de TVA"},
    "iva_percentage": {"pt": "Percentagem de IVA (%)", "es": "Porcentaje de IVA (%)", "en": "VAT percentage (%)", "de": "Mehrwertsteuer (%)", "fr": "Pourcentage de TVA (%)"},
    "status": {"pt": "Estado", "es": "Estado", "en": "Status", "de": "Status", "fr": "Statut"},
    "save_config": {"pt": "Guardar configuração", "es": "Guardar configuración", "en": "Save configuration", "de": "Konfiguration speichern", "fr": "Enregistrer la configuration"},
    "saved_success": {"pt": "Configuração guardada com sucesso.", "es": "Configuración guardada correctamente.", "en": "Configuration saved successfully.", "de": "Konfiguration erfolgreich gespeichert.", "fr": "Configuration enregistrée avec succès."},
    "save_finance": {"pt": "Guardar movimento", "es": "Guardar movimiento", "en": "Save entry", "de": "Eintrag speichern", "fr": "Enregistrer le mouvement"},
    "financial_saved": {"pt": "Movimento financeiro guardado.", "es": "Movimiento financiero guardado.", "en": "Financial entry saved.", "de": "Finanzbewegung gespeichert.", "fr": "Mouvement financier enregistré."},
    "finance_type": {"pt": "Tipo", "es": "Tipo", "en": "Type", "de": "Typ", "fr": "Type"},
    "description": {"pt": "Descrição", "es": "Descripción", "en": "Description", "de": "Beschreibung", "fr": "Description"},
    "category": {"pt": "Categoria", "es": "Categoría", "en": "Category", "de": "Kategorie", "fr": "Catégorie"},
    "value": {"pt": "Valor (€)", "es": "Valor (€)", "en": "Value (€)", "de": "Wert (€)", "fr": "Valeur (€)"},
    "date": {"pt": "Data", "es": "Fecha", "en": "Date", "de": "Datum", "fr": "Date"},
    "comments": {"pt": "Observações", "es": "Observaciones", "en": "Notes", "de": "Bemerkungen", "fr": "Observations"},
    "task_title": {"pt": "Título da tarefa", "es": "Título de la tarea", "en": "Task title", "de": "Aufgabentitel", "fr": "Titre de la tâche"},
    "task_description": {"pt": "Descrição da tarefa", "es": "Descripción de la tarea", "en": "Task description", "de": "Aufgabenbeschreibung", "fr": "Description de la tâche"},
    "responsible": {"pt": "Responsável", "es": "Responsable", "en": "Responsible", "de": "Verantwortlich", "fr": "Responsable"},
    "priority": {"pt": "Prioridade", "es": "Prioridad", "en": "Priority", "de": "Priorität", "fr": "Priorité"},
    "add_task": {"pt": "Adicionar tarefa", "es": "Añadir tarea", "en": "Add task", "de": "Aufgabe hinzufügen", "fr": "Ajouter une tâche"},
    "task_saved": {"pt": "Tarefa adicionada com sucesso.", "es": "Tarea añadida correctamente.", "en": "Task added successfully.", "de": "Aufgabe erfolgreich hinzugefügt.", "fr": "Tâche ajoutée avec succès."},
    "task_plan": {"pt": "Tarefas do plano", "es": "Tareas del plan", "en": "Planned tasks", "de": "Geplante Aufgaben", "fr": "Tâches prévues"},
    "financial_registries": {"pt": "Registos financeiros", "es": "Registros financieros", "en": "Financial entries", "de": "Finanzbuchungen", "fr": "Écritures financières"},
    "no_financial": {"pt": "Ainda não existem registos financeiros.", "es": "Todavía no hay registros financieros.", "en": "No financial entries yet.", "de": "Noch keine Finanzbuchungen.", "fr": "Aucune écriture financière pour le moment."},
    "no_tasks": {"pt": "Ainda não existem tarefas planeadas.", "es": "Todavía no hay tareas previstas.", "en": "No planned tasks yet.", "de": "Noch keine geplanten Aufgaben.", "fr": "Aucune tâche planifiée pour le moment."},
    "warning_fill": {"pt": "Preencha descrição e categoria antes de guardar.", "es": "Rellene descripción y categoría antes de guardar.", "en": "Fill in description and category before saving.", "de": "Beschreibung und Kategorie vor dem Speichern ausfüllen.", "fr": "Remplissez la description et la catégorie avant d'enregistrer."},
    "warning_task": {"pt": "Preencha título e responsável para criar a tarefa.", "es": "Rellene título y responsable para crear la tarea.", "en": "Fill in title and responsible person to create the task.", "de": "Titel und Verantwortlichen ausfüllen, um die Aufgabe zu erstellen.", "fr": "Remplissez le titre et le responsable pour créer la tâche."},
    "project_status": {
        "pt": ["Planeamento", "Em execução", "Concluída", "Pausada"],
        "es": ["Planificación", "En ejecución", "Completada", "Pausada"],
        "en": ["Planning", "In progress", "Completed", "Paused"],
        "de": ["Planung", "In Bearbeitung", "Abgeschlossen", "Pausiert"],
        "fr": ["Planification", "En cours", "Terminé", "En pause"],
    },
    "iva_options": {
        "pt": ["Com IVA", "Sem IVA"],
        "es": ["Con IVA", "Sin IVA"],
        "en": ["With VAT", "Without VAT"],
        "de": ["Mit MwSt.", "Ohne MwSt."],
        "fr": ["Avec TVA", "Sans TVA"],
    },
    "priority_options": {
        "pt": ["Baixa", "Média", "Alta"],
        "es": ["Baja", "Media", "Alta"],
        "en": ["Low", "Medium", "High"],
        "de": ["Niedrig", "Mittel", "Hoch"],
        "fr": ["Faible", "Moyenne", "Élevée"],
    },
    "status_options": {
        "pt": ["Pendente", "Em execução", "Concluída"],
        "es": ["Pendiente", "En ejecución", "Completada"],
        "en": ["Pending", "In progress", "Completed"],
        "de": ["Ausstehend", "In Bearbeitung", "Abgeschlossen"],
        "fr": ["En attente", "En cours", "Terminé"],
    },
    "income": {"pt": "Receita", "es": "Ingresos", "en": "Income", "de": "Einnahmen", "fr": "Revenu"},
    "expense": {"pt": "Despesa", "es": "Gasto", "en": "Expense", "de": "Ausgabe", "fr": "Dépense"},
    "receipt": {"pt": "Receitas", "es": "Ingresos", "en": "Income", "de": "Einnahmen", "fr": "Revenus"},
    "spend": {"pt": "Despesas", "es": "Gastos", "en": "Expenses", "de": "Ausgaben", "fr": "Dépenses"},
    "balance": {"pt": "Saldo", "es": "Saldo", "en": "Balance", "de": "Saldo", "fr": "Solde"},
    "currency": {"pt": "€", "es": "€", "en": "€", "de": "€", "fr": "€"},
}


def translate_text(key: str, lang: str | None = None) -> str:
    target_lang = lang or st.session_state.get("language", "pt")
    return TRANSLATIONS.get(key, {}).get(target_lang, TRANSLATIONS.get(key, {}).get("pt", key))


def get_language_options() -> list[str]:
    return LANGUAGES


def format_language_option(lang: str) -> str:
    return LANGUAGE_LABELS.get(lang, lang.upper())


def get_data_client():
    client = get_supabase_auth_client()
    if client is None:
        raise RuntimeError("A sessão Supabase não está disponível.")
    return client


def create_or_update_work(
    nome: str,
    cliente: str,
    local: str,
    gestor: str,
    data_inicio: str,
    data_fim: str,
    valor_obra: float,
    tipo_iva: str,
    iva: float,
    status: str,
    work_id: int | None = None,
) -> int:
    client = get_data_client()
    payload = {
        "nome": nome,
        "cliente": cliente,
        "local": local,
        "gestor": gestor,
        "data_inicio": data_inicio or None,
        "data_fim": data_fim or None,
        "valor_obra": float(valor_obra),
        "tipo_iva": tipo_iva,
        "iva": float(iva),
        "status": status,
    }
    if work_id is not None:
        rows = client.table("obras").update(payload).eq("id", work_id).select("id").execute().data or []
        if not rows:
            raise PermissionError("A obra não existe ou a sessão não tem permissão para a alterar.")
        active_id = int(work_id)
    else:
        rows = client.table("obras").insert(payload).execute().data or []
        if not rows:
            raise RuntimeError("O Supabase não confirmou a criação da obra.")
        active_id = int(rows[0]["id"])

    st.session_state["active_work_id"] = active_id
    return active_id


def list_works() -> list[dict]:
    result = get_data_client().table("obras").select(
        "id,nome,cliente,local,gestor,data_inicio,data_fim,valor_obra,tipo_iva,iva,status"
    ).order("id").execute()
    return result.data or []


def set_active_work(work_id: int) -> None:
    if not any(int(work["id"]) == int(work_id) for work in list_works()):
        raise ValueError("A obra selecionada não está disponível nesta conta.")
    st.session_state["active_work_id"] = int(work_id)


def get_active_work() -> dict | None:
    works = list_works()
    if not works:
        st.session_state.pop("active_work_id", None)
        return None

    active_id = st.session_state.get("active_work_id")
    active_work = next((work for work in works if int(work["id"]) == active_id), None)
    if active_work is None:
        active_work = works[0]
        st.session_state["active_work_id"] = int(active_work["id"])
    return active_work


def delete_work(work_id: int) -> None:
    rows = get_data_client().table("obras").delete().eq("id", work_id).select("id").execute().data or []
    if not rows:
        raise PermissionError("A obra não existe ou a sessão não tem permissão para a eliminar.")
    if st.session_state.get("active_work_id") == int(work_id):
        st.session_state.pop("active_work_id", None)


def load_config() -> dict:
    row = get_active_work()
    if row is None:
        return {
            "nome": "Nova obra",
            "cliente": "Cliente",
            "local": "Local da obra",
            "gestor": "Gestor",
            "data_inicio": "",
            "data_fim": "",
            "valor_obra": 0,
            "tipo_iva": "Sem IVA",
            "iva": 0,
            "status": "Planeamento",
        }
    return row


def save_config(values: dict) -> None:
    active = get_active_work()
    if active is None:
        work_id = create_or_update_work(
            nome=values.get("nome", "Nova obra"),
            cliente=values.get("cliente", "Cliente"),
            local=values.get("local", "Local da obra"),
            gestor=values.get("gestor", "Gestor"),
            data_inicio=values.get("data_inicio", ""),
            data_fim=values.get("data_fim", ""),
            valor_obra=values.get("valor_obra", 0),
            tipo_iva=values.get("tipo_iva", "Sem IVA"),
            iva=values.get("iva", 0),
            status=values.get("status", "Planeamento"),
        )
        return

    create_or_update_work(
        nome=values["nome"],
        cliente=values["cliente"],
        local=values["local"],
        gestor=values["gestor"],
        data_inicio=values["data_inicio"],
        data_fim=values["data_fim"],
        valor_obra=values["valor_obra"],
        tipo_iva=values["tipo_iva"],
        iva=values["iva"],
        status=values["status"],
        work_id=active["id"],
    )


def add_financial_entry(
    tipo: str,
    descricao: str,
    categoria: str,
    valor: float,
    data: str,
    observacoes: str = "",
) -> int:
    active_work = get_active_work()
    if active_work is None:
        raise ValueError("Crie ou selecione uma obra antes de registar movimentos financeiros.")
    rows = get_data_client().table("movimentos_financeiros").insert(
        {
            "obra_id": active_work["id"],
            "tipo": tipo,
            "descricao": descricao,
            "categoria": categoria,
            "valor": float(valor),
            "data": data,
            "observacoes": observacoes,
        }
    ).execute().data or []
    if not rows:
        raise RuntimeError("O Supabase não confirmou o movimento financeiro.")
    return int(rows[0]["id"])


def list_financial_entries() -> list[dict]:
    active_work = get_active_work()
    if active_work is None:
        return []
    result = get_data_client().table("movimentos_financeiros").select(
        "id,tipo,descricao,categoria,valor,data,observacoes"
    ).eq("obra_id", active_work["id"]).order("data", desc=True).order("id", desc=True).execute()
    return result.data or []


def get_financial_summary() -> dict:
    entries = list_financial_entries()
    revenue = sum(float(entry["valor"]) for entry in entries if entry["tipo"] == "Receita")
    expense = sum(float(entry["valor"]) for entry in entries if entry["tipo"] == "Despesa")

    return {
        "receitas": float(revenue),
        "despesas": float(expense),
        "saldo": float(revenue - expense),
        "registos": len(entries),
    }


def add_task(
    titulo: str,
    descricao: str,
    responsavel: str,
    prioridade: str,
    data_inicio: str,
    data_fim: str,
    status: str = "Pendente",
) -> int:
    active_work = get_active_work()
    if active_work is None:
        raise ValueError("Crie ou selecione uma obra antes de adicionar tarefas.")
    rows = get_data_client().table("tarefas").insert(
        {
            "obra_id": active_work["id"],
            "titulo": titulo,
            "descricao": descricao,
            "responsavel": responsavel,
            "prioridade": prioridade,
            "data_inicio": data_inicio or None,
            "data_fim": data_fim or None,
            "status": status,
        }
    ).execute().data or []
    if not rows:
        raise RuntimeError("O Supabase não confirmou a criação da tarefa.")
    return int(rows[0]["id"])


def get_tasks() -> list[dict]:
    active_work = get_active_work()
    if active_work is None:
        return []
    result = get_data_client().table("tarefas").select(
        "id,titulo,descricao,responsavel,prioridade,data_inicio,data_fim,status"
    ).eq("obra_id", active_work["id"]).order("data_fim").order("id").execute()
    return result.data or []


def render_dashboard(config: dict, financial: dict, role: str = "manager") -> None:
    language = st.session_state.get("language", "pt")
    render_page_heading(translate_text("dashboard_title", language))
    if role != "manager":
        name_col, status_col = st.columns(2)
        name_col.metric(translate_text("project_name", language), config["nome"])
        status_col.metric(translate_text("status", language), config["status"])
        return

    project_tab, finance_tab = st.tabs([
        translate_text("project_summary", language),
        translate_text("finance_summary", language),
    ])
    with project_tab:
        value_col, status_col = st.columns(2)
        value_col.metric(translate_text("project_value", language), f"€ {float(config['valor_obra']):,.2f}")
        status_col.metric(translate_text("status", language), config["status"])
        left, right = st.columns(2)
        with left:
            st.markdown(f"#### {translate_text('project_summary', language)}")
            st.write(f"{translate_text('project_name', language)}: {config['nome']}")
            st.write(f"{translate_text('customer', language)}: {config['cliente']}")
            st.write(f"{translate_text('location', language)}: {config['local']}")
        with right:
            st.markdown(f"#### {translate_text('manager', language)}")
            st.write(config["gestor"])
            st.write(f"{translate_text('start_date', language)}: {config['data_inicio'] or '-'}")
            st.write(f"{translate_text('end_date', language)}: {config['data_fim'] or '-'}")

    with finance_tab:
        income_col, expense_col, balance_col = st.columns(3)
        income_col.metric(translate_text("receipt", language), f"€ {financial['receitas']:,.2f}")
        expense_col.metric(translate_text("spend", language), f"€ {financial['despesas']:,.2f}")
        balance_col.metric(translate_text("balance", language), f"€ {financial['saldo']:,.2f}")
        st.caption(
            f"{translate_text('financial_registries', language)}: {financial['registos']} · "
            f"{translate_text('iva_type', language)}: {config['tipo_iva']} · "
            f"{translate_text('iva_percentage', language)}: {float(config['iva']):.0f}%"
        )


def render_configuracao(config: dict) -> None:
    language = st.session_state.get("language", "pt")
    render_page_heading(translate_text("configuration", language))

    with st.expander("Base de dados remota", expanded=False):
        st.caption("Verifique a disponibilidade da ligação ao Supabase.")
        if st.button("Testar ligação ao Supabase"):
            st.session_state["supabase_connection_result"] = test_supabase_connection()
        if "supabase_connection_result" in st.session_state:
            connected, message = st.session_state["supabase_connection_result"]
            if connected:
                st.success(message)
            else:
                st.error(message)

    with st.form("obra_form"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input(translate_text("project_name", language), value=config["nome"])
            cliente = st.text_input(translate_text("customer", language), value=config["cliente"])
            local = st.text_input(translate_text("location", language), value=config["local"])
            gestor = st.text_input(translate_text("manager", language), value=config["gestor"])
        with c2:
            data_inicio = st.date_input(translate_text("start_date", language))
            data_fim = st.date_input(translate_text("end_date", language))
            valor_obra = st.number_input(translate_text("project_value", language), min_value=0.0, value=float(config["valor_obra"]))
            tipo_iva_options = TRANSLATIONS["iva_options"][language]
            tipo_iva = st.selectbox(translate_text("iva_type", language), tipo_iva_options, index=0 if config["tipo_iva"] == "Com IVA" else 1)
            iva = st.number_input(translate_text("iva_percentage", language), min_value=0.0, max_value=25.0, value=float(config["iva"]))
            status_options = TRANSLATIONS["project_status"][language]
            status = st.selectbox(translate_text("status", language), status_options, index=status_options.index(config["status"]) if config["status"] in status_options else 0)

        submitted = st.form_submit_button(translate_text("save_config", language))
        if submitted:
            payload = {
                "nome": nome,
                "cliente": cliente,
                "local": local,
                "gestor": gestor,
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
                "valor_obra": valor_obra,
                "tipo_iva": tipo_iva,
                "iva": iva,
                "status": status,
            }
            save_config(payload)
            st.success(translate_text("saved_success", language))
            st.rerun()


def render_financeiro() -> None:
    language = st.session_state.get("language", "pt")
    render_page_heading(translate_text("finance", language))
    financial = get_financial_summary()

    col1, col2, col3 = st.columns(3)
    col1.metric(translate_text("receipt", language), f"€ {financial['receitas']:.2f}")
    col2.metric(translate_text("spend", language), f"€ {financial['despesas']:.2f}")
    col3.metric(translate_text("balance", language), f"€ {financial['saldo']:.2f}")

    active_work = get_active_work()
    if active_work is None:
        st.info("Crie uma obra antes de registar movimentos financeiros.")
        return

    tipo_map = {"Receita": translate_text("income", language), "Despesa": translate_text("expense", language)}

    with st.expander("Registar movimento", expanded=True):
        with st.form("financial_form"):
            c1, c2 = st.columns(2)
            with c1:
                tipo = st.selectbox(
                    translate_text("finance_type", language),
                    list(tipo_map.keys()),
                    format_func=lambda value: tipo_map[value],
                )
                descricao = st.text_input(translate_text("description", language))
                categoria = st.text_input(translate_text("category", language))
            with c2:
                valor = st.number_input(translate_text("value", language), min_value=0.0, step=10.0)
                data = st.date_input(translate_text("date", language))
                observacoes = st.text_area(translate_text("comments", language), height=100)

            submitted = st.form_submit_button(translate_text("save_finance", language))
        if submitted:
            if descricao and categoria:
                add_financial_entry(
                    tipo=tipo,
                    descricao=descricao,
                    categoria=categoria,
                    valor=valor,
                    data=data.isoformat(),
                    observacoes=observacoes,
                )
                st.success(translate_text("financial_saved", language))
                st.rerun()
            else:
                st.warning(translate_text("warning_fill", language))

    entries = list_financial_entries()
    if entries:
        st.markdown(f"### {translate_text('financial_registries', language)}")
        st.dataframe(entries, use_container_width=True, hide_index=True)
    else:
        st.info(translate_text("no_financial", language))


def render_planeamento() -> None:
    language = st.session_state.get("language", "pt")
    render_page_heading(translate_text("planning", language))

    if get_active_work() is None:
        st.info("Crie uma obra antes de adicionar tarefas.")
        return

    with st.expander("Adicionar tarefa", expanded=True):
        with st.form("task_form"):
            titulo = st.text_input(translate_text("task_title", language))
            descricao = st.text_area(translate_text("task_description", language), height=100)
            responsavel = st.text_input(translate_text("responsible", language))
            prioridade = st.selectbox(translate_text("priority", language), TRANSLATIONS["priority_options"][language])
            data_inicio = st.date_input(translate_text("start_date", language))
            data_fim = st.date_input(translate_text("end_date", language))
            status = st.selectbox(translate_text("status", language), TRANSLATIONS["status_options"][language])

            submitted = st.form_submit_button(translate_text("add_task", language))
        if submitted:
            if titulo and responsavel:
                add_task(
                    titulo=titulo,
                    descricao=descricao,
                    responsavel=responsavel,
                    prioridade=prioridade,
                    data_inicio=data_inicio.isoformat(),
                    data_fim=data_fim.isoformat(),
                    status=status,
                )
                st.success(translate_text("task_saved", language))
                st.rerun()
            else:
                st.warning(translate_text("warning_task", language))

    tasks = get_tasks()
    if tasks:
        st.markdown(f"### {translate_text('task_plan', language)}")
        st.dataframe(tasks, use_container_width=True, hide_index=True)
    else:
        st.info(translate_text("no_tasks", language))


def render_relatorios() -> None:
    language = st.session_state.get("language", "pt")
    render_page_heading(translate_text("reports", language))
    st.info("Relatórios resumidos e indicadores da obra vão entrar nesta fase.")


def render_obras(role: str = "manager") -> None:
    render_page_heading("Obras")
    works = list_works()
    active_work = get_active_work()

    if role in {"manager", "builder"}:
        with st.expander("Criar obra", expanded=not works):
            with st.form("new_work_form"):
                nome = st.text_input("Nome da obra")
                cliente = st.text_input("Cliente")
                local = st.text_input("Local")
                gestor = st.text_input("Gestor")
                data_inicio = st.date_input("Data de início")
                data_fim = st.date_input("Data de fim")
                valor_obra = st.number_input("Valor da obra (€)", min_value=0.0, step=100.0)
                tipo_iva = st.selectbox("Tipo de IVA", ["Com IVA", "Sem IVA"])
                iva = st.number_input("Percentagem de IVA (%)", min_value=0.0, max_value=25.0)
                status = st.selectbox("Estado", ["Planeamento", "Em execução", "Concluída", "Pausada"])

                submitted = st.form_submit_button("Guardar obra")
            if submitted:
                if nome:
                    create_or_update_work(
                        nome=nome,
                        cliente=cliente,
                        local=local,
                        gestor=gestor,
                        data_inicio=data_inicio.isoformat(),
                        data_fim=data_fim.isoformat(),
                        valor_obra=valor_obra,
                        tipo_iva=tipo_iva,
                        iva=iva,
                        status=status,
                    )
                    st.success("Obra guardada.")
                    st.rerun()
                st.warning("Introduza o nome da obra.")

    if works:
        st.markdown("### Lista de obras")
        for work in works:
            with st.container(border=True):
                details_col, status_col, value_col = st.columns([3, 1.2, 1.2])
                with details_col:
                    st.markdown(f"#### {work['nome']}")
                    st.caption(f"{work['cliente']} · {work['local']}")
                with status_col:
                    st.caption("Estado")
                    st.write(work["status"])
                with value_col:
                    st.caption("Valor da obra")
                    st.write(f"€ {float(work['valor_obra']):,.2f}")

                action_col, active_col, delete_col = st.columns([1.2, 2, 1.2])
                delete_pending = st.session_state.get("confirm_delete_work_id") == work["id"]
                if delete_pending:
                    with action_col:
                        if st.button("Cancelar", key=f"cancel_delete_{work['id']}", icon=":material/close:"):
                            st.session_state.pop("confirm_delete_work_id", None)
                            st.rerun()
                elif active_work and active_work["id"] == work["id"]:
                    with action_col:
                        st.button("Obra ativa", key=f"active_{work['id']}", icon=":material/check_circle:", disabled=True)
                else:
                    with action_col:
                        if st.button("Ativar obra", key=f"select_{work['id']}", icon=":material/arrow_forward:"):
                            set_active_work(work["id"])
                            st.rerun()
                if active_work and active_work["id"] == work["id"] and not delete_pending:
                    with active_col:
                        st.caption("Selecionada para o projeto atual")
                if role == "manager":
                    with delete_col:
                        if delete_pending:
                            if st.button("Confirmar", key=f"confirm_delete_{work['id']}", icon=":material/delete:"):
                                delete_work(work["id"])
                                st.session_state.pop("confirm_delete_work_id", None)
                                st.rerun()
                        elif st.button("Eliminar", key=f"delete_{work['id']}", icon=":material/delete:"):
                            st.session_state["confirm_delete_work_id"] = work["id"]
                            st.rerun()


def main() -> None:
    if "language" not in st.session_state:
        st.session_state["language"] = "pt"

    st.set_page_config(page_title="Obra Manager", page_icon="🏗️", layout="wide")
    render_app_styles()
    auth_client = get_supabase_auth_client()
    role = render_login_page(
        auth_client,
        LOGO_PATH,
        authenticate_username_password,
        get_session_role,
    )
    if role is None:
        return

    try:
        config = load_config()
        financial = get_financial_summary() if role == "manager" else {}
    except Exception:
        st.error("Não foi possível carregar os dados do Supabase. Verifique as migrações e políticas RLS.")
        st.stop()

    _, sidebar_logo, _ = st.sidebar.columns([1, 4, 1])
    with sidebar_logo:
        st.image(str(LOGO_PATH), width=170)
    language = st.session_state["language"]
    language_selector = st.sidebar.selectbox(
        translate_text("language", language),
        LANGUAGES,
        index=LANGUAGES.index(language),
        format_func=format_language_option,
    )
    if language_selector != language:
        st.session_state["language"] = language_selector
        st.rerun()

    st.sidebar.markdown(
        f'<div class="sidebar-role">{role.capitalize()}</div>',
        unsafe_allow_html=True,
    )

    menu_options = get_menu_options(role, language)
    st.sidebar.markdown(f"### {translate_text('menu', language)}")
    default_menu = translate_text("dashboard", language)
    if default_menu not in menu_options:
        default_menu = menu_options[0]
    if st.session_state.get("active_menu") not in menu_options:
        st.session_state["active_menu"] = default_menu

    nav_icons = [
        ":material/construction:",
        ":material/space_dashboard:",
        ":material/settings:",
        ":material/payments:",
        ":material/event_note:",
        ":material/query_stats:",
    ]
    for index, option in enumerate(menu_options):
        if st.sidebar.button(
            option,
            key=f"page_nav_{index}",
            icon=nav_icons[index],
            type="primary" if st.session_state["active_menu"] == option else "secondary",
            use_container_width=True,
        ):
            st.session_state["active_menu"] = option
            st.rerun()

    st.sidebar.divider()
    if st.sidebar.button(
        "Terminar sessão",
        key="logout_button",
        icon=":material/logout:",
        type="secondary",
        use_container_width=True,
    ):
        try:
            if auth_client is not None:
                auth_client.auth.sign_out()
        finally:
            st.session_state.pop("supabase_auth_client", None)
            st.session_state.pop("active_menu", None)
            st.session_state.pop("active_work_id", None)
            st.rerun()

    menu = st.session_state["active_menu"]

    try:
        if menu == "Obras":
            render_obras(role)
        elif menu == translate_text("dashboard", language):
            render_dashboard(config, financial, role)
        elif menu == translate_text("configuration", language):
            render_configuracao(config)
        elif menu == translate_text("finance", language):
            render_financeiro()
        elif menu == translate_text("planning", language):
            render_planeamento()
        elif menu == translate_text("reports", language):
            render_relatorios()
    except Exception:
        st.error("Não foi possível concluir a operação no Supabase. Verifique a obra ativa e as permissões da sua conta.")


if __name__ == "__main__":
    main()
