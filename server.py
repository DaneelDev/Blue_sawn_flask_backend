import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import psycopg2
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env")
if not ENCRYPTION_KEY or len(ENCRYPTION_KEY) != 64:
    raise RuntimeError("ENCRYPTION_KEY должен быть ровно 64 HEX-символа (32 байта)")


# --- Маршруты ---

@app.route("/products", methods=["GET"])
def get_products():
    category = request.args.get("category")
    _sort = request.args.get("_sort", "id")
    _order = request.args.get("_order", "DESC")

    # Белый список разрешённых колонок для сортировки
    allowed_sort = ["name", "price", "created_at", "id"]

    # Если прислали что-то не из списка — ставим безопасное значение
    sort_column = _sort if _sort in allowed_sort else "id"
    order_dir = "ASC" if _order.lower() == "asc" else "DESC"

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            if category:
                # category — это параметр, его передаём через %s
                query = f"SELECT * FROM products WHERE category = %s ORDER BY {sort_column} {order_dir}"
                cur.execute(query, (category,))
            else:
                # Без категории — только сортировка
                query = f"SELECT * FROM products ORDER BY {sort_column} {order_dir}"
                cur.execute(query)

            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            products = [dict(zip(columns, row)) for row in rows]

        return jsonify(products), 200
    except Exception as e:
        print("❌ Ошибка в /products:")
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if conn:
            conn.close()



# --- Шифрование / Расшифровка ---
def encrypt_text(text: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex) #converts hex key into bytes
    iv = os.urandom(12) #random initialisation vector
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()) #create encrypt obj with validation
    encryptor = cipher.encryptor() #configure the encrypt process
    ciphertext = encryptor.update(text.encode("utf-8")) + encryptor.finalize() #create an encrypted string in utf-8
    tag = encryptor.tag #need to decrypt the ciphertext
    blob = iv + tag + ciphertext
    return base64.b64encode(blob).decode("ascii") #encodes bin into base64 then decodes to ascii sctr

def decrypt_text(b64_data: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex)
    blob = base64.b64decode(b64_data)
    iv = blob[0:12]
    tag = blob[12:28]
    ciphertext = blob[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode("utf-8")


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json or {}
    recipient_name = data.get("recipientName")
    recipient_phone = data.get("recipientPhone")
    recipient_address = data.get("recipientAddress")
    products = data.get("products", [])
    total_quantity = data.get("totalQuantity")
    total_price = data.get("totalPrice")

    if not ENCRYPTION_KEY:
        return jsonify({"message": "Ошибка конфигурации сервера"}), 500

    encrypted_name = encrypt_text(recipient_name, ENCRYPTION_KEY)
    encrypted_phone = encrypt_text(recipient_phone, ENCRYPTION_KEY)
    encrypted_address = encrypt_text(recipient_address, ENCRYPTION_KEY)
    json_products = str(products).replace("'", '"')

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            query = """
                INSERT INTO orders
                (recipient_name, recipient_phone, recipient_address, products, total_quantity, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *;
            """
            cur.execute(query, [
                encrypted_name,
                encrypted_phone,
                encrypted_address,
                json_products,
                total_quantity,
                total_price,
            ])
            order_row = cur.fetchone() #raw data without columns
            columns = [desc[0] for desc in cur.description] #columns
            order_data = dict(zip(columns, order_row)) #create JSON obj
        conn.commit() #save changes
        return jsonify(order_data), 201
    except Exception as e:
        if conn:
            conn.rollback()
        print("Ошибка при вставке заказа:", e)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500
    finally:
        if conn:
            conn.close() #close connection with DB

# --- SMTP (Yandex mail) ---
def send_email_yandex(to_email: str, subject: str, html_body: str):
    msg = MIMEText(html_body, "html", "utf-8")
    msg["From"] = formataddr((str(Header("Магазин", "utf-8")), SMTP_USER))
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    with smtplib.SMTP_SSL("smtp.yandex.ru", 465) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# --- Verification block ---
@app.route("/send-email", methods=["POST"])
def send_verification_code():
    data = request.json or {}
    email = data.get("email")
    if not email:
        return jsonify({"message": "Email обязателен"}), 400

    code = str(random.randint(100000, 999999))

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO verification_codes (email, verification_code) VALUES (%s, %s)",
                (email, code),
            )
        conn.commit()

        subject = "Ваш код подтверждения"
        html_body = f"<h1>Ваш код подтверждения: {code}</h1>"
        send_email_yandex(email, subject, html_body)

        print(f"Код {code} отправлен на email {email}")
        return jsonify({"message": "Код отправлен на ваш email"}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print("Ошибка при отправке email:", e)
        return jsonify({"message": "Ошибка при отправке кода"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/verify-code", methods=["POST"])
def verify_code():
    data = request.json or {}
    email = data.get("email")
    code = data.get("code")

    if not code:
        return jsonify({"message": "Код обязателен"}), 400

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM verification_codes WHERE verification_code = %s",
                (code,),
            )
            row = cur.fetchone()

            if row:
                cur.execute("DELETE FROM verification_codes WHERE verification_code = %s", (code,))
                conn.commit()
                return jsonify({"message": "Код успешно проверен."}), 200
            else:
                conn.rollback()
                return jsonify({"message": "Код не найден."}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        print("Ошибка при проверке кода:", e)
        return jsonify({"message": "Ошибка при проверке кода."}), 500
    finally:
        if conn:
            conn.close()


@app.route("/users", methods=["GET"])
def get_user():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Email обязателен"}), 400

    if not ENCRYPTION_KEY:
        return jsonify({"message": "Ошибка конфигурации сервера"}), 500

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
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
    except Exception as e:
        print("Ошибка получения данных пользователя:", e)
        return jsonify({"message": "Ошибка сервера"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/users", methods=["POST"])
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

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
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
                columns = [desc[0] for desc in cur.description]
                result = dict(zip(columns, row))
                conn.commit()
                return jsonify(result), 200
            else:
                cur.execute("""
                    INSERT INTO users (name, email, phone_number, address)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *;
                """, [encrypted_name, email, encrypted_phone_number, encrypted_address])
                row = cur.fetchone()
                columns = [desc[0] for desc in cur.description]
                result = dict(zip(columns, row))
                conn.commit()
                return jsonify(result), 201
    except Exception as e:
        if conn:
            conn.rollback()
        print("Ошибка при сохранении данных пользователя:", e)
        return jsonify({"message": "Ошибка сервера при сохранении пользователя"}), 500
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    print(f"Server running on port {port}")
    app.run(host="0.0.0.0", port=port)
