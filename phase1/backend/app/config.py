from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str

    ldap_url: str
    ldap_base_dn: str
    ldap_people_dn: str = "ou=users,dc=seeder,dc=org"
    # Kept for future use (e.g. user search/autocomplete, admin lookups).
    # Not required for current auth flow — user binds with their own
    # credentials and reads their own attributes; no service account needed.
    ldap_bind_dn: str | None = None
    ldap_bind_password: str | None = None
    bootstrap_admin_uid: str
    # StartTLS cert — leave unset to use system trust store
    ldap_ca_cert_path: str | None = None

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = 3600
    jwt_refresh_expiry_seconds: int = 604800

    connector_encryption_key: str

    litellm_url: str
    litellm_master_key: str

    class Config:
        env_file = ".env"


settings = Settings()
