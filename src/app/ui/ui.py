import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# Import from local packages
from ..database import db

def populate_tree(tree, search_term=None):
    """Populates the treeview with products, optionally filtered by search_term."""
    # Clear existing items
    for row in tree.get_children():
        tree.delete(row)

    try:
        # Directly use database function to get products
        products = db.get_all_products(search_term)
        for product in products:
            product_id, name, category, quantity, min_stock, last_changed_by_user_id = product
            tags = () # Initialize tags as an empty tuple
            if quantity <= min_stock:
                tags = ('low_stock',)
            tree.insert("", "end", values=product, tags=tags)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch products: {e}")

def show_in_stock(root, main_tree=None):
    # Directly use database function to get all products
    products = db.get_all_products()
    
    # Show all products in a new window
    win = tk.Toplevel(root)
    win.title("In-Stock Products")
    win.geometry("600x400")

    # --- Search Bar ---
    search_frame = ttk.Frame(win, padding="5")
    search_frame.pack(fill="x")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=(0, 5))
    def do_search(event=None):
        term = search_var.get().strip().lower()
        if term:
            # When searching, filter by name or category
            filtered = [p for p in db.get_all_products() if term in str(p[1]).lower() or term in str(p[2]).lower()]
        else:
            # When no search term, show all products
            filtered = db.get_all_products()
        tree.delete(*tree.get_children())
        for product in filtered:
            tree.insert("", "end", values=product)
    search_button = ttk.Button(search_frame, text="Search", command=do_search)
    search_button.pack(side="left")
    search_entry.bind('<Return>', do_search)

    tree = ttk.Treeview(win, columns=("ID", "Name", "Category", "Quantity", "Min Stock"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True)
    
    for product in products:
        tree.insert("", "end", values=product)

    # Add buttons for Add Item and Update Quantity
    btn_frame = ttk.Frame(win, padding="10")
    btn_frame.pack(fill="x", pady=(5, 0))

    def refresh_in_stock_tree():
        for row in tree.get_children():
            tree.delete(row)
        products = db.get_all_products()
        for product in products:
            tree.insert("", "end", values=product)
        if main_tree: # Also refresh the main window tree if available
            populate_tree(main_tree)

    ttk.Button(btn_frame, text="Add Item", command=lambda: add_product_window(win, refresh_in_stock_tree)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Update Quantity", command=lambda: on_update_quantity_clicked(win, tree, refresh_in_stock_tree)).pack(side="left", padx=5)

    def on_update_quantity_clicked(root_window, current_tree, refresh_callback):
        selected_item = current_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a product to update quantity.")
            return
        
        item_values = current_tree.item(selected_item[0])['values']
        product_id = item_values[0]
        current_quantity = item_values[3]
        
        # In a real application, you would pass the current user's ID here
        # For now, we'll pass None or a placeholder
        current_user_id = 1  # Placeholder, replace with actual logged-in user ID

        update_quantity_window(root_window, product_id, current_quantity, refresh_callback, current_user_id)

def show_out_of_stock(root, main_tree=None):
    # Directly use database function to get ALL products
    products = db.get_all_products()
    
    # Show all products in a new window, but keep the title as 'Out of Stock Products'
    win = tk.Toplevel(root)
    win.title("Out of Stock Products") # Keep this title as requested
    win.geometry("600x400")

    # --- Search Bar ---
    search_frame = ttk.Frame(win, padding="5")
    search_frame.pack(fill="x")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=(0, 5))
    def do_search(event=None):
        term = search_var.get().strip().lower()
        filtered = [p for p in db.get_all_products() if term in str(p[1]).lower() or term in str(p[2]).lower()] if term else db.get_all_products()
        tree.delete(*tree.get_children())
        for product in filtered:
            tree.insert("", "end", values=product)
    search_button = ttk.Button(search_frame, text="Search", command=do_search)
    search_button.pack(side="left")
    search_entry.bind('<Return>', do_search)

    tree = ttk.Treeview(win, columns=("ID", "Name", "Category", "Quantity", "Min Stock"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill="both", expand=True)
    
    for product in products: # Iterate through all products now
        tree.insert("", "end", values=product)

    # Add buttons for Delete Item and Remove Stock
    btn_frame = ttk.Frame(win, padding="10")
    btn_frame.pack(fill="x", pady=(5, 0))

    def refresh_out_of_stock_tree():
        for row in tree.get_children():
            tree.delete(row)
        products_to_display = db.get_all_products() # Get all products for refresh
        for product in products_to_display:
            tree.insert("", "end", values=product)
        if main_tree: # Also refresh the main window tree if available
            populate_tree(main_tree)

    def on_delete_item_clicked(root_window, current_tree, refresh_callback):
        selected_item = current_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a product to delete.")
            return
        
        item_values = current_tree.item(selected_item[0])['values']
        product_id = item_values[0]
        product_name = item_values[1]
        
        remove_product_window(root_window, product_id, product_name, refresh_callback)

    def on_remove_stock_clicked(root_window, current_tree, refresh_callback, current_user_id):
        selected_item = current_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a product to remove stock from.")
            return
        
        item_values = current_tree.item(selected_item[0])['values']
        product_id = item_values[0]
        product_name = item_values[1]
        current_quantity = item_values[3]
        
        remove_stock_window(root_window, product_id, product_name, current_quantity, refresh_callback, current_user_id)

    ttk.Button(btn_frame, text="Delete Item", command=lambda: on_delete_item_clicked(win, tree, refresh_out_of_stock_tree)).pack(side="left", padx=5)
    # Placeholder for current_user_id, replace with actual logged-in user ID
    ttk.Button(btn_frame, text="Remove Stock", command=lambda: on_remove_stock_clicked(win, tree, refresh_out_of_stock_tree, 1)).pack(side="left", padx=5)

def show_quantity_history(root, item_id, item_name):
    # Directly use database function to get history
    history = db.get_quantity_history(item_id)
    
    # Show history in a new window
    win = tk.Toplevel(root)
    win.title(f"Quantity History - {item_name}")
    win.geometry("800x400")
    
    tree = ttk.Treeview(win, columns=("Date", "Old Quantity", "New Quantity", "Seller/Buyer", "Invoice", "Changed By"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(fill="both", expand=True)
    
    for old_qty, new_qty, change_date, name, invoice_number, user_id, username in history:
        tree.insert("", "end", values=(change_date, old_qty, new_qty, name, invoice_number, username))

def add_user_window(root):
    win = tk.Toplevel(root)
    win.title("Add User")
    win.geometry("300x200")
    
    frame = ttk.Frame(win, padding="20")
    frame.pack(fill="both", expand=True)
    
    ttk.Label(frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
    username_entry = ttk.Entry(frame)
    username_entry.grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
    password_entry = ttk.Entry(frame, show="*")
    password_entry.grid(row=1, column=1, padx=5, pady=5)
    
    def save_user():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return
        
        try:
            # Directly use database function to add user
            if db.add_user_to_db(username, password, "user"):
                messagebox.showinfo("Success", "User created successfully!")
                win.destroy()
            else:
                messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {e}")
    
    tk.Button(frame, text="Create User", command=save_user).grid(row=2, column=0, columnspan=2, pady=10)
    
    # Allow pressing Enter to save
    win.bind('<Return>', lambda event=None: save_user())
    
    frame.columnconfigure(1, weight=1) # Allow username/password entries to expand

def add_product_window(root, refresh_tree_callback=None, current_user_id=None):
    """Opens a new window to add a new product."""
    win = tk.Toplevel(root)
    win.title("Add New Product")
    win.geometry("400x300")

    frame = ttk.Frame(win, padding="20")
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
    name_entry = ttk.Entry(frame)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
    category_entry = ttk.Entry(frame)
    category_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Quantity:").grid(row=2, column=0, padx=5, pady=5)
    quantity_entry = ttk.Entry(frame)
    quantity_entry.grid(row=2, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Min Stock:").grid(row=3, column=0, padx=5, pady=5)
    min_stock_entry = ttk.Entry(frame)
    min_stock_entry.grid(row=3, column=1, padx=5, pady=5)

    def save_product():
        name = name_entry.get().strip()
        category = category_entry.get().strip()
        quantity_str = quantity_entry.get().strip()
        min_stock_str = min_stock_entry.get().strip()

        if not name or not quantity_str or not min_stock_str:
            messagebox.showwarning("Input Error", "Name, Quantity, and Min Stock are required.")
            return

        try:
            quantity = int(quantity_str)
            min_stock = int(min_stock_str)

            if quantity < 0 or min_stock < 0:
                messagebox.showwarning("Input Error", "Quantity and Min Stock cannot be negative.")
                return

            # Pass current_user_id to add_product
            db.add_product(name, category, quantity, min_stock, current_user_id)
            messagebox.showinfo("Success", "Product added successfully!")
            win.destroy()
            if refresh_tree_callback:
                refresh_tree_callback()
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity and Min Stock must be valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add product: {e}")

    tk.Button(frame, text="Add Product", command=save_product).grid(row=4, column=0, columnspan=2, pady=10)
    frame.columnconfigure(1, weight=1)

def update_quantity_window(root, product_id, current_quantity, refresh_tree_callback=None, current_user_id=None):
    """Opens a new window to update the quantity of an existing product."""
    win = tk.Toplevel(root)
    win.title(f"Update Quantity for Product ID: {product_id}")
    win.geometry("400x250")

    frame = ttk.Frame(win, padding="20")
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"Current Quantity: {current_quantity}").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

    ttk.Label(frame, text="New Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    new_quantity_entry = ttk.Entry(frame)
    new_quantity_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame, text="Seller/Buyer Name (Optional):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    seller_buyer_entry = ttk.Entry(frame)
    seller_buyer_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame, text="Invoice Number (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    invoice_number_entry = ttk.Entry(frame)
    invoice_number_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    def save_quantity():
        new_quantity_str = new_quantity_entry.get().strip()
        seller_name = seller_buyer_entry.get().strip()
        invoice_number = invoice_number_entry.get().strip()

        if not new_quantity_str:
            messagebox.showwarning("Input Error", "New Quantity is required.")
            return

        try:
            quantity_to_add = int(new_quantity_str)
            if quantity_to_add < 0: # Ensure only non-negative quantities can be added
                messagebox.showwarning("Input Error", "Quantity to add must be a non-negative number.")
                return

            final_quantity = current_quantity + quantity_to_add # Add to current quantity

            db.update_product_quantity(product_id, final_quantity, seller_name, invoice_number, current_user_id)
            messagebox.showinfo("Success", "Quantity updated successfully!")
            win.destroy()
            if refresh_tree_callback:
                refresh_tree_callback()
        except ValueError:
            messagebox.showwarning("Input Error", "New Quantity must be a valid number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update quantity: {e}")

    tk.Button(frame, text="Update Quantity", command=save_quantity).grid(row=4, column=0, columnspan=2, pady=10)
    frame.columnconfigure(1, weight=1)

def remove_product_window(root, product_id, product_name, refresh_tree_callback=None):
    """Opens a confirmation window to remove a product."""
    if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove {product_name} (ID: {product_id})?\nThis action cannot be undone."):
        try:
            db.delete_product(product_id)
            messagebox.showinfo("Success", f"{product_name} removed successfully!")
            if refresh_tree_callback:
                refresh_tree_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove product: {e}")

def remove_stock_window(root, product_id, product_name, current_quantity, refresh_tree_callback=None, current_user_id=None):
    """Opens a window to remove stock from a product (reduce quantity)."""
    win = tk.Toplevel(root)
    win.title(f"Remove Stock from {product_name} (ID: {product_id})")
    win.geometry("400x250")

    frame = ttk.Frame(win, padding="20")
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"Current Quantity: {current_quantity}").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

    ttk.Label(frame, text="Quantity to Remove:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    quantity_to_remove_entry = ttk.Entry(frame)
    quantity_to_remove_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame, text="Seller/Buyer Name (Optional):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    seller_buyer_entry = ttk.Entry(frame)
    seller_buyer_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame, text="Invoice Number (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    invoice_number_entry = ttk.Entry(frame)
    invoice_number_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    def save_removal():
        quantity_to_remove_str = quantity_to_remove_entry.get().strip()
        seller_name = seller_buyer_entry.get().strip()
        invoice_number = invoice_number_entry.get().strip()

        if not quantity_to_remove_str:
            messagebox.showwarning("Input Error", "Quantity to Remove is required.")
            return

        try:
            quantity_to_remove = int(quantity_to_remove_str)
            if quantity_to_remove <= 0:
                messagebox.showwarning("Input Error", "Quantity to Remove must be a positive number.")
                return
            
            new_quantity = current_quantity - quantity_to_remove
            if new_quantity < 0:
                messagebox.showwarning("Warning", f"Removing {quantity_to_remove} would result in a negative quantity ({new_quantity}). Setting to 0 instead.")
                new_quantity = 0

            db.update_product_quantity(product_id, new_quantity, seller_name, invoice_number, current_user_id)
            messagebox.showinfo("Success", "Stock removed successfully!")
            win.destroy()
            if refresh_tree_callback:
                refresh_tree_callback()
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity to Remove must be a valid number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove stock: {e}")

    tk.Button(frame, text="Remove Stock", command=save_removal).grid(row=4, column=0, columnspan=2, pady=10)
    frame.columnconfigure(1, weight=1)

def show_add_user_window(parent_root):
    add_user_win = tk.Toplevel(parent_root)
    add_user_win.title("Add New User")
    add_user_win.geometry("400x250")
    add_user_win.transient(parent_root)
    add_user_win.grab_set()

    tk.Label(add_user_win, text="Username:").pack(pady=5)
    username_entry = tk.Entry(add_user_win, width=30)
    username_entry.pack(pady=5)

    tk.Label(add_user_win, text="Password:").pack(pady=5)
    password_entry = tk.Entry(add_user_win, width=30, show="*")
    password_entry.pack(pady=5)

    def add_user_action():
        username = username_entry.get()
        password = password_entry.get()
        if username and password:
            try:
                db.add_user(username, password) # This function will be added in db.py
                messagebox.showinfo("Success", f"User {username} added successfully.")
                add_user_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add user: {e}")
        else:
            messagebox.showwarning("Input Error", "Username and password cannot be empty.")

    tk.Button(add_user_win, text="Add User", command=add_user_action).pack(pady=10)

def show_delete_user_window(parent_root):
    delete_user_win = tk.Toplevel(parent_root)
    delete_user_win.title("Delete User")
    delete_user_win.geometry("450x300") # Adjusted size for Treeview
    delete_user_win.transient(parent_root)
    delete_user_win.grab_set()

    # Treeview to display users
    users_tree = ttk.Treeview(delete_user_win, columns=("ID", "Username", "Role"), show="headings")
    users_tree.heading("ID", text="ID")
    users_tree.heading("Username", text="Username")
    users_tree.heading("Role", text="Role")
    users_tree.column("ID", width=50)
    users_tree.column("Username", width=150)
    users_tree.column("Role", width=100)
    users_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def populate_users_tree():
        for item in users_tree.get_children():
            users_tree.delete(item)
        try:
            users = db.get_all_users()
            for user_id, username, role in users: # Unpack tuple directly
                users_tree.insert("", "end", values=(user_id, username, role))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch users: {e}")
    
    populate_users_tree()

    def delete_user_action():
        selected_item = users_tree.selection()
        if selected_item:
            user_id = users_tree.item(selected_item[0])['values'][0] # Get ID from selected row
            username = users_tree.item(selected_item[0])['values'][1] # Get username for message
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete user {username} (ID: {user_id})?"):
                try:
                    db.delete_user(user_id)
                    messagebox.showinfo("Success", f"User {username} deleted successfully.")
                    populate_users_tree() # Refresh the list
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete user: {e}")
        else:
            messagebox.showwarning("Selection Error", "Please select a user to delete.")

    tk.Button(delete_user_win, text="Delete Selected User", command=delete_user_action).pack(pady=10)

def show_all_users_window(parent_root):
    all_users_win = tk.Toplevel(parent_root)
    all_users_win.title("Available Users")
    all_users_win.geometry("500x400")
    all_users_win.transient(parent_root)
    all_users_win.grab_set()

    users_tree = ttk.Treeview(all_users_win, columns=("ID", "Username", "Role"), show="headings")
    users_tree.heading("ID", text="ID")
    users_tree.heading("Username", text="Username")
    users_tree.heading("Role", text="Role")
    users_tree.column("ID", width=50)
    users_tree.column("Username", width=200)
    users_tree.column("Role", width=100)
    users_tree.pack(fill="both", expand=True, padx=10, pady=10)

    try:
        users = db.get_all_users()
        for user_id, username, role in users: # Unpack tuple directly, including role
            users_tree.insert("", "end", values=(user_id, username, role))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch users: {e}")

    tk.Button(all_users_win, text="Close", command=all_users_win.destroy).pack(pady=10)

def show_change_password_window(parent_root, current_user_id):
    change_pass_win = tk.Toplevel(parent_root)
    change_pass_win.title("Change Password")
    change_pass_win.geometry("400x250")
    change_pass_win.transient(parent_root)
    change_pass_win.grab_set()

    tk.Label(change_pass_win, text="Old Password:").pack(pady=5)
    old_password_entry = tk.Entry(change_pass_win, width=30, show="*")
    old_password_entry.pack(pady=5)

    tk.Label(change_pass_win, text="New Password:").pack(pady=5)
    new_password_entry = tk.Entry(change_pass_win, width=30, show="*")
    new_password_entry.pack(pady=5)

    tk.Label(change_pass_win, text="Confirm New Password:").pack(pady=5)
    confirm_new_password_entry = tk.Entry(change_pass_win, width=30, show="*")
    confirm_new_password_entry.pack(pady=5)

    def change_password_action():
        old_password = old_password_entry.get()
        new_password = new_password_entry.get()
        confirm_new_password = confirm_new_password_entry.get()

        if not old_password or not new_password or not confirm_new_password:
            messagebox.showwarning("Input Error", "All password fields are required.")
            return
        if new_password != confirm_new_password:
            messagebox.showwarning("Input Error", "New password and confirmation do not match.")
            return
        
        try:
            # Verify old password first
            user_data = db.get_user_by_id(current_user_id) # Need to fetch user data including password hash
            if user_data and db.check_password(old_password, user_data['password_hash']):
                db.update_user_password(current_user_id, new_password) # This function will be added in db.py
                messagebox.showinfo("Success", "Password changed successfully!")
                change_pass_win.destroy()
            else:
                messagebox.showerror("Error", "Incorrect old password.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change password: {e}")

    tk.Button(change_pass_win, text="Change Password", command=change_password_action).pack(pady=10)
