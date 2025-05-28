import tkinter as tk
from tkinter import ttk, messagebox, filedialog
# import db # Remove direct db import
import ui
from datetime import datetime, time
from tkcalendar import DateEntry
import csv
import requests
import subprocess
import sys

# Define the base URL for your Flask API (placeholder - replace with your Render service URL)
API_BASE_URL = "http://127.0.0.1:5000" # Replace with your Render service URL later

def main():
    # Start the Flask backend server in a separate process
    try:
        # Use sys.executable to ensure the same Python interpreter is used
        # The command should be 'python app.py'
        # We run in the background and capture output to avoid blocking
        backend_process = subprocess.Popen([sys.executable, 'app.py'], cwd='.')
        print("Backend process started with PID:", backend_process.pid)
    except Exception as e:
        print(f"Failed to start backend process: {e}")
        messagebox.showerror("Startup Error", "Failed to start the backend server. Please ensure app.py is in the correct directory.")
        return # Exit if the backend fails to start

    # db.create_tables() # Database table creation should be handled by the backend service

    root = tk.Tk()
    root.title("MVD Stock Manager")
    root.geometry("800x400")

    columns = ("ID", "Name", "Category", "Quantity", "Min Stock")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
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
            ui.show_quantity_history(root, item_id, item_name)

    tree.bind('<Double-1>', on_item_double_click)

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", pady=(10, 0))

    # These functions in ui.py already use the API
    tk.Button(btn_frame, text="In-Stock", command=lambda: ui.show_in_stock(root, tree)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Out of Stock", command=lambda: ui.show_out_of_stock(root, tree)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Refresh", command=lambda: ui.populate_tree(tree)).pack(side="left", padx=5)

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
            product_names = {}

            try:
                for sel in selected:
                    item = tree.item(sel)['values']
                    item_id = int(item[0]) # Ensure item_id is integer

                    # Fetch product details from API
                    product_response = requests.get(f"{API_BASE_URL}/product/{item_id}")
                    product_response.raise_for_status()
                    product = product_response.json()
                    product_names[item_id] = (product.get('name', 'N/A'), product.get('category', 'N/A'))

                    # Fetch history from API
                    history_response = requests.get(f"{API_BASE_URL}/product/{item_id}/history")
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
                        if change_date_dt < start_dt or change_date_dt > end_dt:
                            continue

                        history_data.append({
                            "product_id": item_id,
                            "old_quantity": record.get('old_quantity'),
                            "new_quantity": record.get('new_quantity'),
                            "change_date": change_date_dt,
                            "name": record.get('name'), # This is seller/buyer name from history
                            "invoice_number": record.get('invoice_number')
                        })

            except requests.exceptions.RequestException as e:
                messagebox.showerror("API Error", f"Failed to fetch data for CSV export: {e}")
                return

            # Sort history data by date (optional, but good for chronological export)
            history_data.sort(key=lambda x: x['change_date'])

            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Product Name", "Category", "Date", "Old Quantity", "New Quantity", "Change", "Name", "Invoice Number"])

                for record in history_data:
                    product_name, product_category = product_names.get(record['product_id'], ("N/A", "N/A"))
                    old_qty = record['old_quantity']
                    new_qty = record['new_quantity']
                    change_date_dt = record['change_date']
                    name = record['name']
                    invoice_number = record['invoice_number']

                    change = "N/A"
                    try:
                        old_num = int(old_qty) if old_qty is not None else 0
                        new_num = int(new_qty) if new_qty is not None else 0
                        change = new_num - old_num
                        change_text = f"{'+' if change > 0 else ''}{change}"
                    except (ValueError, TypeError):
                        change_text = "N/A"

                    date_str = change_date_dt.strftime("%Y-%m-%d %H:%M")

                    writer.writerow([
                        product_name,
                        product_category or "N/A",
                        date_str,
                        old_qty if old_qty is not None else "N/A",
                        new_qty if new_qty is not None else "N/A",
                        change_text,
                        name or "N/A",
                        invoice_number or "N/A"
                    ])

            tk.messagebox.showinfo("Success", f"History exported successfully to:\n{file_path}")
        tk.Button(prompt, text="OK", command=on_ok).grid(row=2, column=0, columnspan=2, pady=10)

    tk.Button(btn_frame, text="Export to CSV", command=export_selected_to_csv).pack(side="left", padx=5)

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
            response = requests.get(f"{API_BASE_URL}/stock")
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
    tk.Button(btn_frame, text="Print Stock", command=print_stock).pack(side="left", padx=5)

    # populate_tree is already updated to use the API via ui.py
    ui.populate_tree(tree)
    root.mainloop()

if __name__ == "__main__":
    main()
