from flask import Blueprint, request, jsonify
from db_utils import get_cursor
from crypto_utils import encrypt_text, decrypt_text
from config import ENCRYPTION_KEY

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("", methods=["GET"])
def get_user():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Email обязателен"}), 400

    if not ENCRYPTION_KEY:
        return jsonify({"message": "Ошибка конфигурации сервера"}), 500

    with get_cursor() as cur:
        cur.execute(
            "SELECT name, phone_number, address, email FROM users WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()

    if not row:
        return jsonify({"message": "Пользователь не найден"}), 404

    columns = ["name", "phone_number", "address", "email"]
    raw = dict(zip(columns, row))

    decrypted_name = decrypt_text(raw["name"], ENCRYPTION_KEY)
    decrypted_phone_number = decrypt_text(raw["phone_number"], ENCRYPTION_KEY)
    decrypted_address = decrypt_text(raw["address"], ENCRYPTION_KEY)

    user_data = {
        "name": decrypted_name,
        "phone_number": decrypted_phone_number,
        "address": decrypted_address,
        "email": raw["email"],
    }

    return jsonify(user_data), 200


@users_bp.route("", methods=["POST"])
def save_or_update_user():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    phone_number = data.get("phoneNumber")
    address = data.get("address")

    if not email:
        return jsonify({"message": "Email обязателен"}), 400

    if not ENCRYPTION_KEY:
        return jsonify({"message": "Ошибка конфигурации сервера"}), 500

    encrypted_name = encrypt_text(name, ENCRYPTION_KEY)
    encrypted_phone_number = encrypt_text(phone_number, ENCRYPTION_KEY)
    encrypted_address = encrypt_text(address, ENCRYPTION_KEY)

    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE users
                SET name = %s, phone_number = %s, address = %s
                WHERE email = %s
                RETURNING *;
            """, [encrypted_name, encrypted_phone_number, encrypted_address, email])
            row = cur.fetchone()
        else:
            cur.execute("""
                INSERT INTO users (name, email, phone_number, address)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            """, [encrypted_name, email, encrypted_phone_number, encrypted_address])
            row = cur.fetchone()

        columns = [desc[0] for desc in cur.description]
        result = dict(zip(columns, row))

    return jsonify(result), 200 if existing else 201
