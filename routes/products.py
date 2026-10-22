from flask import Blueprint, request, jsonify
from db_utils import get_cursor

products_bp = Blueprint("products", __name__, url_prefix="/products")

@products_bp.route("", methods=["GET"])
def get_products():
    category = request.args.get("category")
    _sort = request.args.get("_sort", "id")
    _order = request.args.get("_order", "DESC")

    allowed_sort = ["name", "price", "created_at", "id"]
    sort_column = _sort if _sort in allowed_sort else "id"
    order_dir = "ASC" if _order.lower() == "asc" else "DESC"

    query = f"SELECT * FROM products ORDER BY {sort_column} {order_dir}"
    params = ()
    if category:
        query = f"SELECT * FROM products WHERE category = %s ORDER BY {sort_column} {order_dir}"
        params = (category,)

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        products = [dict(zip(columns, row)) for row in rows]

    return jsonify(products), 200
