from __future__ import annotations

from typing import Any

from supabase import Client, create_client

_default_client: Client | None = None


def get_client(url: str, service_key: str) -> Client:
    global _default_client
    _default_client = create_client(url, service_key)
    return _default_client


def has_certificate_sent_column(client: Client) -> bool:
    try:
        client.table("workshop_registrations").select("certificate_sent_at").limit(1).execute()
        return True
    except Exception:
        return False


def get_workshop_ids(client: Client) -> list[str]:
    response = client.table("workshop_registrations").select("workshop_id").execute()
    rows = response.data or []
    workshop_ids = sorted({row.get("workshop_id") for row in rows if row.get("workshop_id")})
    return workshop_ids


def get_workshop_titles(client: Client) -> dict[str, str]:
    try:
        response = client.table("workshops").select("slug,title").execute()
        rows = response.data or []
        mapping: dict[str, str] = {}
        for row in rows:
            slug = row.get("slug")
            title = row.get("title")
            if slug and title:
                mapping[str(slug)] = str(title)
        return mapping
    except Exception:
        return {}


def get_registrations(client: Client, workshop_id: str) -> list[dict[str, Any]]:
    try:
        response = (
            client.table("workshop_registrations")
            .select("id,full_name,email,created_at,workshop_id,certificate_sent_at")
            .eq("workshop_id", workshop_id)
            .order("created_at")
            .execute()
        )
        return response.data or []
    except Exception:
        response = (
            client.table("workshop_registrations")
            .select("id,full_name,email,created_at,workshop_id")
            .eq("workshop_id", workshop_id)
            .order("created_at")
            .execute()
        )
        return response.data or []


def get_registration_by_short_id(short_id: str) -> dict[str, Any] | None:
    if not short_id:
        return None
    if _default_client is None:
        raise ValueError("Supabase client is not initialized. Call get_client() first.")

    response = (
        _default_client.table("workshop_registrations")
        .select("id,full_name,email,created_at,workshop_id,certificate_sent_at")
        .filter("id", "like", f"{short_id}%")
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None
