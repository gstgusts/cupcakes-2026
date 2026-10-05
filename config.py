import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://cupcakes:cupcakes@localhost:5432/cupcakes",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Keycloak URL as the browser sees it (login page, logout, token issuer)
    KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8080")
    # Keycloak URL for server-to-server calls (token exchange, signing keys).
    # Inside Docker Compose this is the service name, outside it is the same as the public URL.
    KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", KEYCLOAK_PUBLIC_URL)
    KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "cupcakes")
    KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "cupcakes-web")
    KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "cupcakes-web-secret")
