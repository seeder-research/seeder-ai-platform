import ssl
import logging
from ldap3 import Server, Connection, Tls, ALL, AUTO_BIND_TLS_BEFORE_BIND
from app.config import settings

logger = logging.getLogger(__name__)

def _build_tls() -> Tls:
    return Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=settings.ldap_ca_cert_path or None)

def authenticate_ldap(username: str, password: str) -> dict | None:
    server = Server(settings.ldap_url, get_info=ALL, tls=_build_tls())
    user_dn = f"uid={username},{settings.ldap_people_dn}"

    try:
        conn = Connection(server, user=user_dn, password=password,
                          auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
    except Exception as e:
        logger.error(f"LDAP bind failed for {username}: {type(e).__name__}: {e}")
        return None

    conn.search(
        search_base=settings.ldap_people_dn,
        search_filter=f"(uid={username})",
        attributes=["mail", "cn", "uidNumber", "gidNumber", "homeDirectory"],
    )
    if not conn.entries:
        logger.error(f"LDAP search returned no entries for {username}")
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
