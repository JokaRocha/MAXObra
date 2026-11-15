from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_login_page(client, logo_path: Path, authenticate_username_password, get_session_role) -> str | None:
    if client is None:
        logo_left, logo_center, logo_right = st.columns([1, 2, 1])
        with logo_center:
            st.image(str(logo_path), width=240)
        st.title("Acesso ao Obra Manager")
        st.error("Não foi possível configurar a autenticação. Verifique a URL e a chave publishable do Supabase.")
        return None

    try:
        session = client.auth.get_session()
    except Exception:
        session = None

    if session is not None:
        role = get_session_role(session)
        return role

    auth_message = st.session_state.pop("auth_message", None)
    _, login_column, _ = st.columns([1.1, 1.4, 1.1])
    with login_column:
        _, logo_column, _ = st.columns([1, 3, 1])
        with logo_column:
            st.image(str(logo_path), width=400)
        st.markdown(
            """
            <style>
            .login-caption {
                margin: 0 0 .75rem;
                color: var(--obra-muted);
                text-align: center;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="login-caption">Entre com as credenciais da sua conta.</p>',
            unsafe_allow_html=True,
        )
        if auth_message:
            st.success(auth_message)
        with st.form("supabase_login_form"):
            username = st.text_input("Utilizador", autocomplete="username")
            password = st.text_input("Palavra-passe", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            if not username.strip() or not password:
                st.error("Preencha o utilizador e a palavra-passe.")
            else:
                authenticated, message = authenticate_username_password(client, username, password)
                if authenticated:
                    st.rerun()
                else:
                    st.error(message)

        st.markdown(
            '<p class="login-caption">As contas e os níveis de acesso são geridos pela administração.</p>',
            unsafe_allow_html=True,
        )
    return None
