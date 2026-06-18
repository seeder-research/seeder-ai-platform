from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str

    ldap_url: str
    ldap_base_dn: str
    ldap_people_dn: str = "ou=users,dc=seeder,dc=org"
    ldap_bind_dn: str
    ldap_bind_password: str
    bootstrap_admin_uid: str
    # StartTLS server cert validation. Leave unset to use the system default
    # trust store (e.g. /etc/ssl/certs/ca-certificates.crt on Debian/Ubuntu),
    # which already includes anything placed in /usr/local/share/ca-certificates
    # and registered via `update-ca-certificates`. Set this only if you need to
    # point at a specific cert file instead of relying on the system store.
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
