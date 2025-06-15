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
import subprocess
import sys

# Import from local packages
from app.ui import ui
from app.database import db

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define default font configuration
DEFAULT_FONT = ('Helvetica', 12)
HEADING_FONT = ('Helvetica', 12, 'bold')

# Get the path to the application directory, works in both dev and PyInstaller
def get_app_path():
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

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
    # Ensure the main database connection is closed at the very beginning
    # This helps in scenarios where the database file might have been replaced (e.g., by migrate_data.py)
    db.close_main_db_connection()

    # Ensure database tables are created. This will create them if they don't exist.
    db.create_tables()

    # Create admin user if no users exist in the database (first run or after a full data wipe)
    if db.get_user_count() == 0:
        print("No users found. Creating default admin user.")
        db.add_user("admin", "admin123", role="admin")
        print("Default admin user 'admin' created successfully.")
    else:
        print("Users already exist in the database. Skipping default admin creation.")

    # Debug: Show users right before login attempt
    print("DEBUG: Users in DB right before login attempt:")
    db.debug_get_all_users()

    # Show login window
    login_window = LoginWindow()
    login_successful, user_data = login_window.run()
    
    if not login_successful:
        return  # Exit if login failed

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

    # Initialize progress bar and label (hidden initially)
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="indeterminate")
    progress_label = ttk.Label(root, text="", font=DEFAULT_FONT)

    # Functions to show/hide progress bar
    def show_progress(message="Processing...", mode="indeterminate"):
        print(f"DEBUG: show_progress called with message='{message}', mode='{mode}'")
        progress_label.config(text=message)
        progress_label.pack(pady=5)
        progress_bar.config(mode=mode) # Set the mode
        progress_bar.start()
        progress_bar.pack(pady=5)

    def hide_progress(final_message=""):
        progress_bar.stop()
        progress_bar.pack_forget()
        progress_label.config(text=final_message)
        # Optionally hide the label if no final message is desired
        # progress_label.pack_forget()

    def update_progress(percentage, message):
        progress_bar['value'] = percentage
        progress_label.config(text=f"{message} ({percentage}%)")
        root.update_idletasks() # Ensure UI updates immediately

    # --- Menu Bar ---
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # Admin Menu
    admin_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Admin", menu=admin_menu)

    # Stock Menu
    stock_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Stock", menu=stock_menu)

    # Export Menu
    export_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Export", menu=export_menu)

    # Data Menu
    data_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Data", menu=data_menu)

    # --- Function Definitions ---
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
            item = tree.item(selected_item[0])['values']
            item_id = item[0]
            item_name = item[1]
            ui.show_update_quantity_window(root, item_id, item_name, current_user_id=int(user_data['id']))

    def show_out_of_stock_window():
        ui.show_out_of_stock(root, tree)

    def show_in_stock_window():
        ui.show_in_stock(root, tree)

    def show_add_user_window():
        ui.show_add_user_window(root)

    def show_delete_user_window():
        ui.show_delete_user_window(root)

    def show_all_users_window():
        ui.show_all_users_window(root)

    def show_change_password_window():
        ui.show_change_password_window(root, int(user_data['id']))

    def download_to_local():
        if messagebox.askyesno("Confirm Download", "This will replace your local data with data from the cloud database. Are you sure you want to proceed?"):
            # Close the main application's database connection before starting the background thread
            db.close_main_db_connection()

            def run_download():
                try:
                    # Delete the existing local database file if it exists
                    db_file_path = os.path.join(get_app_path(), 'database', 'inventory.db')
                    if os.path.exists(db_file_path):
                        os.remove(db_file_path)
                        print(f"Local database {db_file_path} deleted successfully.")

                    # Define the PostgreSQL DATABASE_URL
                    postgresql_db_url = "postgresql://Stock_Database_owner:npg_9REjbMoDi2wc@ep-misty-mountain-a15c30qc-pooler.ap-southeast-1.aws.neon.tech/Stock_Database?sslmode=require"
                    
                    # Import and run migration directly
                    from app.database.migrate_data import migrate_data
                    migrate_data(postgresql_db_url)
                    
                    # Re-establish the main database connection and refresh UI on the main thread after successful download
                    def refresh_and_show_success():
                        db.get_main_db_connection() 
                        db.reset_auto_increment_sequence('products') # Reset products sequence
                        db.deduplicate_admin_users() # Deduplicate admin users after download
                        ui.populate_tree(tree)
                        hide_progress("Download Complete!")
                        messagebox.showinfo("Download Complete", "Data successfully downloaded from cloud to local!")
                    root.after(0, refresh_and_show_success)
                except Exception as e:
                    def show_error(error):
                        hide_progress("Download Failed.")
                        messagebox.showerror("Error", f"An unexpected error occurred during download: {error}")
                    root.after(0, lambda error=e: show_error(error))
                finally:
                    def cleanup():
                        hide_progress("") # Ensure progress bar is hidden eventually
                    root.after(0, cleanup)

            # Start the download process in a background thread
            print("DEBUG: Calling show_progress for download.")
            show_progress("Downloading data...", mode="determinate")
            threading.Thread(target=run_download, daemon=True).start()

    def upload_to_cloud():
        if messagebox.askyesno("Confirm Upload", "This will replace your cloud data with data from your local database. Are you sure you want to proceed?"):
            # Close the main application's database connection before starting the background thread
            db.close_main_db_connection()

            def run_upload():
                try:
                    # Define the PostgreSQL DATABASE_URL
                    postgresql_db_url = "postgresql://Stock_Database_owner:npg_9REjbMoDi2wc@ep-misty-mountain-a15c30qc-pooler.ap-southeast-1.aws.neon.tech/Stock_Database?sslmode=require"
                    
                    # Import and run upload directly
                    from app.database.upload_to_cloud import upload_data
                    upload_data(postgresql_db_url)
                    
                    # Re-establish the main database connection and refresh UI on the main thread after successful upload
                    def refresh_and_show_success():
                        db.get_main_db_connection() 
                        ui.populate_tree(tree)
                        hide_progress("Upload Complete!")
                        messagebox.showinfo("Upload Complete", "Data successfully uploaded from local to cloud!")
                    root.after(0, refresh_and_show_success)
                except Exception as e:
                    def show_error(error):
                        hide_progress("Upload Failed.")
                        messagebox.showerror("Error", f"An unexpected error occurred during upload: {error}")
                    root.after(0, lambda error=e: show_error(error))
                finally:
                    def cleanup():
                        hide_progress("")
                    root.after(0, cleanup)
            
            # Start the upload process in a background thread
            print("DEBUG: Calling show_progress for upload.")
            show_progress("Uploading data...", mode="determinate")
            threading.Thread(target=run_upload, daemon=True).start()

    # Add menu commands
    # Only show user management options for admin users
    if user_data['role'] == 'admin':
        admin_menu.add_command(label="Add User", command=show_add_user_window)
        admin_menu.add_command(label="Delete User", command=show_delete_user_window)
        admin_menu.add_command(label="Show Users", command=show_all_users_window)
        admin_menu.add_separator()

    admin_menu.add_command(label="Change Password", command=show_change_password_window)

    stock_menu.add_command(label="In-Stock Products", command=show_in_stock_window)
    stock_menu.add_command(label="Out of Stock Products", command=show_out_of_stock_window)

    export_menu.add_command(label="Export to CSV", command=export_selected_to_csv)
    export_menu.add_command(label="Print Stock", command=print_stock)

    data_menu.add_command(label="Download to Local", command=download_to_local)
    data_menu.add_command(label="Upload to Cloud", command=upload_to_cloud)

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
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()

def on_closing(root):
    # Close the main database connection when the application closes
    db.close_main_db_connection()
    root.destroy()

if __name__ == "__main__":
    main()
