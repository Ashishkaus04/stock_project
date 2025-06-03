import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from datetime import datetime

# Define the base URL for your Flask API (placeholder - replace with your Render service URL)
API_BASE_URL = "http://127.0.0.1:5000" # Replace with your Render service URL later

def populate_tree(tree, search_term=None, auth_token=None):
    """Populates the treeview with products, optionally filtered by search_term."""
    for row in tree.get_children():
        tree.delete(row)
    
    try:
        # Construct the API URL, adding search query parameter if search_term is provided
        url = f"{API_BASE_URL}/products"
        if search_term:
            url += f"?search={requests.utils.quote(search_term)}"

        # Add authorization header
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        # Make GET request to the API
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        products = response.json()
        
        for product in products:
            # The API returns product details as a dictionary
            item_id = product['id']
            name = product['name']
            category = product['category']
            quantity = product['quantity']
            min_stock = product['min_stock']
            
            # Format the row to show N/A for None values
            formatted_row = [
                str(item_id) if item_id is not None else "N/A",
                name if name is not None else "N/A",
                category if category is not None else "N/A",
                str(quantity) if quantity is not None else "N/A",
                str(min_stock) if min_stock is not None else "N/A"
            ]
            
            item = tree.insert("", "end", values=formatted_row)
            
            # If quantity is below min_stock, tag the item
            # Ensure quantity and min_stock are treated as numbers for comparison
            try:
                quantity_num = int(quantity) if quantity != "N/A" else 0
                min_stock_num = int(min_stock) if min_stock != "N/A" else 0
                if quantity_num < min_stock_num:
                    tree.item(item, tags=('low_stock',))
            except ValueError:
                 # Handle cases where quantity or min_stock might not be valid numbers
                 pass

    except requests.exceptions.RequestException as e:
        messagebox.showerror("API Error", f"Failed to fetch products: {e}")

def add_product_window(root, tree=None, auth_token=None):
    win = tk.Toplevel(root)
    win.title("Add Product")

    fields = ["Name", "Category", "Quantity", "Min Stock"]
    entries = {}

    for i, field in enumerate(fields):
        tk.Label(win, text=field).grid(row=i, column=0, padx=5, pady=5)
        entry = tk.Entry(win)
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries[field.lower().replace(" ", "_")] = entry

    def save():
        try:
            data = {k: v.get() for k, v in entries.items()}
            
            # Prepare data for API request
            product_data = {
                "name": data.get("name"),
                "category": data.get("category"),
                "quantity": int(data.get("quantity", 0)),
                "min_stock": int(data.get("min_stock", 0))
            }

            # Add authorization header
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            # Make POST request to the API to add product
            response = requests.post(f"{API_BASE_URL}/product", json=product_data, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes
            
            # Handle success response
            messagebox.showinfo("Success", "Product added successfully!")
            win.destroy()
            if tree:
                populate_tree(tree, auth_token=auth_token)

        except ValueError:
             messagebox.showerror("Error", "Please enter valid numbers for Quantity and Min Stock.")
        except requests.exceptions.RequestException as e:
            # Attempt to parse API error message if available
            error_message = str(e)
            if response and response.content:
                try:
                    api_error = response.json()
                    if 'error' in api_error:
                        error_message = api_error['error']
                except:
                    pass # Ignore if JSON parsing fails
            messagebox.showerror("API Error", f"Failed to add product: {error_message}")

    tk.Button(win, text="Save", command=save).grid(row=len(fields), column=0, columnspan=2, pady=10)

def show_in_stock(root, main_tree=None, auth_token=None):
    win = tk.Toplevel(root)
    win.title("In-Stock Items")

    columns = ("ID", "Name", "Quantity")
    tree = ttk.Treeview(win, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Configure the tag for low stock items
    tree.tag_configure('low_stock', foreground='red')

    def populate_in_stock():
        for row in tree.get_children():
            tree.delete(row)
        try:
            # Add authorization header
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            response = requests.get(f"{API_BASE_URL}/products", headers=headers)
            response.raise_for_status()
            products = response.json()

            for product in products:
                item_id = product['id']
                name = product['name']
                quantity = product['quantity']
                min_stock = product['min_stock']

                item = tree.insert("", "end", values=(item_id, name, quantity))
                if min_stock is not None and quantity < min_stock:
                    tree.item(item, tags=('low_stock',))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to fetch products: {e}")

    def add_new_item():
        add_product_window(win, tree=tree, auth_token=auth_token)

    def update_quantity():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
            
        item = tree.item(selected[0])['values']
        item_id = int(item[0]) # Ensure item_id is integer
        item_name = item[1]
        current_qty = int(item[2]) # Ensure current_qty is integer

        # Get all product details from API (to get min_stock for preview)
        try:
            # Add authorization header
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            response = requests.get(f"{API_BASE_URL}/product/{item_id}", headers=headers)
            response.raise_for_status()
            product_details = response.json()
            min_stock = product_details.get('min_stock', 0)
            current_qty_from_api = product_details.get('quantity', 0)

            # Use the quantity from API in case the local tree view is outdated
            current_qty = current_qty_from_api

        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to fetch product details for update: {e}")
            return

        update_win = tk.Toplevel(win)
        update_win.title(f"Update Product - {item_name}")
        update_win.geometry("400x500")  # Increased height for new fields
        update_win.resizable(False, False)

        # Center the window
        update_win.transient(win)
        update_win.grab_set()

        # Create a frame for better organization
        frame = tk.Frame(update_win, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        # Product details section
        details_frame = tk.LabelFrame(frame, text="Product Details", padx=10, pady=10)
        details_frame.pack(fill="x", pady=(0, 15))

        # Name
        name_frame = tk.Frame(details_frame)
        name_frame.pack(fill="x", pady=2)
        tk.Label(name_frame, text="Name:", width=10, anchor="w").pack(side="left")
        tk.Label(name_frame, text=product_details.get('name', 'N/A'), font=("Arial", 9, "bold")).pack(side="left")

        # Category
        cat_frame = tk.Frame(details_frame)
        cat_frame.pack(fill="x", pady=2)
        tk.Label(cat_frame, text="Category:", width=10, anchor="w").pack(side="left")
        tk.Label(cat_frame, text=product_details.get('category', 'N/A')).pack(side="left")

        # Min Stock
        min_frame = tk.Frame(details_frame)
        min_frame.pack(fill="x", pady=2)
        tk.Label(min_frame, text="Min Stock:", width=10, anchor="w").pack(side="left")
        tk.Label(min_frame, text=product_details.get('min_stock', 'N/A')).pack(side="left")

        # Current Quantity
        curr_frame = tk.Frame(details_frame)
        curr_frame.pack(fill="x", pady=2)
        tk.Label(curr_frame, text="Current Qty:", width=10, anchor="w").pack(side="left")
        tk.Label(curr_frame, text=str(current_qty), font=("Arial", 9, "bold")).pack(side="left")

        # Quantity update section
        update_frame = tk.LabelFrame(frame, text="Update Quantity", padx=10, pady=10)
        update_frame.pack(fill="x", pady=(0, 15))

        qty_frame = tk.Frame(update_frame)
        qty_frame.pack(fill="x", pady=5)

        tk.Label(qty_frame, text="Quantity to Add:").pack(side="left", padx=(0, 5))
        qty_entry = tk.Entry(qty_frame, width=10)
        qty_entry.insert(0, "0")
        qty_entry.pack(side="left")
        qty_entry.focus_set()
        qty_entry.select_range(0, tk.END)

        # Seller Information section
        seller_frame = tk.LabelFrame(frame, text="Seller Information", padx=10, pady=10)
        seller_frame.pack(fill="x", pady=(0, 15))

        # Seller Name
        seller_name_frame = tk.Frame(seller_frame)
        seller_name_frame.pack(fill="x", pady=2)
        tk.Label(seller_name_frame, text="Name:", width=10, anchor="w").pack(side="left")
        seller_name_entry = tk.Entry(seller_name_frame)
        seller_name_entry.pack(side="left", fill="x", expand=True)

        # Invoice Number
        invoice_frame = tk.Frame(seller_frame)
        invoice_frame.pack(fill="x", pady=2)
        tk.Label(invoice_frame, text="Invoice:", width=10, anchor="w").pack(side="left")
        invoice_entry = tk.Entry(invoice_frame)
        invoice_entry.pack(side="left", fill="x", expand=True)

        # Preview section
        preview_frame = tk.LabelFrame(frame, text="Preview", padx=10, pady=10)
        preview_frame.pack(fill="x", pady=(0, 15))

        preview_label = tk.Label(preview_frame, text=f"New Total: {current_qty}")
        preview_label.pack(pady=5)

        def update_preview(*args):
            try:
                add_qty = int(qty_entry.get())
                new_total = current_qty + add_qty
                preview_label.config(text=f"New Total: {new_total}")

                # Add warning if below min stock
                try:
                    min_stock_num = int(min_stock) if min_stock != "N/A" else 0
                    if new_total < min_stock_num:
                         preview_label.config(fg="red")
                    else:
                         preview_label.config(fg="black")
                except ValueError:
                    pass # Ignore if min_stock is not a valid number
            except ValueError:
                preview_label.config(text="New Total: Invalid", fg="red")

        # Bind the entry to update preview
        qty_entry.bind('<KeyRelease>', update_preview)

        def validate_and_save():
            try:
                add_qty = int(qty_entry.get())
                new_qty = current_qty + add_qty
                if new_qty < 0:
                    messagebox.showerror("Error", "Final quantity cannot be negative")
                    return

                # Get seller information
                seller_name = seller_name_entry.get().strip()
                invoice_number = invoice_entry.get().strip()

                # Prepare data for API request
                update_data = {
                    "new_quantity": new_qty,
                    "seller_name": seller_name if seller_name else None,
                    "invoice_number": invoice_number if invoice_number else None
                }

                # Add authorization header
                headers = {}
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"

                # Make PUT request to the API to update quantity
                response = requests.put(f"{API_BASE_URL}/product/{item_id}/quantity", json=update_data, headers=headers)
                response.raise_for_status() # Raise an exception for bad status codes

                # Handle success response
                messagebox.showinfo("Success", f"Quantity updated to {new_qty}")
                update_win.destroy()

                # Refresh the treeview after update
                if main_tree:
                    populate_tree(main_tree, auth_token=auth_token)

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except requests.exceptions.RequestException as e:
                 # Attempt to parse API error message if available
                error_message = str(e)
                if response and response.content:
                    try:
                        api_error = response.json()
                        if 'error' in api_error:
                            error_message = api_error['error']
                    except:
                        pass # Ignore if JSON parsing fails
                messagebox.showerror("API Error", f"Failed to update quantity: {error_message}")

        # Bind Enter key to save
        update_win.bind('<Return>', lambda event=None: validate_and_save())

        # Button frame
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=(10, 0))

        tk.Button(btn_frame, text="Save", command=validate_and_save, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=update_win.destroy, width=10).pack(side="left", padx=5)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Add Item", command=add_new_item).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Update Quantity", command=update_quantity).pack(side="left", padx=5)

    populate_in_stock()

def show_out_of_stock(root, main_tree=None, auth_token=None):
    win = tk.Toplevel(root)
    win.title("Out of Stock Management")
    win.geometry("600x400")

    columns = ("ID", "Name", "Category", "Quantity", "Min Stock")
    tree = ttk.Treeview(win, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Configure the tag for low stock items
    tree.tag_configure('low_stock', foreground='red')

    def populate_out_of_stock():
        # This view should only show items that are out of stock (quantity <= 0)
        for row in tree.get_children():
            tree.delete(row)

        try:
            # Add authorization header
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            # Fetch ALL products from API and filter locally
            # Alternatively, could add an API endpoint for out of stock items
            response = requests.get(f"{API_BASE_URL}/products", headers=headers)
            response.raise_for_status()
            products = response.json()

            # out_of_stock_products = [p for p in products if p.get('quantity', 0) <= 0]
            all_products = products

            for product in all_products:
                item_id = product['id']
                name = product['name']
                category = product['category']
                quantity = product['quantity']
                min_stock = product['min_stock']

                # Format the row to show N/A for None values
                formatted_row = [
                    str(item_id) if item_id is not None else "N/A",
                    name if name is not None else "N/A",
                    category if category is not None else "N/A",
                    str(quantity) if quantity is not None else "N/A",
                    str(min_stock) if min_stock is not None else "N/A"
                ]

                item = tree.insert("", "end", values=formatted_row)

                # If quantity is below min_stock, tag the item (should all be low stock if out of stock)
                try:
                     quantity_num = int(quantity) if quantity != "N/A" else 0
                     min_stock_num = int(min_stock) if min_stock != "N/A" else 0
                     if quantity_num < min_stock_num:
                         tree.item(item, tags=('low_stock',))
                except ValueError:
                    pass # Ignore if quantity or min_stock is not a valid number

        except requests.exceptions.RequestException as e:
             messagebox.showerror("API Error", f"Failed to fetch products for out of stock view: {e}")

    def remove_stock():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to remove stock")
            return
            
        item = tree.item(selected[0])['values']
        item_id = int(item[0]) # Ensure item_id is integer
        item_name = item[1]
        current_qty = int(item[3]) # Ensure current_qty is integer

        # Get all product details from API (to get current qty for preview)
        try:
            # Add authorization header
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            response = requests.get(f"{API_BASE_URL}/product/{item_id}", headers=headers)
            response.raise_for_status()
            product_details = response.json()
            current_qty_from_api = product_details.get('quantity', 0)

            # Use the quantity from API in case the local tree view is outdated
            current_qty = current_qty_from_api

        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to fetch product details for removal: {e}")
            return

        remove_win = tk.Toplevel(win)
        remove_win.title(f"Remove Stock - {item_name}")
        remove_win.geometry("400x500")  # Increased height for buyer information
        remove_win.resizable(False, False)

        # Center the window
        remove_win.transient(win)
        remove_win.grab_set()

        frame = tk.Frame(remove_win, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        # Current stock info
        info_frame = tk.LabelFrame(frame, text="Current Stock", padx=10, pady=10)
        info_frame.pack(fill="x", pady=(0, 15))

        tk.Label(info_frame, text=f"Current Quantity: {current_qty}").pack(pady=5)

        # Quantity to remove
        qty_frame = tk.Frame(frame)
        qty_frame.pack(fill="x", pady=5)
        
        tk.Label(qty_frame, text="Quantity to Remove:").pack(side="left", padx=(0, 5))
        qty_entry = tk.Entry(qty_frame, width=10)
        qty_entry.insert(0, "0")
        qty_entry.pack(side="left")
        qty_entry.focus_set()
        qty_entry.select_range(0, tk.END)

        # Buyer Information section
        buyer_frame = tk.LabelFrame(frame, text="Buyer Information", padx=10, pady=10)
        buyer_frame.pack(fill="x", pady=(0, 15))

        # Buyer Name
        buyer_name_frame = tk.Frame(buyer_frame)
        buyer_name_frame.pack(fill="x", pady=2)
        tk.Label(buyer_name_frame, text="Name:", width=10, anchor="w").pack(side="left")
        buyer_name_entry = tk.Entry(buyer_name_frame)
        buyer_name_entry.pack(side="left", fill="x", expand=True)

        # Invoice Number
        invoice_frame = tk.Frame(buyer_frame)
        invoice_frame.pack(fill="x", pady=2)
        tk.Label(invoice_frame, text="Invoice:", width=10, anchor="w").pack(side="left")
        invoice_entry = tk.Entry(invoice_frame)
        invoice_entry.pack(side="left", fill="x", expand=True)

        # Preview
        preview_label = tk.Label(frame, text=f"Remaining: {current_qty}")
        preview_label.pack(pady=10)

        def update_preview(*args):
            try:
                remove_qty = int(qty_entry.get())
                remaining = current_qty - remove_qty
                preview_label.config(text=f"Remaining: {remaining}")
                if remaining < 0:
                    preview_label.config(fg="red")
                else:
                    preview_label.config(fg="black")
            except ValueError:
                preview_label.config(text="Remaining: Invalid", fg="red")

        qty_entry.bind('<KeyRelease>', update_preview)

        def save_removal():
            try:
                remove_qty = int(qty_entry.get())
                if remove_qty < 0:
                    messagebox.showerror("Error", "Cannot remove negative quantity")
                    return
                    
                new_qty = current_qty - remove_qty
                if new_qty < 0:
                    messagebox.showerror("Error", "Cannot remove more than available stock")
                    return

                # Get buyer information
                buyer_name = buyer_name_entry.get().strip()
                invoice_number = invoice_entry.get().strip()

                # Prepare data for API request (new quantity will be current - removed)
                update_data = {
                    "new_quantity": new_qty,
                    "seller_name": buyer_name if buyer_name else None, # Using seller_name field for buyer
                    "invoice_number": invoice_number if invoice_number else None
                }

                # Add authorization header
                headers = {}
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"

                # Make PUT request to the API to update quantity
                response = requests.put(f"{API_BASE_URL}/product/{item_id}/quantity", json=update_data, headers=headers)
                response.raise_for_status() # Raise an exception for bad status codes

                messagebox.showinfo("Success", f"Removed {remove_qty} items. New quantity: {new_qty}")
                remove_win.destroy()
                
                # Refresh the treeview after removal
                if main_tree:
                    populate_tree(main_tree, auth_token=auth_token)

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except requests.exceptions.RequestException as e:
                # Attempt to parse API error message if available
                error_message = str(e)
                if response and response.content:
                    try:
                        api_error = response.json()
                        if 'error' in api_error:
                            error_message = api_error['error']
                    except:
                        pass # Ignore if JSON parsing fails
                messagebox.showerror("API Error", f"Failed to remove stock: {error_message}")

        def on_enter(event):
            save_removal()

        qty_entry.bind('<Return>', on_enter)

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=(10, 0))
        
        tk.Button(btn_frame, text="Remove", command=save_removal, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=remove_win.destroy, width=10).pack(side="left", padx=5)

    def delete_item():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
            
        item = tree.item(selected[0])['values']
        item_id = int(item[0]) # Ensure item_id is integer
        item_name = item[1]

        if not messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete '{item_name}'?\nThis action cannot be undone."):
            return

        try:
            # Add authorization header
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            # Make DELETE request to the API to delete the product
            response = requests.delete(f"{API_BASE_URL}/product/{item_id}", headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes
            
            messagebox.showinfo("Success", f"Item '{item_name}' has been deleted")
            
            # Refresh the treeview after deletion
            if main_tree:
                populate_tree(main_tree, auth_token=auth_token)

        except requests.exceptions.RequestException as e:
            # Attempt to parse API error message if available
            error_message = str(e)
            if response and response.content:
                try:
                    api_error = response.json()
                    if 'error' in api_error:
                        error_message = api_error['error']
                except:
                    pass # Ignore if JSON parsing fails
            messagebox.showerror("API Error", f"Failed to delete item: {error_message}")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Remove Stock", command=remove_stock).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete Item", command=delete_item).pack(side="left", padx=5)

    # Initial population
    populate_out_of_stock()

def show_quantity_history(root, item_id, item_name, auth_token=None):
    win = tk.Toplevel(root)
    win.title(f"Quantity History - {item_name}")
    win.geometry("800x400")  # Increased width to accommodate new columns
    win.resizable(False, False)

    # Center the window
    win.transient(root)
    win.grab_set()

    # Create main frame
    frame = tk.Frame(win, padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    # Product info section
    info_frame = tk.LabelFrame(frame, text="Product Information", padx=10, pady=10)
    info_frame.pack(fill="x", pady=(0, 15))

    # Get current product details from API
    try:
        # Add authorization header
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        response = requests.get(f"{API_BASE_URL}/product/{item_id}", headers=headers)
        response.raise_for_status()
        product = response.json()

        # Name
        name_frame = tk.Frame(info_frame)
        name_frame.pack(fill="x", pady=2)
        tk.Label(name_frame, text="Name:", width=10, anchor="w").pack(side="left")
        tk.Label(name_frame, text=product.get('name', 'N/A'), font=("Arial", 9, "bold")).pack(side="left")

        # Category
        cat_frame = tk.Frame(info_frame)
        cat_frame.pack(fill="x", pady=2)
        tk.Label(cat_frame, text="Category:", width=10, anchor="w").pack(side="left")
        tk.Label(cat_frame, text=product.get('category', 'N/A')).pack(side="left")

        # Current Quantity
        curr_frame = tk.Frame(info_frame)
        curr_frame.pack(fill="x", pady=2)
        tk.Label(curr_frame, text="Current Qty:", width=10, anchor="w").pack(side="left")
        tk.Label(curr_frame, text=str(product.get('quantity', 'N/A')), font=("Arial", 9, "bold")).pack(side="left")

        # Min Stock
        min_frame = tk.Frame(info_frame)
        min_frame.pack(fill="x", pady=2)
        tk.Label(min_frame, text="Min Stock:", width=10, anchor="w").pack(side="left")
        tk.Label(min_frame, text=product.get('min_stock', 'N/A')).pack(side="left")

        # Created Date
        created_frame = tk.Frame(info_frame)
        created_frame.pack(fill="x", pady=2)
        tk.Label(created_frame, text="Created:", width=10, anchor="w").pack(side="left")
        created_date_str = product.get('created_date', 'N/A')
        tk.Label(created_frame, text=created_date_str).pack(side="left")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("API Error", f"Failed to fetch product details: {e}")
        win.destroy()
        return

    # History section
    history_frame = tk.LabelFrame(frame, text="Quantity History", padx=10, pady=10)
    history_frame.pack(fill="both", expand=True)

    # Create Treeview for history with seller information
    history_columns = ("Date", "Old Quantity", "New Quantity", "Change", "Name", "Invoice")
    history_tree = ttk.Treeview(history_frame, columns=history_columns, show="headings", height=10)

    # Configure column widths
    column_widths = {
        "Date": 150,
        "Old Quantity": 100,
        "New Quantity": 100,
        "Change": 80,
        "Name": 120,
        "Invoice": 100
    }

    for col in history_columns:
        history_tree.heading(col, text=col)
        history_tree.column(col, width=column_widths.get(col, 100))

    history_tree.pack(fill="both", expand=True)

    # Add scrollbar to history tree
    history_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=history_tree.yview)
    history_scroll.pack(side="right", fill="y")
    history_tree.configure(yscrollcommand=history_scroll.set)

    # Populate history from API
    try:
        # Add authorization header
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        response = requests.get(f"{API_BASE_URL}/product/{item_id}/history", headers=headers)
        response.raise_for_status()
        history = response.json()

        for record in history:
            old_qty = record.get('old_quantity', 'N/A')
            new_qty = record.get('new_quantity', 'N/A')
            change_date_str = record.get('change_date', 'N/A')
            name = record.get('name', 'N/A')
            invoice_number = record.get('invoice_number', 'N/A')

            change = "N/A"
            try:
                old_num = int(old_qty) if old_qty != "N/A" else 0
                new_num = int(new_qty) if new_qty != "N/A" else 0
                change = new_num - old_num
                change_text = f"{'+' if change > 0 else ''}{change}"
            except ValueError:
                change_text = "N/A"

            history_tree.insert("", "end", values=(
                change_date_str,
                old_qty,
                new_qty,
                change_text,
                name,
                invoice_number
            ))

    except requests.exceptions.RequestException as e:
        messagebox.showerror("API Error", f"Failed to fetch history: {e}")

    # Only show the Close button
    button_frame = tk.Frame(frame)
    button_frame.pack(side="bottom", fill="x", pady=(10, 0))
    close_btn = tk.Button(button_frame, text="Close", command=win.destroy, width=10)
    close_btn.pack(side="left", padx=5)
