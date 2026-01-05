from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import json
from database import mysql, init_db
import uuid
import random
import string
import MySQLdb.cursors
from werkzeug.utils import secure_filename
from datetime import datetime
from models import get_products_by_category
from models import get_user_addresses
from flask import jsonify
import ast

app = Flask(__name__)
app.secret_key = "supersecretkey"
init_db(app)

app.permanent_session_lifetime = timedelta(days=7)


def get_consumer_district():
    if session.get('user_type') == 'consumer' and session.get('user_id'):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT district FROM users WHERE id=%s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        if user:
            return user['district']
    return None

@app.before_request
def make_session_permanent():
    session.permanent = True


def process_rows(rows):
    products = []

    for row in rows:
        image_list = []
        if row["image"]:
            try:
                image_list = ast.literal_eval(row["image"])   # "['a.jpg']" → ['a.jpg']
            except:
                image_list = [row["image"]]

        weight_list = []
        if row["weights"]:
            try:
                weight_list = ast.literal_eval(row["weights"])
            except:
                weight_list = [row["weights"]]

        products.append({
    "id": row["id"],
    "name": row["name"],
    "price_min": row["price_min"],
    "description": row["description"],
    "image": image_list,
    "stock_status": row["stock_status"],
    "weights": weight_list,
    "district": row["district"],
    "farmer_id": row.get("farmer_id")   # 🔥 YE LINE ADD KARO
})


    return products


def get_initials(name):
    parts = name.split()
    return "".join([p[0].upper() for p in parts if p])


# -------------------- Product Queries --------------------
def get_featured_products(district=None):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if district:
        cur.execute("""
            SELECT id, name, category, price_min, district,
                   image, stock_status, description, weights
            FROM products
            WHERE district=%s
            ORDER BY id DESC
            LIMIT 8
        """, (district,))
    else:
        cur.execute("""
            SELECT id, name, category, price_min, district,
                   image, stock_status, description, weights
            FROM products
            ORDER BY id DESC
            LIMIT 8
        """)

    rows = cur.fetchall()
    cur.close()
    return rows



def get_popular_products(district=None):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if district:
        # pehle featured ids nikal lo
        cur.execute("""
            SELECT id FROM products
            WHERE district=%s
            ORDER BY id DESC
            LIMIT 8
        """, (district,))
    else:
        cur.execute("""
            SELECT id FROM products
            ORDER BY id DESC
            LIMIT 8
        """)

    featured_ids = [str(p['id']) for p in cur.fetchall()]

    # ab popular me featured ko exclude karo
    if district:
        query = f"""
            SELECT id, name, category, price_min, district,
                   image, stock_status, description, weights
            FROM products
            WHERE district=%s
            AND id NOT IN ({','.join(featured_ids) if featured_ids else 0})
            ORDER BY id DESC
            LIMIT 8
        """
        cur.execute(query, (district,))
    else:
        query = f"""
            SELECT id, name, category, price_min, district,
                   image, stock_status, description, weights
            FROM products
            WHERE id NOT IN ({','.join(featured_ids) if featured_ids else 0})
            ORDER BY id DESC
            LIMIT 8
        """
        cur.execute(query)

    rows = cur.fetchall()
    cur.close()
    return rows


def get_all_products():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    cur.close()
    return rows



def create_user(username, email, phone, user_type,
                address, pincode, location, district,
                crop_type, payment_details, password):

    hashed_password = generate_password_hash(password)

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO users
        (username, email, phone, user_type, address, pincode, location,
         district, crop_type, payment_details, password, state)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        username, email, phone, user_type,
        address, pincode, location,
        district, crop_type, payment_details,
        hashed_password, "Bihar"
    ))
    mysql.connection.commit()
    cur.close()




def get_user_by_phone(phone, user_type):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, username, user_type
        FROM users
        WHERE phone=%s AND user_type=%s
    """, (phone, user_type))
    user = cur.fetchone()
    cur.close()
    return user


@app.context_processor
def inject_initials():
    if 'username' in session:
        return {'initials': get_initials(session['username'])}
    return {'initials': None}


# -------------------- Routes --------------------
@app.route('/')
def index():
    # District filter hata diya
    featured_products = process_rows(get_featured_products())
    popular_products = process_rows(get_popular_products())

    return render_template(
        "index.html",
        featured_products=featured_products,
        popular_products=popular_products
    )




@app.route('/products')
def products_page():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products ORDER BY id DESC")  # Show all products
    rows = cur.fetchall()
    cur.close()
    products = process_rows(rows)
    return render_template('products.html', products=products)



@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/register', methods=['POST'])
def register():
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        flash("❌ Passwords do not match!", "danger")
        return redirect(url_for('account'))

    create_user(
    request.form.get('username'),
    request.form.get('email'),
    request.form.get('phone'),
    request.form.get('user_type').strip().lower(),  # ✅ FIX
    request.form.get('address', ''),
    request.form.get('pincode', '800001'),
    request.form.get('location', ''),
    request.form.get('district'),
    request.form.get('crop_type', ''),
    request.form.get('payment_details', ''),
    password
)


    flash("✅ Registration successful. Please login.")
    return redirect(url_for('account'))


@app.route('/login', methods=['POST'])
def login():
    # 🔹 Clean inputs
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '').strip()
    user_type = request.form.get('user_type', '').strip().lower()  # consumer / farmer

    # 🔒 Basic validation
    if not phone or not password or not user_type:
        flash("❌ Please fill all fields", "danger")
        return redirect(url_for('account'))

    # 🔍 Fetch user from DB
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT id, username, password, user_type
        FROM users
        WHERE CAST(phone AS CHAR)=%s
          AND LOWER(TRIM(user_type))=%s
    """, (phone, user_type))

    user = cursor.fetchone()
    cursor.close()

    if not user:
        flash("❌ Invalid phone or password", "danger")
        return redirect(url_for('account'))

    # 🔐 Password verification (HASHED + PLAIN BOTH SUPPORTED)
    db_password = user['password']

    try:
        valid = check_password_hash(db_password, password)
    except Exception:
        valid = (db_password == password)

    if not valid:
        flash("❌ Invalid phone or password", "danger")
        return redirect(url_for('account'))

    # ✅ LOGIN SUCCESS
    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['user_type'] = user['user_type'].strip().lower()

    flash(f"✅ Welcome, {user['username']}!", "success")

    # 🚀 Role based redirect
    if session['user_type'] == 'farmer':
        return redirect(url_for('farmer_dashboard'))
    else:
        return redirect(url_for('consumer_dashboard'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '').strip().lower()

        if not phone or not user_type:
            flash("❌ All fields are required", "danger")
            return redirect(url_for('forgot_password'))

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id FROM users
            WHERE phone=%s AND LOWER(user_type)=%s
        """, (phone, user_type))
        user = cur.fetchone()
        cur.close()

        if not user:
            flash("❌ User not found", "danger")
            return redirect(url_for('forgot_password'))

        # ✅ Temporarily store user id
        session['reset_user_id'] = user['id']

        return redirect(url_for('reset_password'))

    return render_template('forgot_password.html',hide_footer=True)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        flash("❌ Session expired. Try again.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("❌ Passwords do not match", "danger")
            return redirect(url_for('reset_password'))

        hashed_password = generate_password_hash(new_password)

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE users SET password=%s WHERE id=%s
        """, (hashed_password, session['reset_user_id']))
        mysql.connection.commit()
        cur.close()

        # ✅ Clear reset session
        session.pop('reset_user_id', None)

        flash("✅ Password reset successful. Please login.", "success")
        return redirect(url_for('account'))

    return render_template('reset_password.html',hide_footer=True)

@app.route('/logout')
def logout():
    session.clear()
    flash("✅ You have been logged out.")
    return redirect(url_for('index'))


def get_user_data(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user


@app.route('/consumer_dashboard', methods=['GET', 'POST'])
def consumer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'consumer':
        return redirect(url_for('account'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE users SET
                username=%s,
                email=%s,
                phone=%s,
                address=%s,
                district=%s,
                state='Bihar',
                pincode=%s
            WHERE id=%s
        """, (
            request.form['username'],
            request.form['email'],
            request.form['phone'],
            request.form['address'],
            request.form['district'],
            request.form['pincode'],
            session['user_id']
        ))
        mysql.connection.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for('consumer_dashboard'))

    cursor.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cursor.fetchone()
    return render_template("consumer_dashboard.html", user=user,  hide_footer=True)

@app.route('/farmer_dashboard', methods=['GET', 'POST'])
def farmer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'farmer':
        return redirect(url_for('account'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE users SET
                username=%s,
                email=%s,
                phone=%s,
                location=%s,
                district=%s,
                state='Bihar',
                pincode=%s,
                crop_type=%s,
                payment_details=%s
            WHERE id=%s
        """, (
            request.form['username'],
            request.form['email'],
            request.form['phone'],
            request.form['location'],
            request.form['district'],
            request.form['pincode'],
            request.form['crop_type'],
            request.form['payment_details'],
            session['user_id']
        ))
        mysql.connection.commit()
        flash("Farmer profile updated successfully", "success")
        return redirect(url_for('farmer_dashboard'))

    cursor.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cursor.fetchone()
    return render_template("farmer_dashboard.html", user=user,   hide_footer=True)



# Route for each category (dropdown link se jayega)
@app.route('/category/<cat_name>')
def category_products(cat_name):
    categories_map = {
        'grains-pulses': 'Grains & Pulses',
        'vegetables': 'Fresh Vegetables',
        'fruits': 'Fresh Fruits',
        'spices-herbs': 'Spices & Herbs',
        'oil-seeds': 'Oil Seeds & Nuts',
        'other': 'Other'
    }

    db_category = categories_map.get(cat_name)
    if not db_category:
        flash("❌ Category not found.")
        return redirect(url_for('index'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # District filter hata diya
    cur.execute("SELECT * FROM products WHERE category=%s", (db_category,))
    rows = cur.fetchall()
    cur.close()

    products = process_rows(rows)
    return render_template('category_products.html', products=products, category=db_category)


@app.route('/search')
def search():
    query = request.args.get("query", "")

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # District filter hata diya
    cur.execute("""
        SELECT * FROM products
        WHERE LOWER(name) LIKE %s OR LOWER(description) LIKE %s
    """, (f"%{query.lower()}%", f"%{query.lower()}%"))

    rows = cur.fetchall()
    cur.close()

    products = process_rows(rows)
    return render_template("search_results.html", products=products, search_query=query)
    
@app.route('/track_order', methods=['GET', 'POST'])
def track_order():
    order_info = None
    error_message = None

    if request.method == 'POST':
        order_id = request.form.get('order_id')

        if not order_id or not order_id.startswith("OD"):
            error_message = "❌ Please enter a valid Order ID (eg: OD12345678)"
        else:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # 🔹 Order basic info
            cur.execute("""
                SELECT order_id, status, created_at
                FROM orders
                WHERE order_id=%s
            """, (order_id,))
            order = cur.fetchone()

            if not order:
                error_message = "❌ Order ID not found."
                cur.close()
            else:
                # 🔹 Order items
                cur.execute("""
                    SELECT product_name, quantity, price
                    FROM order_items
                    WHERE order_id=%s
                """, (order_id,))
                items = cur.fetchall()
                cur.close()

                order_info = {
                    "order_id": order["order_id"],
                    "status": order["status"],
                    "placed_at": order["created_at"],
                    "items": items
                }

    return render_template(
        "track_order.html",
        order_info=order_info,
        error_message=error_message
    )

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):

    # 🔐 LOGIN CHECK
    if 'user_id' not in session:
        flash("❌ Please login to add products to cart.", "danger")
        return redirect(url_for('account'))

    user_id = session['user_id']
    user_type = session['user_type']

    # 🔹 Fetch product owner
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT farmer_id FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()
    cur.close()

    if not product:
        flash("❌ Product not found.", "danger")
        return redirect(request.referrer or url_for('products_page'))

    # 🚫 Farmer cannot buy own product
    if user_type == 'farmer' and product['farmer_id'] == user_id:
        flash("❌ आप अपने उत्पाद को नहीं खरीद सकते।", "danger")
        return redirect(request.referrer or url_for('products_page'))

    # 🔹 Normal cart logic
    qty = int(request.form.get('qty', 1))
    weight = request.form.get('weight', '')

    if 'cart' not in session:
        session['cart'] = {}

    key = f"{product_id}_{weight}" if weight else str(product_id)

    if key in session['cart']:
        session['cart'][key]['qty'] += qty
    else:
        session['cart'][key] = {
            'product_id': product_id,
            'qty': qty,
            'weight': weight
        }

    session.modified = True
    flash("✅ Product added to cart!", "success")
    return redirect(request.referrer or url_for('products_page'))

@app.route('/cart')
def cart():

    # 🔐 LOGIN CHECK (farmer + consumer both allowed)
    if 'user_id' not in session:
        flash("❌ Please login to view your cart.", "danger")
        return redirect(url_for('account'))

    cart_items = []
    total_price = 0

    if 'cart' in session:
        for key, item in session['cart'].items():
            product_id = item['product_id']
            cur = mysql.connection.cursor()
            cur.execute("SELECT id, name, price_min, image FROM products WHERE id=%s", (product_id,))
            p = cur.fetchone()
            cur.close()

            if p:
                qty = item['qty']
                price = p[2]
                subtotal = price * qty
                total_price += subtotal

                img_field = p[3]
                try:
                    img_list = json.loads(img_field) if img_field else []
                    img_name = img_list[0] if img_list else ''
                except:
                    img_name = ''

                cart_items.append({
                    'key': key,
                    'id': p[0],
                    'name': p[1],
                    'price': price,
                    'image': img_name,
                    'qty': qty,
                    'subtotal': subtotal
                })

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    key = request.form.get('key')
    qty = int(request.form.get('qty', 1))
    if 'cart' in session and key in session['cart']:
        session['cart'][key]['qty'] = qty
        session.modified = True
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<key>')
def remove_from_cart(key):
    if 'cart' in session and key in session['cart']:
        del session['cart'][key]
        session.modified = True
    return redirect(url_for('cart'))


# -------------------- Checkout / Place Order Flow --------------------
@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect(url_for("account"))

    if "cart" not in session or not session["cart"]:
        flash("🛒 Your cart is empty")
        return redirect(url_for("products_page"))

    cart_items = []
    totalprice = 0
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    for item in session["cart"].values():
        cur.execute(
            "SELECT id, name, price_min FROM products WHERE id=%s",
            (item["product_id"],)
        )
        product = cur.fetchone()
        if product:
            subtotal = product["price_min"] * item["qty"]
            totalprice += subtotal
            cart_items.append({
                "name": product["name"],
                "qty": item["qty"],
                "price": product["price_min"],
                "subtotal": subtotal
            })

    # ✅ FETCH SAVED ADDRESSES
    cur.execute("""
        SELECT * FROM user_addresses
        WHERE user_id=%s
        ORDER BY is_default DESC, id DESC
    """, (session["user_id"],))
    addresses = cur.fetchall()
    cur.close()

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        totalprice=totalprice,
        addresses=addresses,
        hide_footer=True
    )

# PROCESS PAYMENT
# -------------------------------
@app.route("/process_payment", methods=["POST"])
def process_payment():

    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("account"))

    if "cart" not in session or not session["cart"]:
        flash("Your cart is empty")
        return redirect(url_for("checkout"))

    payment_method = request.form.get("paymentmethod")
    ship_name = request.form.get("ship_name")
    ship_phone = request.form.get("ship_phone")
    ship_address = request.form.get("ship_address")

    order_id = "OD" + "".join(random.choices(string.digits, k=8))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 🔢 TOTAL CALC
    total_amount = 0
    for item in session["cart"].values():
        cur.execute("SELECT price_min FROM products WHERE id=%s", (item["product_id"],))
        p = cur.fetchone()
        if p:
            total_amount += p["price_min"] * item["qty"]

    # ✅ STEP 1: INSERT ORDER FIRST (PARENT)
    cur.execute("""
        INSERT INTO orders
        (order_id, user_id, full_name, phone, address,
         total_amount, payment_method, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        order_id,
        session["user_id"],
        ship_name,
        ship_phone,
        ship_address,
        total_amount,
        payment_method,
        "Placed"
    ))

    # ✅ STEP 2: INSERT ORDER ITEMS (CHILD)
    for item in session["cart"].values():
        cur.execute(
            "SELECT id, name, price_min FROM products WHERE id=%s",
            (item["product_id"],)
        )
        product = cur.fetchone()

        if product:
            cur.execute("""
                INSERT INTO order_items
                (order_id, product_id, product_name, quantity, price)
                VALUES (%s,%s,%s,%s,%s)
            """, (
                order_id,
                product["id"],
                product["name"],
                item["qty"],
                product["price_min"]
            ))

    mysql.connection.commit()
    cur.close()

    session.pop("cart", None)

    return redirect(url_for("order_confirmation", order_id=order_id))

@app.route('/order-confirmation/<order_id>')
def order_confirmation(order_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT order_id, full_name, total_amount, status 
        FROM orders 
        WHERE order_id=%s
    """, (order_id,))
    order = cursor.fetchone()
    cursor.close()

    if not order:
        flash("Order not found")
        return redirect(url_for('index'))

    return render_template(
        'order_confirmation.html',
        order_id=order[0],
        full_name=order[1],
        total_amount=order[2],
        status=order[3],
        hide_footer=True
    )
# -------------------- Consumer Orders Section --------------------

@app.route('/consumer/orders')
def consumer_orders():
    if 'user_id' not in session:
        return redirect(url_for('account'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT order_id, total_amount, status, created_at
        FROM orders
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (session['user_id'],))
    orders = cur.fetchall()
    cur.close()

    return render_template('consumer/orders.html', orders=orders)

@app.route('/consumer/orders/<order_id>')
def consumer_order_detail(order_id):
    if 'user_id' not in session or session.get('user_type') != 'consumer':
        flash("❌ Please login as a consumer to view order details")
        return redirect(url_for('account'))

    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT * FROM orders 
        WHERE order_id = %s AND user_id = %s
    """, (order_id, user_id))
    order = cur.fetchone()

    if not order:
        flash("❌ Order not found.")
        return redirect(url_for('consumer_orders'))

    cur.execute("""
        SELECT product_name, quantity, price 
        FROM order_items 
        WHERE order_id = %s
    """, (order_id,))
    items = cur.fetchall()
    cur.close()

    return render_template('consumer/order_detail.html', order=order, items=items, hide_footer=True)

@app.route('/get_address/<int:address_id>')
def get_address(address_id):
    if 'user_id' not in session:
        return {"error": "unauthorized"}, 401

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT id, fullname, phone, address, city, state, pincode
        FROM user_addresses
        WHERE id=%s AND user_id=%s
    """, (address_id, session['user_id']))

    addr = cur.fetchone()
    cur.close()

    if not addr:
        return {"error": "not found"}, 404

    return jsonify(addr)


@app.route('/add_address', methods=['POST'])
def add_address():
    if 'user_id' not in session:
        return jsonify({"ok": False, "msg": "Login required"})

    user_id = session['user_id']
    data = request.form

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO user_addresses
        (user_id, fullname, phone, address, city, state, pincode, is_default)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        data.get('fullname'),
        data.get('phone'),
        data.get('address'),
        data.get('city'),
        data.get('state'),
        data.get('pincode'),
        0
    ))
    mysql.connection.commit()
    cur.close()

    flash("✅ Address added successfully!")
    return redirect(url_for('checkout'))

@app.route('/edit_address/<int:address_id>', methods=['POST'])
def edit_address(address_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    user_id = session['user_id']
    data = request.form

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE user_addresses SET
        fullname=%s, phone=%s, address=%s, city=%s, state=%s, pincode=%s
        WHERE id=%s AND user_id=%s
    """, (
        data.get('fullname'),
        data.get('phone'),
        data.get('address'),
        data.get('city'),
        data.get('state'),
        data.get('pincode'),
        address_id,
        user_id
    ))
    mysql.connection.commit()
    cur.close()

    flash("✅ Address updated successfully!")
    return redirect(url_for('checkout'))

@app.route('/delete_address/<int:address_id>', methods=['POST'])
def delete_address(address_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_addresses WHERE id=%s AND user_id=%s", (address_id, user_id))
    mysql.connection.commit()
    cur.close()

    flash("✅ Address deleted!")
    return redirect(url_for('checkout'))

@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO support_messages (name, email, message) VALUES (%s, %s, %s)", 
                       (name, email, message))
        mysql.connection.commit()
        cursor.close()

        flash("✅ आपका संदेश सेव हो गया है। हमारी टीम जल्द ही संपर्क करेगी।")
        return redirect(url_for('support'))

    return render_template('support.html')

@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if 'user_id' not in session:
        flash('❌ Login required to add wishlist!', 'danger')
        return redirect(url_for('account'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM wishlist WHERE user_id=%s AND product_id=%s", (user_id, product_id))
    exists = cur.fetchone()
    if exists:
        flash('❗ Already in your wishlist.', 'info')
    else:
        cur.execute("INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
        mysql.connection.commit()
        flash('✅ Added to wishlist!', 'success')
    cur.close()
    return redirect(request.referrer or url_for('products_page'))

# Remove product from wishlist
@app.route('/remove_from_wishlist/<int:wishlist_id>', methods=['POST'])
def remove_from_wishlist(wishlist_id):
    if 'user_id' not in session:
        flash('❌ Login required!', 'danger')
        return redirect(url_for('account'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM wishlist WHERE id=%s AND user_id=%s", (wishlist_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('🗑️ Removed from wishlist.', 'success')
    return redirect(url_for('wishlist'))

# Wishlist page
@app.route('/wishlist')
def wishlist():
    if 'user_id' not in session:
        flash("❌ Login required!", 'danger')
        return redirect(url_for('account'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT wishlist.id, products.id AS product_id, products.name, products.price_min, products.price_max, products.image, products.category
        FROM wishlist
        JOIN products ON wishlist.product_id=products.id
        WHERE wishlist.user_id=%s
        ORDER BY wishlist.added_at DESC
    """, (user_id,))
    items = cur.fetchall()
    cur.close()

    # Ensure JSON
    processed_items = []
    for item in items:
        item = list(item)
        img_field = item[5]
        if img_field and img_field.strip().startswith('['):
            try:
                item[5] = json.loads(img_field)
            except:
                item[5] = []
        else:
            item[5] = [img_field] if img_field else []
        processed_items.append(item)

    return render_template('wishlist.html', wishlist=processed_items)


@app.route('/subscribe', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('newsletter_email')
    if not email or '@' not in email:
        flash("❌ Please enter a valid email address.", "danger")
        return redirect(request.referrer or url_for('privacy_policy'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM newsletter_subscribers WHERE email = %s", (email,))
    exists = cur.fetchone()
    if exists:
        flash("⚡ You are already subscribed!", "info")
    else:
        cur.execute("INSERT INTO newsletter_subscribers (email) VALUES (%s)", (email,))
        mysql.connection.commit()
        flash("✅ Thank you for subscribing!", "success")
    cur.close()
    return redirect(request.referrer or url_for('privacy_policy'))

@app.route('/return-policy')
def return_policy():
    return render_template('return_policy.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')\
    
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session.get('user_type') != 'farmer':
        flash("कृपया पहले farmer के रूप में login करें", "danger")
        return redirect(url_for('account'))

    if request.method == 'POST':

        # ===== FORM DATA (HTML TEMPLATE KE HISAB SE) =====
        name = request.form.get('product_name')
        category = request.form.get('category')
        variety = request.form.get('variety','')
        weight_raw = request.form.get('weight_options','')
        weights = [w.strip() for w in weight_raw.split(',') if w.strip()]
        contact_number = request.form.get('contact_number')
        quantity = request.form.get('quantity', 0)
        stock_status = request.form.get('stock_status')
        price_per_unit = request.form.get('price_per_unit')
        negotiable = request.form.get('negotiable', 0)
        location = request.form.get('location')
        delivery_available = request.form.get('delivery_available', 0)
        harvest_date = request.form.get('harvest_date')
        description = request.form.get('description','')

        images = request.files.getlist('images')
        farmer_id = session['user_id']

        # ===== FARMER DISTRICT AUTO FETCH =====
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT district FROM users WHERE id=%s", (farmer_id,))
        farmer = cur.fetchone()
        cur.close()
        farmer_district = farmer['district'] if farmer else ''

        # ===== IMAGE UPLOAD SAFE =====
        image_filenames = []
        for img in images:
            if img and allowed_file(img.filename):
                filename = secure_filename(img.filename)
                unique_name = f"{uuid.uuid4()}_{filename}"
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                image_filenames.append(unique_name)

        # ===== INSERT PRODUCT =====
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO products
            (farmer_id, name, category, variety, price_min, price_max, image, stock_status,
             description, weights, quantity, contact_number, negotiable, location,
             delivery_available, harvest_date, district)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            farmer_id,
            name,
            category,
            variety,
            price_per_unit,
            price_per_unit,
            json.dumps(image_filenames),
            stock_status,
            description,
            json.dumps(weights),
            quantity,
            contact_number,
            negotiable,
            location,
            delivery_available,
            harvest_date,
            farmer_district
        ))

        mysql.connection.commit()
        cur.close()

        flash("Product successfully added!", "success")
        return redirect(url_for('farmer_dashboard'))

    return render_template('add_product.html')

@app.route('/farmer/manage_products')
def farmer_manage_products():
    # Check login
    if 'user_id' not in session or session.get('user_type') != 'farmer':
        flash("Please login as a farmer to continue.", "warning")
        return redirect(url_for('login'))

    farmer_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, name, category, price_min, price_max, stock_status, description, weights, image, created_at
        FROM products
        WHERE farmer_id = %s
        ORDER BY created_at DESC
    """, (farmer_id,))
    rows = cur.fetchall()
    cur.close()

    products = []
    for row in rows:
        p = dict(zip(['id','name','category','price_min','price_max','stock_status','description','weights','image','created_at'], row))
        try:
            p['weights'] = json.loads(p['weights']) if p['weights'] else []
        except:
            p['weights'] = []
        try:
            p['image'] = json.loads(p['image']) if p['image'] else []
        except:
            p['image'] = []
        products.append(p)

    return render_template('farmer_manage_products.html', products=products)


@app.route('/farmer/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    farmer_id = session.get('user_id')
    if not farmer_id:
        flash("Please login to continue.", "warning")
        return redirect(url_for('farmer_login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id = %s AND farmer_id = %s", (product_id, farmer_id))
    mysql.connection.commit()
    cur.close()
    flash("Product deleted successfully.", "success")
    return redirect(url_for('farmer_manage_products'))


# -------------------- Edit Product Route --------------------
@app.route('/farmer/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    # Farmer login check
    if 'user_id' not in session or session.get('user_type') != 'farmer':
        flash("❌ Access denied!", "danger")
        return redirect(url_for('account'))

    # Fetch product for this farmer
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM products WHERE id=%s AND farmer_id=%s", (product_id, session['user_id']))
    product = cur.fetchone()
    cur.close()

    if not product:
        flash("❌ Product not found!", "danger")
        return redirect(url_for('farmer_manage_products'))

    # Decode JSON fields
    try:
        product['image'] = json.loads(product['image']) if product['image'] else []
    except:
        product['image'] = []

    try:
        product['weights'] = json.loads(product['weights']) if product['weights'] else []
    except:
        product['weights'] = []

    # Handle form submission
    if request.method == 'POST':
        # Product fields
        name = request.form['product_name']
        category = request.form['category']
        price_per_unit = request.form.get('price_per_unit', 0)
        stock_status = request.form.get('stock_status', '')
        description = request.form.get('description', '')
        quantity = request.form.get('quantity', 0)
        contact_number = request.form.get('contact_number', '')
        negotiable = request.form.get('negotiable', 0)
        location = request.form.get('location', '')
        delivery_available = request.form.get('delivery_available', 0)
        harvest_date = request.form.get('harvest_date', None)
        variety = request.form.get('variety', '')

        # Weights
        weights_raw = request.form.get('weight_options', '')
        weights_list = [w.strip() for w in weights_raw.split(',') if w.strip()]
        weights_json = json.dumps(weights_list)

        # Images: replace only if user selected new images
        images = request.files.getlist('images')
        if images and any(img.filename for img in images):
            # User selected new images → replace old
            saved_images = []
            for img in images:
                if img and allowed_file(img.filename):
                    filename = secure_filename(img.filename)
                    unique_filename = f"{str(uuid.uuid4())}_{filename}"
                    img.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    saved_images.append(unique_filename)
        else:
            # No new images → keep old
            saved_images = product['image']

        images_json = json.dumps(saved_images)

        # Update DB
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE products SET name=%s, category=%s, price_min=%s, price_max=%s,
            stock_status=%s, description=%s, weights=%s, image=%s, quantity=%s,
            contact_number=%s, negotiable=%s, location=%s, delivery_available=%s, harvest_date=%s, variety=%s
            WHERE id=%s AND farmer_id=%s
        """, (
            name, category, price_per_unit, price_per_unit,
            stock_status, description, weights_json, images_json, quantity,
            contact_number, negotiable, location, delivery_available, harvest_date, variety,
            product_id, session['user_id']
        ))
        mysql.connection.commit()
        cur.close()

        flash("✅ Product updated successfully!", "success")
        return redirect(url_for('farmer_manage_products'))

    return render_template('edit_product.html', product=product)


# -------------------- Farmer: Orders Received (List + Detail + Update) --------------------

@app.route('/farmer/orders')
def farmer_orders():
    if 'user_id' not in session or session.get('user_type') != 'farmer':
        flash("कृपया farmer के रूप में login करें")
        return redirect(url_for('login'))

    farmer_id = session['user_id']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT 
            oi.id AS order_item_id,
            oi.order_id,
            oi.product_id,
            oi.product_name,
            oi.quantity,
            oi.price,
            o.full_name AS buyer_name,
            o.phone AS buyer_phone,
            o.address AS buyer_address,
            o.status AS order_status,
            o.created_at
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE p.farmer_id = %s
        ORDER BY o.created_at DESC, oi.id DESC
    """, (farmer_id,))
    
    orders = cur.fetchall()
    cur.close()

    return render_template('farmer_orders.html', orders=orders)


@app.route('/farmer/order/<string:order_id>')
def farmer_order_detail(order_id):
    if 'user_id' not in session or session.get('user_type') != 'farmer':
        flash("⚠️ Please login as a farmer.", "danger")
        return redirect(url_for('account'))

    farmer_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Order info (single row)
    cur.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cur.fetchone()

    # Items in this order that belong to this farmer
    cur.execute("""
        SELECT oi.*, p.name AS product_name, p.image AS product_images
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s AND p.farmer_id = %s
    """, (order_id, farmer_id))
    items = cur.fetchall()
    cur.close()

    if not order:
        flash("❌ Order not found.", "danger")
        return redirect(url_for('farmer_orders'))

    return render_template('farmer_order_detail.html', order=order, items=items)


@app.route('/farmer/update_order_status/<order_id>', methods=['POST'])
def farmer_update_order_status(order_id):
    new_status = request.form.get('status')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT status FROM orders WHERE order_id=%s", (order_id,))
    order = cursor.fetchone()

    if not order:
        flash("Order not found", "danger")
        return redirect(request.referrer)

    # ❌ Cancel restriction
    if new_status == "Cancelled" and order['status'] not in ['Placed','Packed']:
        flash("Order cannot be cancelled after shipment", "danger")
        return redirect(request.referrer)

    cursor.execute(
        "UPDATE orders SET status=%s WHERE order_id=%s",
        (new_status, order_id)
    )
    mysql.connection.commit()

    flash("Order status updated successfully", "success")
    return redirect(request.referrer)



@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s)


@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    order_id = request.form.get('order_id')
    product_id = request.form.get('product_id')
    rating = request.form.get(f'rating_{product_id}')
    comment = request.form.get('comment')

    user_id = session.get('user_id')  

    if not all([order_id, product_id, rating, comment, user_id]):
        flash('❌ All fields are required.', 'danger')

        # Redirect depending on user type
        if session.get('user_type') == 'farmer':
            return redirect(url_for('farmer_order_detail', order_id=order_id))
        else:
            return redirect(url_for('consumer_order_detail', order_id=order_id))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO feedback (order_id, product_id, user_id, rating, comment, consumer_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (order_id, product_id, user_id, rating, comment, user_id))
    mysql.connection.commit()
    cursor.close()

    flash('✅ Feedback submitted successfully!', 'success')

    # Redirect to the proper order detail page depending on user type
    if session.get('user_type') == 'farmer':
        return redirect(url_for('farmer_order_detail', order_id=order_id))
    else:
        return redirect(url_for('consumer_order_detail', order_id=order_id))




@app.route('/farmer/feedback')
def farmer_feedback():
    if 'user_id' not in session or session.get('user_type') != 'farmer':
        flash("⚠️ Please login as a farmer to view feedback.", "warning")
        return redirect(url_for('account'))

    farmer_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("""
        SELECT f.rating, f.comment, f.created_at,
               p.name AS product_name,
               u.username AS consumer_name
        FROM feedback f
        JOIN products p ON f.product_id = p.id
        JOIN users u ON f.consumer_id = u.id
        WHERE p.farmer_id = %s
        ORDER BY f.created_at DESC
    """, (farmer_id,))
    
    feedbacks = cur.fetchall()
    cur.close()

    return render_template('farmer_feedback.html', feedbacks=feedbacks)





if __name__ == '__main__':
    app.run(debug=True)
