import tkinter as tk
from tkinter import ttk
import db
import ui
from datetime import datetime
from tkcalendar import DateEntry

def main():
    db.create_tables()

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
            ui.show_quantity_history(root, item_id, item_name)

    tree.bind('<Double-1>', on_item_double_click)

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", pady=(10, 0))

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
            from datetime import datetime, time
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
            import csv
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Product Name", "Category", "Date", "Old Quantity", "New Quantity", "Change", "Name", "Invoice Number"])
                for sel in selected:
                    item = tree.item(sel)['values']
                    item_id = item[0]
                    product = db.get_product_details(item_id)
                    history = db.get_quantity_history(item_id)
                    for old_qty, new_qty, change_date, name, invoice_number in history:
                        # Filter by date range
                        if isinstance(change_date, str):
                            try:
                                change_date_dt = datetime.fromisoformat(change_date)
                            except Exception:
                                continue
                        else:
                            change_date_dt = change_date
                        if change_date_dt < start_dt or change_date_dt > end_dt:
                            continue
                        change = new_qty - old_qty
                        change_text = f"{'+' if change > 0 else ''}{change}"
                        date_str = change_date_dt.strftime("%Y-%m-%d %H:%M")
                        writer.writerow([
                            product[0],
                            product[1] or "N/A",
                            date_str,
                            old_qty,
                            new_qty,
                            change_text,
                            name or "N/A",
                            invoice_number or "N/A"
                        ])
            tk.messagebox.showinfo("Success", f"History exported successfully to:\n{file_path}")
        tk.Button(prompt, text="OK", command=on_ok).grid(row=2, column=0, columnspan=2, pady=10)

    tk.Button(btn_frame, text="Export to CSV", command=export_selected_to_csv).pack(side="left", padx=5)

    def print_stock():
        # Ask for file path
        from datetime import datetime
        suggested_name = f"stock_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=suggested_name
        )
        if not file_path:
            return
        import csv
        conn = db.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, category, quantity FROM products")
        rows = cursor.fetchall()
        conn.close()
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Product Name", "Category", "Quantity"])
            for row in rows:
                writer.writerow(row)
        tk.messagebox.showinfo("Success", f"Stock exported successfully to:\n{file_path}")

    # Add button to UI
    tk.Button(btn_frame, text="Print Stock", command=print_stock).pack(side="left", padx=5)

    ui.populate_tree(tree)
    root.mainloop()

if __name__ == "__main__":
    main()
