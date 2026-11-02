from flask import Flask, redirect, render_template, url_for

from .models.base import db
from .services.auth import current_user, has_role, init_oauth


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Schema is managed by Alembic migrations (flask db upgrade), not db.create_all()
    db.init_app(app)
    init_oauth(app)

    # Register web blueprints (split by entity)
    from .web.auth import auth_bp
    from .web.cupcake import cupcakes_bp
    from .web.cupcake_image import cupcake_images_bp
    from .web.plan import plans_bp
    from .web.prediction import predictions_bp
    from .web.prediction_model import prediction_models_bp
    from .web.profile import profile_bp
    from .web.sales import sales_bp
    from .web.user import users_bp
    app.register_blueprint(auth_bp)  # /auth
    app.register_blueprint(cupcakes_bp)  # /cupcakes
    app.register_blueprint(cupcake_images_bp)  # /cupcakes/.../images
    app.register_blueprint(prediction_models_bp)  # /prediction-models
    app.register_blueprint(predictions_bp)  # /predictions
    app.register_blueprint(plans_bp)  # /plans
    app.register_blueprint(sales_bp)  # /sales
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
