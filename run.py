from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)  # enables Alembic via Flask-Migrate

if __name__ == "__main__":
    app.run(debug=True)
