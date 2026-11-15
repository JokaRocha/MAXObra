from __future__ import annotations

from collections.abc import Callable

import httpx


class MFAError(RuntimeError):
    pass


def _mfa_request(
    client,
    get_supabase_config: Callable[[], tuple[str | None, str | None]],
    method: str,
    path: str,
    payload: dict | None = None,
) -> dict:
    url, publishable_key = get_supabase_config()
    session = client.auth.get_session()
    access_token = getattr(session, "access_token", None)
    if not url or not publishable_key or not access_token:
        raise MFAError("A sessão de autenticação não está disponível.")

    try:
        response = httpx.request(
            method,
            f"{url.rstrip('/')}/auth/v1/{path.lstrip('/')}",
            headers={
                "apikey": publishable_key,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
    except httpx.RequestError as exc:
        raise MFAError("Não foi possível contactar o serviço MFA do Supabase.") from exc

    if not response.is_success:
        raise MFAError("O Supabase rejeitou a operação MFA. Confirme o código e tente novamente.")
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise MFAError("Resposta inválida do serviço MFA do Supabase.") from exc


def list_totp_factors(client, get_supabase_config: Callable[[], tuple[str | None, str | None]]) -> list[dict]:
    response = _mfa_request(client, get_supabase_config, "GET", "factors")
    return response.get("totp") or []


def enroll_totp_factor(
    client,
    get_supabase_config: Callable[[], tuple[str | None, str | None]],
    friendly_name: str,
) -> dict:
    return _mfa_request(
        client,
        get_supabase_config,
        "POST",
        "factors",
        {"factor_type": "totp", "friendly_name": friendly_name},
    )


def verify_totp_factor(
    client,
    get_supabase_config: Callable[[], tuple[str | None, str | None]],
    factor_id: str,
    code: str,
) -> dict:
    challenge = _mfa_request(
        client,
        get_supabase_config,
        "POST",
        f"factors/{factor_id}/challenge",
        {},
    )
    challenge_id = challenge.get("id")
    if not challenge_id:
        raise MFAError("O Supabase não criou o desafio MFA.")

    return _mfa_request(
        client,
        get_supabase_config,
        "POST",
        f"factors/{factor_id}/verify",
        {"challenge_id": challenge_id, "code": code.strip()},
    )


def remove_unverified_factor(
    client,
    get_supabase_config: Callable[[], tuple[str | None, str | None]],
    factor_id: str,
) -> None:
    _mfa_request(client, get_supabase_config, "DELETE", f"factors/{factor_id}")
