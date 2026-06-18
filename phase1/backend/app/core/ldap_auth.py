import ssl
from ldap3 import Server, Connection, Tls, ALL, AUTO_BIND_TLS_BEFORE_BIND
from app.config import settings


def _build_tls() -> Tls:
    # ca_certs_file=None falls back to the system default trust store, which
    # already includes the cert at /usr/local/share/ca-certificates once
    # `update-ca-certificates` has been run. Set LDAP_CA_CERT_PATH in .env to
    # point at a specific file instead, if your environment needs that.
    return Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=settings.ldap_ca_cert_path or None)


def authenticate_ldap(username: str, password: str) -> dict | None:
    """
    Identity-only LDAP auth over StartTLS (no group-based role resolution —
    role lives in the platform DB only, per Option B). Confirms the bind
    succeeds and pulls back posixAccount attributes needed for ephemeral-
    container UID/GID mapping later, plus basic profile fields.
    """
    server = Server(settings.ldap_url, get_info=ALL, tls=_build_tls())
    user_dn = f"uid={username},{settings.ldap_people_dn}"

    try:
        # Opens the connection on the plain LDAP port, negotiates StartTLS,
        # then binds — all in one call. Raises on bad credentials, failed TLS
        # negotiation, or certificate validation failure.
        conn = Connection(server, user=user_dn, password=password, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
    except Exception:
        return None

    conn.search(
        search_base=settings.ldap_people_dn,
        search_filter=f"(uid={username})",
        attributes=["mail", "cn", "uidNumber", "gidNumber", "homeDirectory"],
    )
    if not conn.entries:
        conn.unbind()
        return None

    entry = conn.entries[0]
    info = {
        "uid": username,
        "email": str(entry.mail) if "mail" in entry else f"{username}@seeder.org",
        "display_name": str(entry.cn) if "cn" in entry else username,
        "uid_number": int(entry.uidNumber.value),
        "gid_number": int(entry.gidNumber.value),
        "home_directory": str(entry.homeDirectory.value),
    }
    conn.unbind()
    return info
