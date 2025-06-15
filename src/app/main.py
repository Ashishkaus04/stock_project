import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from tkcalendar import DateEntry
import csv
import os
import json
import threading
import hashlib
from flask import Flask
from app.api.app import create_app
from waitress import serve

# Import from local packages
from .ui import ui
from .database import db

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define default font configuration
DEFAULT_FONT = ('Helvetica', 12)
HEADING_FONT = ('Helvetica', 12, 'bold')

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MVD Stock Manager - Login")
        self.root.geometry("300x200")
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Configure style
        style = ttk.Style()
        style.configure('TLabel', font=DEFAULT_FONT)
        style.configure('TEntry', font=DEFAULT_FONT)
        style.configure('TButton', font=DEFAULT_FONT)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Username
        ttk.Label(main_frame, text="Username:").pack(fill="x", pady=(0, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var)
        self.username_entry.pack(fill="x", pady=(0, 10))
        
        # Password
        ttk.Label(main_frame, text="Password:").pack(fill="x", pady=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*")
        self.password_entry.pack(fill="x", pady=(0, 20))
        
        # Login button
        self.login_button = ttk.Button(main_frame, text="Login", command=self.login)
        self.login_button.pack(fill="x")
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.login())
        
        # Store login result
        self.login_successful = False
        self.user_data = None
        
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        try:
            # Directly use database function to verify user
            user = db.get_user_by_credentials(username, password)
            if user:
                self.user_data = user
                self.login_successful = True
                self.root.destroy()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to database: {e}")
    
    def run(self):
        self.root.mainloop()
        return self.login_successful, self.user_data

def main():
    # Ensure database tables are created
    db.create_tables()

    # Debug: Print all quantity history records
    db.debug_get_all_history()

    # Ensure admin user exists (using db.add_user with bcrypt)
    if not db.get_user_by_username("admin"):
        db.add_user("admin", "admin123", role="admin")
        print("Admin user 'admin' created successfully.")
    else:
        print("Admin user 'admin' already exists.")

    # Show login window
    login_window = LoginWindow()
    login_successful, user_data = login_window.run()
    
    if not login_successful:
        return  # Exit if login failed
    
    # Debug: Remove after verifying fix
    print(f"DEBUG: User data after login: {user_data}")
    print(f"DEBUG: User ID after login: {user_data.get('id')}")

    # Create main application window
    root = tk.Tk()
    root.title(f"MVD Stock Manager - Welcome {user_data['username']}")
    root.geometry("800x400")

    # Create a style object and set clam theme
    style = ttk.Style()
    style.theme_use('clam')

    # Add user info and logout button
    user_frame = tk.Frame(root)
    user_frame.pack(fill="x", pady=(0, 0))
    
    ttk.Label(user_frame, text=f"Logged in as: {user_data['username']}", font=DEFAULT_FONT).pack(side="left", padx=5)
    
    # Frame for right-aligned buttons (Logout and Refresh)
    right_buttons_frame = tk.Frame(user_frame)
    right_buttons_frame.pack(side="right", padx=5)

    def logout():
        root.quit()
    
    ttk.Button(right_buttons_frame, text="Logout", command=logout, style='TButton').pack(side="top", pady=(0, 2)) # Small pady below logout
    ttk.Button(right_buttons_frame, text="Refresh", command=lambda: ui.populate_tree(tree), style='TButton').pack(side="top", pady=(2, 0)) # Small pady above refresh

    # --- Function Definitions (moved here to ensure user_data is available) ---

    def export_selected_to_csv():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one product to export.")
            return
        
        # Ask for date range first
        print("Attempting to create date range prompt...")
        prompt = tk.Toplevel(root)
        prompt.title("Select Date Range")
        prompt.geometry("300x150")
        prompt.transient(root)
        prompt.grab_set()
        
        ttk.Label(prompt, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        start_date_entry = DateEntry(prompt, width=12, background='darkblue', foreground='white', borderwidth=2)
        start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(prompt, text="End Date:").grid(row=1, column=0, padx=5, pady=5)
        end_date_entry = DateEntry(prompt, width=12, background='darkblue', foreground='white', borderwidth=2)
        end_date_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Function to handle what happens after OK is clicked on date prompt
        def on_date_range_ok():
            start_date_obj = start_date_entry.get_date()
            end_date_obj = end_date_entry.get_date()
            prompt.destroy()

            # Convert date objects to datetime objects to cover the full day
            start = datetime.combine(start_date_obj, datetime.min.time()) if start_date_obj else None
            end = datetime.combine(end_date_obj, datetime.max.time()) if end_date_obj else None

            # Now ask for file path after date range is selected
            suggested_name = f"export_{start.strftime('%Y-%m-%d')}_to_{end.strftime('%Y-%m-%d')}.csv"
            file_path = tk.filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=suggested_name
            )
            if not file_path:
                print("File save dialog cancelled or no file selected.")
                return
            
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Product Name", "Category", "Date", "Old Quantity", "New Quantity", "Seller/Buyer Name", "Invoice Number", "Changed By"])
                    
                    for sel in selected:
                        item = tree.item(sel)['values']
                        item_id = int(item[0])
                        print(f"Processing product ID: {item_id}")
                        
                        # Directly use database function to get history
                        history = db.get_quantity_history(item_id, start, end)
                        print(f"Retrieved {len(history)} history records for product ID {item_id} in date range {start} to {end}.")
                        for old_qty, new_qty, change_date, name, invoice_number, user_id, username in history:
                            writer.writerow([item[1], item[2], change_date, old_qty, new_qty, name, invoice_number, username])
                            print(f"Writing history record for product {item[1]}: {change_date}, {old_qty} -> {new_qty}")
                
                messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")
        
        tk.Button(prompt, text="OK", command=on_date_range_ok).grid(row=2, column=0, columnspan=2, pady=10)
        prompt.wait_window() # Make the prompt modal

    def print_stock():
        # Ask for file path
        suggested_name = f"stock_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=suggested_name
        )
        if not file_path:
            print("File save dialog cancelled or no file selected.")
            return

        try:
            # Directly use database function to get stock data
            stock_data = db.get_stock_data()

            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Product Name", "Category", "Quantity"])
                for row in stock_data:
                    writer.writerow([row[0], row[1], row[2]])

            tk.messagebox.showinfo("Success", f"Stock exported successfully to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch stock data: {e}")

    def show_add_product_window():
        ui.add_product_window(root, lambda: ui.populate_tree(tree, search_var.get()), int(user_data['id']))

    def show_update_quantity_window():
        selected_item = tree.selection()
        if selected_item:
            item = tree.item(selected[0])['values']
            item_id = item[0]
            item_name = item[1]
            ui.show_update_quantity_window(root, item_id, item_name, current_user_id=int(user_data['id'])) # Pass user_id

    # --- Menu Bar ---
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # Admin Menu
    admin_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Admin", menu=admin_menu)

    # Only show user management options for admin users
    if user_data['role'] == 'admin':
        admin_menu.add_command(label="Add User", command=lambda: ui.show_add_user_window(root))
        admin_menu.add_command(label="Delete User", command=lambda: ui.show_delete_user_window(root))
        admin_menu.add_command(label="Show Users", command=lambda: ui.show_all_users_window(root))
        admin_menu.add_separator()

    admin_menu.add_command(label="Change Password", command=lambda: ui.show_change_password_window(root, user_data['id']))

    # Stock Menu
    stock_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Stock", menu=stock_menu)
    stock_menu.add_command(label="In-Stock Products", command=lambda: ui.show_in_stock(root, tree))
    stock_menu.add_command(label="Out of Stock Products", command=lambda: ui.show_out_of_stock(root, tree))

    # Export Menu
    export_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Export", menu=export_menu)
    export_menu.add_command(label="Export to CSV", command=export_selected_to_csv)
    export_menu.add_command(label="Print Stock", command=print_stock)

    # --- Search Frame ---
    search_frame = tk.Frame(root)
    search_frame.pack(fill="x", pady=(0, 0))
    
    ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
    search_var = tk.StringVar()

    def update_suggestions(*args):
        search_term = search_var.get()
        if search_term:
            suggestions = db.get_all_products(search_term)
            search_combo['values'] = [product[1] for product in suggestions]
        else:
            search_combo['values'] = [] # Clear suggestions if search term is empty

    def perform_search(event=None):
        search_term = search_var.get()
        print(f"Searching for: {search_term}")
        ui.populate_tree(tree, search_term)

    search_combo = ttk.Combobox(search_frame, textvariable=search_var, width=30)
    search_combo.pack(side="left", padx=5)
    search_combo['postcommand'] = update_suggestions # Ensure dropdown updates dynamically
    
    # Bind the update_suggestions function to the search variable
    search_var.trace('w', update_suggestions)

    # Bind Enter key to perform search
    search_combo.bind('<Return>', perform_search)

    search_button = ttk.Button(search_frame, text="Search", command=perform_search, style='TButton')
    search_button.pack(side="left", padx=5)

    columns = ("ID", "Name", "Category", "Quantity", "Min Stock")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=160)
    tree.pack(fill="both", expand=True)

    # Populate the treeview with data when the application starts
    ui.populate_tree(tree)

    # Configure the tag for low stock items
    tree.tag_configure('low_stock', foreground='red')

    # Add double-click event handler
    def on_item_double_click(event):
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])['values']
            item_id = item[0]
            item_name = item[1]
            # Directly use database function to show history
            ui.show_quantity_history(root, item_id, item_name)

    tree.bind('<Double-1>', on_item_double_click)

    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()
