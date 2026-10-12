from flask import Flask, redirect, render_template, url_for

from .auth import current_user, has_role, init_oauth
from .models.base import db


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Schema is managed by Alembic migrations (flask db upgrade), not db.create_all()
    db.init_app(app)
    init_oauth(app)

    # Register web blueprints (split by entity)
    from .web.auth import auth_bp
    from .web.profile import profile_bp
    from .web.user import users_bp
    app.register_blueprint(auth_bp)  # /auth
    app.register_blueprint(profile_bp)  # /profile
    app.register_blueprint(users_bp)  # /users (admin only)

    @app.context_processor
    def inject_user():
        return {"current_user": current_user(), "is_admin": has_role("admin")}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.get("/")
    def home():
        if current_user():
            return redirect(url_for("profile.details"))
        return render_template("home.html")

    return app
