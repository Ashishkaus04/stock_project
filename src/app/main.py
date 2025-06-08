import tkinter as tk
from tkinter import ttk, messagebox, filedialog
# import db # Remove direct db import
from datetime import datetime, time
from tkcalendar import DateEntry
import csv
import requests
import subprocess
import sys
import os
import tempfile
import json
import shutil
import threading
from flask import Flask
from app.api.app import create_app
from waitress import serve # Import waitress

# Import from local packages
from .ui import ui
from .database import db

from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the base URL for your Flask API (placeholder - replace with your Render service URL)
API_BASE_URL = "https://stock-project-nnei.onrender.com"

# Auto-update configuration
CURRENT_VERSION = "1.1" # !!! IMPORTANT: Update this version number for each new release
VERSION_URL = "https://stock-project-nnei.onrender.com/static/version.json"
DOWNLOAD_URL = "https://stock-project-nnei.onrender.com/static/main.exe"

# Define temporary update file name
UPDATE_TEMP_FILE = "main.exe.temp"
OLD_EXE_FILE = "main.exe.old"

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
        self.auth_token = None
        
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_data = data['user']
                self.auth_token = data['token']
                print(f"DEBUG: Login Successful. Auth Token: {self.auth_token[:10]}...") # Log partial token
                self.login_successful = True
                self.root.destroy()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")
    
    def run(self):
        self.root.mainloop()
        return self.login_successful, self.user_data, self.auth_token

def configure_fonts():
    """Configure fonts for the application."""
    style = ttk.Style()
    
    # Configure default font for all ttk widgets
    style.configure('.', font=DEFAULT_FONT)
    
    # Configure specific widget fonts
    style.configure('Treeview', font=DEFAULT_FONT)
    style.configure('Treeview.Heading', font=HEADING_FONT)
    style.configure('TButton', font=DEFAULT_FONT)
    style.configure('TLabel', font=DEFAULT_FONT)
    style.configure('TEntry', font=DEFAULT_FONT)
    style.configure('TCombobox', font=DEFAULT_FONT)

def change_theme(theme_name):
    """Change the application theme."""
    style = ttk.Style()
    try:
        style.theme_use(theme_name)
        print(f"Theme changed to {theme_name}")
    except tk.TclError as e:
        print(f"Error changing theme: {e}")
        messagebox.showerror("Theme Error", f"Failed to change theme: {e}")

def check_for_updates():
    try:
        response = requests.get(VERSION_URL)
        response.raise_for_status() # Raise an exception for bad status codes
        version_info = response.json()
        latest_version = version_info.get("latest_version")

        if latest_version and latest_version > CURRENT_VERSION:
            print(f"New version ({latest_version}) available. Current version: {CURRENT_VERSION}")
            # Download the new executable
            download_update(latest_version)
            return True # Indicate that an update was found and downloaded
        else:
            print("Application is up to date.")
            return False # Indicate no update was found

    except requests.exceptions.RequestException as e:
        print(f"Error checking for updates: {e}")
        return False
    except json.JSONDecodeError:
        print("Error decoding version.json")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during update check: {e}")
        return False

def download_update(version):
    try:
        print(f"Downloading update version {version} from {DOWNLOAD_URL}")
        response = requests.get(DOWNLOAD_URL, stream=True)
        response.raise_for_status()

        # Get the directory of the currently running executable
        app_dir = os.path.dirname(sys.executable)
        new_exe_path = os.path.join(app_dir, UPDATE_TEMP_FILE)

        with open(new_exe_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Update downloaded successfully to {new_exe_path}")
        messagebox.showinfo("Update Downloaded",
                            f"A new version ({version}) has been downloaded.\n" +
                            "Please restart the application to apply the update.")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading update: {e}")
        messagebox.showerror("Download Error", f"Failed to download update: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")

def apply_update():
    # Get the path to the current executable
    current_exe = sys.executable
    app_dir = os.path.dirname(current_exe)
    temp_update_path = os.path.join(app_dir, UPDATE_TEMP_FILE)
    old_exe_path = os.path.join(app_dir, OLD_EXE_FILE)

    # Check if a temporary update file exists
    if os.path.exists(temp_update_path):
        print(f"Applying update from {temp_update_path}")
        try:
            # Clean up old backup if it exists
            if os.path.exists(old_exe_path):
                os.remove(old_exe_path)

            # Rename current executable to .old
            os.rename(current_exe, old_exe_path)

            # Rename temporary update to current executable name
            os.rename(temp_update_path, current_exe)

            print("Update applied successfully.")
            # Clean up the old executable backup (attempt, might fail if still in use)
            try:
                if os.path.exists(old_exe_path):
                   os.remove(old_exe_path)
            except Exception as e:
                 print(f"Could not remove old executable backup {old_exe_path}: {e}")
                 # This is not critical, the app should still run.

            messagebox.showinfo("Update Applied", "Application has been updated. Click OK to continue.")
            return True # Indicate update applied

        except OSError as e:
            print(f"Error applying update: {e}")
            messagebox.showerror("Update Error",
                                 f"Failed to apply update: {e}\n" +
                                 "Please ensure you have permissions to write to the application directory\n" +
                                 "and try restarting the application again.")
            # If update fails, we might be in an inconsistent state, could exit here.
            # sys.exit(1)
            return False # Indicate update failed

        except Exception as e:
             print(f"An unexpected error occurred during update application: {e}")
             messagebox.showerror("Update Error", f"An unexpected error occurred during update: {e}")
             return False # Indicate update failed
    else:
        print("No update file found to apply.")
        return False # Indicate no update file was present

def run_flask_app():
    app = create_app()
    serve(app, host='127.0.0.1', port=5000) # Use waitress to serve the app

def main():
    # Attempt to apply update on startup
    update_applied = apply_update()
    
    # Check for updates after starting the backend
    if not update_applied:
       check_for_updates()

    # Show login window
    login_window = LoginWindow()
    login_successful, user_data, auth_token = login_window.run()
    
    if not login_successful:
        return  # Exit if login failed
    
    # Create main application window
    root = tk.Tk()
    root.title(f"MVD Stock Manager - Welcome {user_data['username']}")
    root.geometry("800x400")

    # Configure fonts
    configure_fonts()
    
    # Create a style object and set clam theme
    style = ttk.Style()
    style.theme_use('clam')

    # Add user info and logout button
    user_frame = tk.Frame(root)
    user_frame.pack(fill="x", pady=(5, 0))
    
    ttk.Label(user_frame, text=f"Logged in as: {user_data['username']}", font=DEFAULT_FONT).pack(side="left", padx=5)
    
    def logout():
        try:
            response = requests.post(
                f"{API_BASE_URL}/logout",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if response.status_code == 200:
                root.quit()
            else:
                messagebox.showerror("Logout Error", "Failed to logout properly")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")
    
    ttk.Button(user_frame, text="Logout", command=logout, style='TButton').pack(side="right", padx=5)

    # --- Menu Bar ---
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # Admin Menu (or a new menu for User Management)
    # We'll add this only if the logged-in user has an 'admin' role
    if user_data.get('role') == 'admin':
        adminmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Admin", menu=adminmenu)
        adminmenu.add_command(label="Add New User", command=lambda: ui.add_user_window(root, auth_token))

        def show_users_window():
            users_win = tk.Toplevel(root)
            users_win.title("All Users")
            users_tree = ttk.Treeview(users_win, columns=("ID", "Username", "Role"), show="headings")
            for col in ("ID", "Username", "Role"):
                users_tree.heading(col, text=col)
                users_tree.column(col, width=120)
            users_tree.pack(fill="both", expand=True, padx=10, pady=10)
            try:
                response = requests.get(f"{API_BASE_URL}/debug/users")
                response.raise_for_status()
                users = response.json()
                for user in users:
                    users_tree.insert("", "end", values=(user['id'], user['username'], user['role']))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch users: {e}")

        def delete_user_window():
            del_win = tk.Toplevel(root)
            del_win.title("Delete User")
            users_tree = ttk.Treeview(del_win, columns=("ID", "Username", "Role"), show="headings")
            for col in ("ID", "Username", "Role"):
                users_tree.heading(col, text=col)
                users_tree.column(col, width=120)
            users_tree.pack(fill="both", expand=True, padx=10, pady=10)
            try:
                response = requests.get(f"{API_BASE_URL}/debug/users")
                response.raise_for_status()
                users = response.json()
                for user in users:
                    users_tree.insert("", "end", values=(user['id'], user['username'], user['role']))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch users: {e}")
                return
            def delete_selected():
                selected = users_tree.selection()
                if not selected:
                    messagebox.showwarning("Warning", "Please select a user to delete.")
                    return
                user_id = users_tree.item(selected[0])['values'][0]
                if messagebox.askyesno("Confirm", f"Are you sure you want to delete user ID {user_id}?"):
                    try:
                        response = requests.delete(f"{API_BASE_URL}/users/{user_id}", headers={"Authorization": f"Bearer {auth_token}"})
                        if response.status_code == 200:
                            messagebox.showinfo("Success", "User deleted successfully.")
                            users_tree.delete(selected[0])
                        else:
                            messagebox.showerror("Error", f"Failed to delete user: {response.text}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete user: {e}")
            tk.Button(del_win, text="Delete Selected User", command=delete_selected, font=DEFAULT_FONT).pack(pady=10)

        adminmenu.add_command(label="Show Users", command=show_users_window)
        adminmenu.add_command(label="Delete User", command=delete_user_window)

    # Add search feature
    search_frame = tk.Frame(root)
    search_frame.pack(fill="x", pady=(5, 0))

    tk.Label(search_frame, text="Search:", font=DEFAULT_FONT).pack(side="left", padx=5)
    
    # Create a Combobox for search with suggestions
    search_var = tk.StringVar()
    search_combo = ttk.Combobox(search_frame, textvariable=search_var, font=DEFAULT_FONT)
    search_combo.pack(side="left", fill="x", expand=True, padx=5)
    
    def update_suggestions(*args):
        search_term = search_var.get()
        if search_term:
            try:
                # Get suggestions from the API
                response = requests.get(
                    f"{API_BASE_URL}/products?search={requests.utils.quote(search_term)}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                response.raise_for_status()
                products = response.json()
                
                # Create a list of suggestions from product names and categories
                suggestions = set()
                for product in products:
                    if product['name']:
                        suggestions.add(product['name'])
                    if product['category']:
                        suggestions.add(product['category'])
                
                # Update the combobox values
                search_combo['values'] = sorted(list(suggestions))
                
                # Show the dropdown if there are suggestions
                if suggestions:
                    search_combo.event_generate('<Down>')
            except requests.exceptions.RequestException as e:
                print(f"Error getting suggestions: {e}")

    # Bind the update_suggestions function to the search variable
    search_var.trace('w', update_suggestions)

    def perform_search(event=None):
        search_term = search_var.get()
        print(f"Searching for: {search_term}")
        ui.populate_tree(tree, search_term, auth_token)

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

    # Configure the tag for low stock items
    tree.tag_configure('low_stock', foreground='red')

    # Add double-click event handler
    def on_item_double_click(event):
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])['values']
            item_id = item[0]
            item_name = item[1]
            # This function already uses the API via ui.py
            ui.show_quantity_history(root, item_id, item_name, auth_token)

    tree.bind('<Double-1>', on_item_double_click)

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", pady=(10, 0))

    # These functions in ui.py already use the API
    tk.Button(btn_frame, text="In-Stock", command=lambda: ui.show_in_stock(root, tree, auth_token), font=DEFAULT_FONT, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Out of Stock", command=lambda: ui.show_out_of_stock(root, tree, auth_token), font=DEFAULT_FONT, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Refresh", command=lambda: ui.populate_tree(tree, auth_token=auth_token), font=DEFAULT_FONT, width=10).pack(side="left", padx=5)

    def export_selected_to_csv():
        selected = tree.selection()
        if not selected:
            tk.messagebox.showwarning("Warning", "Please select at least one item to export history.")
            return
        # Prompt for start and end date
        prompt = tk.Toplevel(root)
        prompt.title("Select Date Range")
        tk.Label(prompt, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        start_entry = DateEntry(prompt, date_pattern='yyyy-mm-dd')
        start_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(prompt, text="End Date:").grid(row=1, column=0, padx=5, pady=5)
        end_entry = DateEntry(prompt, date_pattern='yyyy-mm-dd')
        end_entry.grid(row=1, column=1, padx=5, pady=5)
        def on_ok():
            start_date = start_entry.get_date()
            end_date = end_entry.get_date()
            prompt.destroy()
            # Set start_dt to 00:00:00 and end_dt to 23:59:59
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
            # Suggest file name with date range
            suggested_name = f"exported_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.csv"
            # Ask for file path
            file_path = tk.filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=suggested_name
            )
            if not file_path:
                return

            history_data = []
            product_info_map = {}
            user_cache = {} # Dictionary to cache usernames by user ID

            try:
                for sel in selected:
                    item = tree.item(sel)['values']
                    item_id = int(item[0]) # Ensure item_id is integer

                    # Fetch product details from API (to get name and category)
                    product_response = requests.get(
                        f"{API_BASE_URL}/product/{item_id}",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                    product_response.raise_for_status()
                    product = product_response.json()
                    product_info_map[item_id] = (product.get('name', 'N/A'), product.get('category', 'N/A'))

                    # Fetch history from API
                    history_response = requests.get(
                        f"{API_BASE_URL}/product/{item_id}/history",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                    history_response.raise_for_status()
                    history = history_response.json()

                    for record in history:
                        change_date_str = record.get('change_date')
                        if change_date_str:
                            try:
                                # Assuming change_date is in ISO format string from API
                                change_date_dt = datetime.fromisoformat(change_date_str)
                            except ValueError:
                                continue # Skip if date format is unexpected
                        else:
                             continue # Skip if no change_date

                        # Filter by date range
                        if start_dt and change_date_dt < start_dt or end_dt and change_date_dt > end_dt:
                            continue

                        user_id = record.get('user_id') # Get user_id from the history record
                        changed_by_username = "N/A" # Default value
                        if user_id is not None:
                            if user_id in user_cache:
                                changed_by_username = user_cache[user_id]
                            else:
                                try:
                                    user_response = requests.get(f"{API_BASE_URL}/users/{user_id}", headers={"Authorization": f"Bearer {auth_token}"})
                                    user_response.raise_for_status()
                                    user_data = user_response.json()
                                    changed_by_username = user_data.get('username', f"User {user_id}") # Fallback to User ID
                                    user_cache[user_id] = changed_by_username # Cache the username
                                except requests.exceptions.RequestException:
                                     changed_by_username = f"User {user_id} (Error)" # Indicate error fetching username


                        history_data.append({
                            "product_id": item_id,
                            "old_quantity": record.get('old_quantity'),
                            "new_quantity": record.get('new_quantity'),
                            "change_date": change_date_dt,
                            "name": record.get('name'), # This is seller/buyer name from history
                            "invoice_number": record.get('invoice_number'),
                            "changed_by": changed_by_username # Include the username
                        })

            except requests.exceptions.RequestException as e:
                messagebox.showerror("API Error", f"Failed to fetch data for CSV export: {e}")
                return

            # Sort history data by date (optional, but good for chronological export)
            history_data.sort(key=lambda x: x['change_date'])

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Product Name", "Category", "Date", "Old Quantity", "New Quantity", "Change", "Seller/Buyer Name", "Invoice Number", "Changed By"])

                for record in history_data:
                    product_name, product_category = product_info_map.get(record['product_id'], ("N/A", "N/A"))
                    old_qty = record['old_quantity']
                    new_qty = record['new_quantity']
                    change_date_dt = record['change_date']
                    name = record['name']
                    invoice_number = record['invoice_number']
                    changed_by = record['changed_by'] # Get the username

                    change = "N/A"
                    try:
                        old_num = int(old_qty) if old_qty is not None else 0
                        new_num = int(new_qty) if new_qty is not None else 0
                        change = new_num - old_num
                        change_text = f"{'+' if change > 0 else ''}{change}"
                    except (ValueError, TypeError):
                        change_text = "N/A"

                    date_str = change_date_dt.strftime("%Y-%m-%d %H:%M:%S") # Include seconds for precision

                    writer.writerow([
                        product_name,
                        product_category or "N/A",
                        date_str,
                        old_qty if old_qty is not None else "N/A",
                        new_qty if new_qty is not None else "N/A",
                        change_text,
                        name or "N/A",
                        invoice_number or "N/A",
                        changed_by or "N/A" # Write the username
                    ])

            tk.messagebox.showinfo("Success", f"History exported successfully to:\n{file_path}")
        tk.Button(prompt, text="OK", command=on_ok).grid(row=2, column=0, columnspan=2, pady=10)

    tk.Button(btn_frame, text="Export to CSV", command=export_selected_to_csv, font=DEFAULT_FONT, width=16).pack(side="left", padx=5)

    def print_stock():
        # Ask for file path
        suggested_name = f"stock_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=suggested_name
        )
        if not file_path:
            return

        try:
            # Make GET request to a new API endpoint to get stock data
            # We need to add a /stock endpoint to api.py first
            response = requests.get(
                f"{API_BASE_URL}/stock",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            response.raise_for_status() # Raise an exception for bad status codes
            stock_data = response.json()

            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Product Name", "Category", "Quantity"])
                for row in stock_data:
                    # Assuming the /stock endpoint returns a list of lists or tuples
                    # Or modify based on the actual JSON structure from the new API endpoint
                    writer.writerow([row.get('name', 'N/A'), row.get('category', 'N/A'), row.get('quantity', 'N/A')])

            tk.messagebox.showinfo("Success", f"Stock exported successfully to:\n{file_path}")

        except requests.exceptions.RequestException as e:
             messagebox.showerror("API Error", f"Failed to fetch stock data: {e}")

    # Add button to UI
    tk.Button(btn_frame, text="Print Stock", command=print_stock, font=DEFAULT_FONT, width=10).pack(side="left", padx=5)

    # populate_tree is already updated to use the API via ui.py
    ui.populate_tree(tree, auth_token=auth_token)
    root.mainloop()

if __name__ == "__main__":
    main()
