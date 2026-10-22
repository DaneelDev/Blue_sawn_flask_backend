# server.py
from flask import Flask
from flask_cors import CORS
from config import PORT
from routes.products import products_bp
from routes.orders import orders_bp
from routes.verification import verification_bp
from routes.users import users_bp

app = Flask(__name__)
CORS(app)

# Регистрируем роуты
app.register_blueprint(products_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(users_bp)

if __name__ == "__main__":
    print(f"Server running on port {PORT}")
    # В продакшене лучше не использовать debug=True
    app.run(host="0.0.0.0", port=PORT, debug=False)
