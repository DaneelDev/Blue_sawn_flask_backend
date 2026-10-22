import secrets
from flask import Blueprint, request, jsonify
from db_utils import get_cursor
from email_service import send_email_yandex

verification_bp = Blueprint("verification", __name__)

@verification_bp.route("/send-email", methods=["POST"])
def send_verification_code():
    data = request.json or {}
    email = data.get("email")
    if not email:
        return jsonify({"message": "Email обязателен"}), 400

    code = str(secrets.randbelow(900000) + 100000)  # 6 цифр, криптостойкий

    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO verification_codes (email, verification_code) VALUES (%s, %s)",
            (email, code),
        )

    subject = "Ваш код подтверждения"
    html_body = f"<h1>Ваш код подтверждения: {code}</h1>"
    send_email_yandex(email, subject, html_body)

    return jsonify({"message": "Код отправлен на ваш email"}), 200


@verification_bp.route("/verify-code", methods=["POST"])
def verify_code():
    data = request.json or {}
    email = data.get("email")
    code = data.get("code")

    if not code:
        return jsonify({"message": "Код обязателен"}), 400

    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM verification_codes WHERE verification_code = %s",
            (code,),
        )
        row = cur.fetchone()

        if row:
            cur.execute("DELETE FROM verification_codes WHERE verification_code = %s", (code,))
            return jsonify({"message": "Код успешно проверен."}), 200
        else:
            # В контексте менеджера ошибка вызовет rollback автоматически
            return jsonify({"message": "Код не найден."}), 400
