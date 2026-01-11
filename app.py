from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from scheduler import start_scheduler
from routes.auth_routes import auth_bp
from routes.food_routes import food_bp



def create_app():
    app = Flask(__name__)

    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:5173"}},
        supports_credentials=True
    )
    app.config.from_object(Config)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(food_bp, url_prefix="/api/food")

    CORS(app)
    JWTManager(app)

    # start background jobs
    start_scheduler(app)

    @app.route("/")
    def home():
        return {"message": "Zero Hunger API is running"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
