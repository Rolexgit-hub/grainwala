from database import mysql
import uuid
import json
import MySQLdb
import MySQLdb.cursors

def get_user_addresses(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT id, full_address FROM user_addresses WHERE user_id=%s",
        (user_id,)
    )
    data = cursor.fetchall()
    cursor.close()
    return data
# -------------------- Product Queries --------------------
def get_featured_products(limit=8):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM products LIMIT %s", (limit,))
        rows = cur.fetchall()
    finally:
        cur.close()
    return process_product_rows(rows)

def get_popular_products(limit=8):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM popular_products LIMIT %s", (limit,))
        rows = cur.fetchall()
    finally:
        cur.close()
    return process_product_rows(rows)

def get_all_products():
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT * FROM products
            UNION ALL
            SELECT * FROM popular_products
        """)
        rows = cur.fetchall()
    finally:
        cur.close()
    return process_product_rows(rows)

def get_products_by_category(category, limit=None):
    cur = mysql.connection.cursor()
    try:
        if limit:
            cur.execute("SELECT * FROM products WHERE category=%s LIMIT %s", (category, limit))
        else:
            cur.execute("SELECT * FROM products WHERE category=%s", (category,))
        rows = cur.fetchall()
    finally:
        cur.close()
    return process_product_rows(rows)

# -------------------- User Queries --------------------
def create_user(username, email, phone, user_type, address, pincode, location, district, crop_type, payment_details, password, state="Bihar"):
    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO users
            (username, email, phone, user_type, address, pincode, location, district, crop_type, payment_details, password, state)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            username, email, phone, user_type,
            address, pincode, location, district,
            crop_type, payment_details, hashed_password, state
        ))
        mysql.connection.commit()
    finally:
        cur.close()

def get_user_by_phone(phone, user_type):
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT id, username, user_type FROM users WHERE phone=%s AND user_type=%s",
            (phone, user_type)
        )
        user = cur.fetchone()
    finally:
        cur.close()
    return user

def get_user_by_id(user_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    finally:
        cur.close()
    return user

# -------------------- Order Queries --------------------
def generate_order_id(prefix="OD", start_number=35553):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT order_id FROM orders ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
    finally:
        cur.close()

    if row and row[0].startswith(prefix):
        last_number = int(row[0][len(prefix):])
        next_number = last_number + 1
    else:
        next_number = start_number
    return f"{prefix}{next_number}"

def place_order(user_id, product_id, qty):
    order_id = generate_order_id()
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO orders (order_id, user_id, product_id, qty) VALUES (%s, %s, %s, %s)",
            (order_id, user_id, product_id, qty)
        )
        mysql.connection.commit()
    finally:
        cur.close()
    return order_id

# -------------------- Utility Functions --------------------
def process_product_rows(rows):
    """
    Process product rows to ensure images and weights are JSON-decoded safely.
    Returns list of products with proper structure.
    """
    processed = []
    for row in rows:
        product = list(row)

        # Images (assume 5th index)
        if len(product) > 5:
            img_field = product[5]
            if img_field and img_field.strip().startswith('['):
                try:
                    img_list = json.loads(img_field)
                    product[5] = img_list[0] if img_list else ''
                except Exception:
                    product[5] = ''
            else:
                product[5] = img_field or ''

        # Weights (assume 8th index)
        if len(product) > 8:
            weights_json = product[8] if product[8] else '[]'
            try:
                product[8] = json.loads(weights_json)
            except Exception:
                product[8] = []
        else:
            product.append([])

        processed.append(product)
    return processed
