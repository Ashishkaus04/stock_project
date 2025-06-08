from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from flask_cors import CORS
import functools
import os
# import sqlite3 # No longer needed if using PostgreSQL

# Import from local packages
from app.database import db
from app.utils.user_management import user_manager

def create_app():
    # Set static_folder relative to the instance path of the app (or to the current working directory after cd src)
    app = Flask(__name__, static_folder='../../static')
    CORS(app)

    # Ensure database tables are created on startup if they don't exist
    with app.app_context(): # Essential for Flask-SQLAlchemy, good practice even without it
        if not db.tables_exist():
            db.create_tables()

        # Create a default admin user if no users exist
        if db.get_user_count() == 0:
            print("No users found. Creating default admin user...")
            user_manager.create_user("admin", "admin123", "admin")
            print("Default admin user created.")

    def login_required(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No authorization token provided"}), 401
            
            token = auth_header.split(' ')[1]
            user = user_manager.verify_session(token)
            
            if not user:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Pass the user object to the decorated function
            return f(*args, user=user, **kwargs)
        return decorated_function

    @app.route('/')
    def index():
        return 'Stock Management API'

    # Route to serve static files (like version.json)
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        user = user_manager.verify_user(username, password)
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Create a new session
        token = user_manager.create_session(user['id'])
        
        return jsonify({
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role']
            }
        })

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout(user):
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        user_manager.delete_session(token)
        return jsonify({"message": "Logged out successfully"})

    @app.route('/products', methods=['GET'])
    @login_required
    def get_products(user):
        try:
            # Get the search term from the query parameters
            search_term = request.args.get('search')
            
            # Pass the search term to the database function
            products = db.get_all_products(search_term)
            
            # Convert list of tuples to list of dicts, including the last_changed_by_user_id
            product_list = []
            for product_id, name, category, quantity, min_stock, last_changed_by_user_id in products:
                product_list.append({
                    'id': product_id,
                    'name': name,
                    'category': category,
                    'quantity': quantity,
                    'min_stock': min_stock,
                    'last_changed_by_user_id': last_changed_by_user_id # Include the user ID
                })
            return jsonify(product_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/product/<int:product_id>', methods=['GET', 'DELETE'])
    @login_required
    def get_product(product_id, user):
        if request.method == 'GET':
            product = db.get_product_details(product_id)
            if product:
                # Convert tuple to dict for better JSON representation
                product_dict = {
                    'id': product_id,
                    'name': product[0],
                    'category': product[1],
                    'quantity': product[2],
                    'min_stock': product[3],
                    'created_date': product[4].isoformat() if isinstance(product[4], datetime) else str(product[4])
                }
                return jsonify(product_dict)
            return jsonify({'error': 'Product not found'}), 404

        elif request.method == 'DELETE':
            try:
                # Assuming a delete_product function exists in db.py
                deleted_count = db.delete_product(product_id)
                if deleted_count > 0:
                    return jsonify({'success': f'Product with ID {product_id} deleted'}), 200
                else:
                    return jsonify({'error': f'Product with ID {product_id} not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    @app.route('/product', methods=['POST'])
    @login_required
    def add_product(user):
        data = request.get_json()
        name = data.get('name')
        category = data.get('category')
        quantity = data.get('quantity')
        min_stock = data.get('min_stock')
        
        if not all([name, category, quantity, min_stock]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        try:
            product_id = db.add_product(name, category, quantity, min_stock)
            return jsonify({'id': product_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/product/<int:product_id>/quantity', methods=['PUT'])
    @login_required
    def update_product_qty(product_id, user):
        data = request.json
        if not data or not 'new_quantity' in data:
            return jsonify({'error': 'Missing new_quantity'}), 400

        new_quantity = data.get('new_quantity')
        seller_name = data.get('seller_name') # Will be buyer_name when removing
        invoice_number = data.get('invoice_number')

        try:
            db.update_product_quantity(product_id, new_quantity, seller_name, invoice_number, user_id=user['id'])
            return jsonify({'success': 'Quantity updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/product/<int:product_id>/history', methods=['GET'])
    @login_required
    def get_history(product_id, user):
        history = db.get_quantity_history(product_id)
        # Convert list of tuples to list of dicts
        history_list = []
        for old_qty, new_qty, change_date, name, invoice_number, user_id in history:
            history_list.append({
                'old_quantity': old_qty,
                'new_quantity': new_qty,
                'change_date': change_date.isoformat() if isinstance(change_date, datetime) else str(change_date),
                'name': name,
                'invoice_number': invoice_number,
                'user_id': user_id
            })
        return jsonify(history_list)

    @app.route('/create-tables', methods=['POST'])
    def create_db_tables():
        try:
            db.create_tables()
            return jsonify({'success': 'Tables created'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/stock', methods=['GET'])
    @login_required
    def get_stock_data(user):
        try:
            stock_data = db.get_stock_data() # Assuming this function exists in db.py
            # Convert list of tuples to list of dicts for JSON
            stock_list = []
            for name, category, quantity in stock_data:
                stock_list.append({
                    'name': name,
                    'category': category,
                    'quantity': quantity
                })
            return jsonify(stock_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        if user_manager.create_user(username, password, role):
            print(f"Attempted to create user '{username}': Success.") # Debug print
            return jsonify({"message": "User created successfully"}), 201
        else:
            print(f"Attempted to create user '{username}': Failed (Username already exists or other error).") # Debug print
            return jsonify({"error": "Username already exists"}), 400

    @app.route('/debug/users', methods=['GET'])
    def debug_users():
        try:
            # Use the PostgreSQL connection to fetch users
            users = db.get_all_users() # Assuming this function exists in db.py
            print(f"API: Found {len(users)} users for /debug/users endpoint.") # Debug print
            user_list = []
            for user_id, username, role in users:
                user_list.append({'id': user_id, 'username': username, 'role': role})
            return jsonify(user_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/users/<int:user_id>', methods=['GET'])
    @login_required
    def get_user_by_id(user_id, user):
        # Only allow admin or the user themselves to view their details
        if user['role'] != 'admin' and user['id'] != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        try:
            user_data = db.get_user_by_id(user_id)
            if user_data:
                return jsonify({
                    'id': user_data[0],
                    'username': user_data[1],
                    'role': user_data[2]
                })
            return jsonify({"error": "User not found"}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/users/<int:user_id>', methods=['DELETE'])
    @login_required
    def delete_user(user_id, user):
        # Only allow admin to delete users
        if user['role'] != 'admin':
            return jsonify({"error": "Unauthorized"}), 403

        try:
            deleted_count = db.delete_user(user_id)
            if deleted_count > 0:
                return jsonify({'success': f'User with ID {user_id} deleted'}), 200
            else:
                return jsonify({'error': f'User with ID {user_id} not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app 