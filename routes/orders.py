from flask import Blueprint, request, jsonify
from db_utils import get_cursor
from crypto_utils import encrypt_text
from config import ENCRYPTION_KEY

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

@orders_bp.route("", methods=["POST"])
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

    with get_cursor() as cur:
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
        order_row = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        order_data = dict(zip(columns, order_row))

    return jsonify(order_data), 201
