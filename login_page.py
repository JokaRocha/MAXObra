from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
from mfa_auth import MFAError, enroll_totp_factor, list_totp_factors, remove_unverified_factor, verify_totp_factor


def _session_user_id(session) -> str | None:
    user = getattr(session, "user", None)
    return getattr(user, "id", None)


def _finish_mfa_verification(client, result: dict) -> None:
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    if not access_token or not refresh_token:
        raise MFAError("O Supabase não devolveu a sessão AAL2 esperada.")

    client.auth.set_session(access_token, refresh_token)
    session = client.auth.get_session()
    verified_token = getattr(session, "access_token", None)
    if not verified_token:
        raise MFAError("Não foi possível confirmar a sessão MFA.")

    st.session_state["mfa_verified_access_token"] = verified_token
    st.session_state.pop("mfa_pending_factor", None)
    st.session_state.pop("mfa_add_factor", None)
    st.rerun()


def _start_totp_enrollment(client, get_supabase_config, user_id: str) -> None:
    result = enroll_totp_factor(client, get_supabase_config, "Obra Manager")
    totp = result.get("totp") or {}
    if not result.get("id") or not totp.get("qr_code") or not totp.get("secret"):
        raise MFAError("O Supabase não devolveu os dados de configuração do autenticador.")
    st.session_state["mfa_pending_factor"] = {
        "user_id": user_id,
        "factor_id": result["id"],
        "qr_code": totp["qr_code"],
        "secret": totp["secret"],
    }
    st.rerun()


def _render_totp_enrollment(client, get_supabase_config, factors: list[dict], user_id: str) -> bool:
    pending = st.session_state.get("mfa_pending_factor")
    if pending and pending.get("user_id") != user_id:
        st.session_state.pop("mfa_pending_factor", None)
        pending = None

    st.title("Configurar autenticação de dois fatores")
    st.info("A conta precisa de um autenticador TOTP para aceder aos dados.")

    if pending is None:
        unverified = [factor for factor in factors if factor.get("status") == "unverified"]
        if unverified:
            st.warning("Existe uma configuração TOTP incompleta. Reinicie para gerar um novo QR code.")
        else:
            st.write("Use uma app autenticadora, como Microsoft Authenticator, Google Authenticator ou 1Password.")

        if st.button("Reiniciar configuração" if unverified else "Configurar autenticador", icon=":material/qr_code_2:"):
            try:
                for factor in unverified:
                    remove_unverified_factor(client, get_supabase_config, factor["id"])
                _start_totp_enrollment(client, get_supabase_config, user_id)
            except MFAError as exc:
                st.error(str(exc))
        return False

    qr_image = base64.b64encode(pending["qr_code"].encode("utf-8")).decode("ascii")
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{qr_image}" alt="QR code para configurar MFA" width="220">',
        unsafe_allow_html=True,
    )
    st.caption("Se não puder ler o QR code, introduza esta chave manualmente no autenticador:")
    st.code(pending["secret"])

    with st.form("mfa_enrollment_form"):
        code = st.text_input("Código de 6 dígitos", max_chars=6, autocomplete="one-time-code")
        submitted = st.form_submit_button("Ativar autenticação", use_container_width=True)
    if submitted:
        if len(code.strip()) != 6 or not code.strip().isdigit():
            st.error("Introduza o código de 6 dígitos da app autenticadora.")
        else:
            try:
                result = verify_totp_factor(
                    client,
                    get_supabase_config,
                    pending["factor_id"],
                    code.strip(),
                )
                _finish_mfa_verification(client, result)
            except MFAError as exc:
                st.error(str(exc))
    return False


def _render_totp_challenge(client, get_supabase_config, factors: list[dict]) -> bool:
    st.title("Verificação em dois fatores")
    st.caption("Introduza o código atual da app autenticadora.")
    labels = {
        factor["id"]: factor.get("friendly_name") or f"Autenticador {index + 1}"
        for index, factor in enumerate(factors)
    }

    with st.form("mfa_challenge_form"):
        factor_id = st.selectbox(
            "Autenticador",
            list(labels),
            format_func=lambda value: labels[value],
        )
        code = st.text_input("Código de 6 dígitos", max_chars=6, autocomplete="one-time-code")
        submitted = st.form_submit_button("Verificar código", use_container_width=True)

    if submitted:
        if len(code.strip()) != 6 or not code.strip().isdigit():
            st.error("Introduza o código de 6 dígitos da app autenticadora.")
        else:
            try:
                result = verify_totp_factor(client, get_supabase_config, factor_id, code.strip())
                _finish_mfa_verification(client, result)
            except MFAError as exc:
                st.error(str(exc))
    return False


def _render_mfa_gate(client, session, get_supabase_config) -> bool:
    access_token = getattr(session, "access_token", None)
    user_id = _session_user_id(session)
    if not access_token or not user_id:
        st.error("Não foi possível validar a sessão. Entre novamente.")
        return False

    adding_factor = st.session_state.get("mfa_add_factor", False)
    if st.session_state.get("mfa_verified_access_token") == access_token and not adding_factor:
        if st.sidebar.button("Adicionar autenticador", icon=":material/phonelink_lock:"):
            st.session_state["mfa_add_factor"] = True
            st.rerun()
        return True

    try:
        factors = list_totp_factors(client, get_supabase_config)
    except MFAError as exc:
        st.error(str(exc))
        return False

    if adding_factor or not any(factor.get("status") == "verified" for factor in factors):
        return _render_totp_enrollment(client, get_supabase_config, factors, user_id)
    return _render_totp_challenge(
        client,
        get_supabase_config,
        [factor for factor in factors if factor.get("status") == "verified"],
    )


def render_login_page(client, logo_path: Path, authenticate_username_password, get_session_role, get_supabase_config) -> str | None:
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
        if not _render_mfa_gate(client, session, get_supabase_config):
            return None
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
