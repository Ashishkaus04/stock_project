from flask import Flask, request, jsonify
import db

app = Flask(__name__)

@app.route('/')
def index():
    return 'Stock Management API'

@app.route('/products', methods=['GET'])
def get_products():
    # Assuming db.get_all_products() exists or similar
    # For now, we'll need to add a function in db.py to get all products
    return jsonify([]) # Placeholder

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
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

@app.route('/product', methods=['POST'])
def add_product():
    data = request.json
    if not data or not 'name' in data or not 'quantity' in data:
        return jsonify({'error': 'Missing name or quantity'}), 400

    name = data.get('name')
    category = data.get('category')
    quantity = data.get('quantity')
    min_stock = data.get('min_stock')

    try:
        product_id = db.add_product(name, category, quantity, min_stock)
        return jsonify({'success': 'Product added', 'product_id': product_id}), 201
    except Exception as e:
         return jsonify({'error': str(e)}), 500

@app.route('/product/<int:product_id>/quantity', methods=['PUT'])
def update_product_qty(product_id):
    data = request.json
    if not data or not 'new_quantity' in data:
        return jsonify({'error': 'Missing new_quantity'}), 400

    new_quantity = data.get('new_quantity')
    seller_name = data.get('seller_name') # Will be buyer_name when removing
    invoice_number = data.get('invoice_number')

    try:
        db.update_product_quantity(product_id, new_quantity, seller_name, invoice_number)
        return jsonify({'success': 'Quantity updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/product/<int:product_id>/history', methods=['GET'])
def get_history(product_id):
    history = db.get_quantity_history(product_id)
    # Convert list of tuples to list of dicts
    history_list = []
    for old_qty, new_qty, change_date, name, invoice_number in history:
         history_list.append({
            'old_quantity': old_qty,
            'new_quantity': new_qty,
            'change_date': change_date.isoformat() if isinstance(change_date, datetime) else str(change_date),
            'name': name,
            'invoice_number': invoice_number
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
def get_stock_data():
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

if __name__ == '__main__':
    app.run(debug=True) 