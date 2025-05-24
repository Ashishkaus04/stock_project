import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import db
from datetime import datetime
import csv

def populate_tree(tree):
    for row in tree.get_children():
        tree.delete(row)
    conn = db.connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, quantity, min_stock FROM products")
    for row in cursor.fetchall():
        item_id, name, category, quantity, min_stock = row
        # Format the row to show N/A for None values
        formatted_row = [str(val) if val is not None else "N/A" for val in row]
        item = tree.insert("", "end", values=formatted_row)
        # If quantity is below min_stock, tag the item
        if min_stock is not None and quantity < min_stock:
            tree.item(item, tags=('low_stock',))
    conn.close()

def add_product_window(root, tree=None):
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
            db.add_product(
                data["name"],
                data["category"],
                int(data["quantity"]),
                int(data["min_stock"])
            )
            win.destroy()
            if tree:
                populate_tree(tree)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add product: {str(e)}")

    tk.Button(win, text="Save", command=save).grid(row=len(fields), column=0, columnspan=2, pady=10)

def show_in_stock(root, main_tree=None):
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
        conn = db.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, quantity, min_stock FROM products")
        for row in cursor.fetchall():
            item_id, name, quantity, min_stock = row
            item = tree.insert("", "end", values=(item_id, name, quantity))
            if min_stock is not None and quantity < min_stock:
                tree.item(item, tags=('low_stock',))
        conn.close()

    def add_new_item():
        add_product_window(win, tree=tree)

    def update_quantity():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
            
        item = tree.item(selected[0])['values']
        item_id = item[0]
        item_name = item[1]
        old_qty = item[2]

        # Get all product details
        conn = db.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, category, quantity, min_stock FROM products WHERE id = ?", (item_id,))
        product = cursor.fetchone()
        conn.close()

        update_win = tk.Toplevel(win)
        update_win.title(f"Update Product - {item_name}")
        update_win.geometry("400x400")
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
        tk.Label(name_frame, text=product[0], font=("Arial", 9, "bold")).pack(side="left")

        # Category
        cat_frame = tk.Frame(details_frame)
        cat_frame.pack(fill="x", pady=2)
        tk.Label(cat_frame, text="Category:", width=10, anchor="w").pack(side="left")
        tk.Label(cat_frame, text=product[1] or "N/A").pack(side="left")

        # Min Stock
        min_frame = tk.Frame(details_frame)
        min_frame.pack(fill="x", pady=2)
        tk.Label(min_frame, text="Min Stock:", width=10, anchor="w").pack(side="left")
        tk.Label(min_frame, text=product[3] or "N/A").pack(side="left")

        # Current Quantity
        curr_frame = tk.Frame(details_frame)
        curr_frame.pack(fill="x", pady=2)
        tk.Label(curr_frame, text="Current Qty:", width=10, anchor="w").pack(side="left")
        tk.Label(curr_frame, text=str(product[2]), font=("Arial", 9, "bold")).pack(side="left")

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

        # Preview section
        preview_frame = tk.LabelFrame(frame, text="Preview", padx=10, pady=10)
        preview_frame.pack(fill="x", pady=(0, 15))
        
        preview_label = tk.Label(preview_frame, text=f"New Total: {product[2]}")
        preview_label.pack(pady=5)

        def update_preview(*args):
            try:
                add_qty = int(qty_entry.get())
                new_total = product[2] + add_qty
                preview_label.config(text=f"New Total: {new_total}")
                
                # Add warning if below min stock
                if new_total < product[3]:
                    preview_label.config(fg="red")
                else:
                    preview_label.config(fg="black")
            except ValueError:
                preview_label.config(text="New Total: Invalid", fg="red")

        # Bind the entry to update preview
        qty_entry.bind('<KeyRelease>', update_preview)

        def validate_and_save():
            try:
                add_qty = int(qty_entry.get())
                new_qty = product[2] + add_qty
                if new_qty < 0:
                    messagebox.showerror("Error", "Final quantity cannot be negative")
                    return
                    
                db.update_product_quantity(item_id, new_qty)
                messagebox.showinfo("Success", f"Quantity updated to {new_qty}")
                update_win.destroy()
                populate_in_stock()
                if main_tree:
                    populate_tree(main_tree)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update quantity: {str(e)}")

        def on_enter(event):
            validate_and_save()

        # Bind Enter key to save
        qty_entry.bind('<Return>', on_enter)
        update_win.bind('<Return>', on_enter)  # Also bind to the window

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

def show_out_of_stock(root, main_tree=None):
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
        for row in tree.get_children():
            tree.delete(row)
        conn = db.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, quantity, min_stock FROM products")
        for row in cursor.fetchall():
            item_id, name, category, quantity, min_stock = row
            # Format the row to show N/A for None values
            formatted_row = [str(val) if val is not None else "N/A" for val in row]
            item = tree.insert("", "end", values=formatted_row)
            if min_stock is not None and quantity < min_stock:
                tree.item(item, tags=('low_stock',))
        conn.close()

    def remove_stock():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to remove stock")
            return
            
        item = tree.item(selected[0])['values']
        item_id = item[0]
        item_name = item[1]
        current_qty = int(item[3])

        remove_win = tk.Toplevel(win)
        remove_win.title(f"Remove Stock - {item_name}")
        remove_win.geometry("300x200")
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

                db.update_product_quantity(item_id, new_qty)
                messagebox.showinfo("Success", f"Removed {remove_qty} items. New quantity: {new_qty}")
                remove_win.destroy()
                populate_out_of_stock()
                if main_tree:
                    populate_tree(main_tree)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove stock: {str(e)}")

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
        item_id = item[0]
        item_name = item[1]

        if not messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete '{item_name}'?\nThis action cannot be undone."):
            return

        try:
            conn = db.connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Item '{item_name}' has been deleted")
            populate_out_of_stock()
            if main_tree:
                populate_tree(main_tree)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete item: {str(e)}")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Remove Stock", command=remove_stock).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete Item", command=delete_item).pack(side="left", padx=5)

    populate_out_of_stock()

def show_quantity_history(root, item_id, item_name):
    win = tk.Toplevel(root)
    win.title(f"Quantity History - {item_name}")
    win.geometry("600x400")
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

    # Get current product details
    product = db.get_product_details(item_id)
    if not product:
        messagebox.showerror("Error", "Product not found")
        win.destroy()
        return

    # Name
    name_frame = tk.Frame(info_frame)
    name_frame.pack(fill="x", pady=2)
    tk.Label(name_frame, text="Name:", width=10, anchor="w").pack(side="left")
    tk.Label(name_frame, text=product[0], font=("Arial", 9, "bold")).pack(side="left")

    # Category
    cat_frame = tk.Frame(info_frame)
    cat_frame.pack(fill="x", pady=2)
    tk.Label(cat_frame, text="Category:", width=10, anchor="w").pack(side="left")
    tk.Label(cat_frame, text=product[1] or "N/A").pack(side="left")

    # Current Quantity
    curr_frame = tk.Frame(info_frame)
    curr_frame.pack(fill="x", pady=2)
    tk.Label(curr_frame, text="Current Qty:", width=10, anchor="w").pack(side="left")
    tk.Label(curr_frame, text=str(product[2]), font=("Arial", 9, "bold")).pack(side="left")

    # Min Stock
    min_frame = tk.Frame(info_frame)
    min_frame.pack(fill="x", pady=2)
    tk.Label(min_frame, text="Min Stock:", width=10, anchor="w").pack(side="left")
    tk.Label(min_frame, text=product[3] or "N/A").pack(side="left")

    # Created Date
    created_frame = tk.Frame(info_frame)
    created_frame.pack(fill="x", pady=2)
    tk.Label(created_frame, text="Created:", width=10, anchor="w").pack(side="left")
    created_date = product[4]
    if isinstance(created_date, str):
        try:
            created_date = datetime.fromisoformat(created_date)
        except ValueError:
            pass
    date_str = created_date.strftime("%Y-%m-%d %H:%M") if hasattr(created_date, 'strftime') else str(created_date)
    tk.Label(created_frame, text=date_str).pack(side="left")

    # History section
    history_frame = tk.LabelFrame(frame, text="Quantity History", padx=10, pady=10)
    history_frame.pack(fill="both", expand=True)

    # Create Treeview for history
    history_columns = ("Date", "Old Quantity", "New Quantity", "Change")
    history_tree = ttk.Treeview(history_frame, columns=history_columns, show="headings", height=10)
    for col in history_columns:
        history_tree.heading(col, text=col)
        history_tree.column(col, width=100)
    history_tree.pack(fill="both", expand=True)

    # Add scrollbar to history tree
    history_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=history_tree.yview)
    history_scroll.pack(side="right", fill="y")
    history_tree.configure(yscrollcommand=history_scroll.set)

    # Populate history
    history = db.get_quantity_history(item_id)
    for old_qty, new_qty, change_date in history:
        change = new_qty - old_qty
        change_text = f"{'+' if change > 0 else ''}{change}"
        # Format the date string
        if isinstance(change_date, str):
            try:
                change_date = datetime.fromisoformat(change_date)
            except ValueError:
                pass
        date_str = change_date.strftime("%Y-%m-%d %H:%M") if hasattr(change_date, 'strftime') else str(change_date)
        history_tree.insert("", "end", values=(
            date_str,
            old_qty,
            new_qty,
            change_text
        ))

    # Only show the Close button
    button_frame = tk.Frame(frame)
    button_frame.pack(side="bottom", fill="x", pady=(10, 0))
    close_btn = tk.Button(button_frame, text="Close", command=win.destroy, width=10)
    close_btn.pack(side="left", padx=5)
