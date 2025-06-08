# StockMaster - Inventory Management App

A simple inventory management application built with Python and Tkinter.

## Features
- Add, update, and remove products
- Track product quantity and minimum stock
- View quantity change history for each product
- Highlight low stock items
- Export quantity history for selected items and date range to CSV
- User-friendly GUI
- **Automatic application updates on startup**

## Requirements
- Python 3.8+
- tkinter (usually included with Python)
- tkcalendar
- PostgreSQL (used by the backend service)

## Setup
1. **Clone the repository:**
   ```sh
   git clone "https://github.com/Ashishkaus04/stock_project.git"
   cd stock_project
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Data Migration (SQLite to PostgreSQL)
If you have existing data in a SQLite database or a CSV file and wish to migrate it to your PostgreSQL database, follow these steps:

1.  **Update the migration script:**
    *   Open `src/app/database/migrate_data.py`.
    *   If migrating from a SQLite `.db` file, ensure `connect_sqlite()` points to your SQLite database file (e.g., `sqlite3.connect(r"F:\path\to\your\inventory.db")`).
    *   If migrating `quantity_history` from a CSV file, update the `csv_file_path` variable to the absolute path of your CSV file (e.g., `r"C:\Users\YourUser\Downloads\your_history.csv"`).

2.  **Ensure CSV format (for Quantity History):** If you are importing `quantity_history` from a CSV, ensure it has the following columns in the header (case-insensitive, exact wording): `Product Name`, `Category`, `Date`, `Old Quantity`, `New Quantity`, `Seller/Buyer Name`, `Invoice Number`, `Changed By`.

3.  **Run the migration script:**
    ```sh
    python src/app/database/migrate_data.py
    ```
    *   The script will attempt to migrate products from the SQLite database first (if specified and not empty). If products are not found from SQLite, or if `quantity_history` is being imported from CSV, it will attempt to find or create products in the PostgreSQL database based on 'Product Name' and 'Category' from the CSV.
    *   It will then migrate quantity history and users (if the users table exists in SQLite and the migration for users is uncommented in the script).

## Usage
Run the Tkinter client application. It will connect to the Flask API deployed on Render:
```sh
python run.py
```

Alternatively, if you have built the executable, run `run.exe` from the `dist` folder.

## Auto-Update Feature
The application automatically checks for updates hosted on a Render service when it starts. If a new version is available, it will be downloaded, and you will be prompted to restart the application to apply the update.

## Exporting Data
- Select one or more products in the main window.
- Click "Export to CSV".
- Choose a start and end date using the calendar widgets.
- Save the exported CSV file.

## Building and Releasing a New Version (Windows)
To build and release a new version with the auto-update mechanism:

1.  **Ensure you have PyInstaller installed:**
    ```sh
    pip install pyinstaller
    ```

2.  **Update the application version:** Manually update the `CURRENT_VERSION` string in `src/app/main.py` and the `version` field in `static/version.json`.
    *   **Note**: The `version.json` in the `static/` folder is the authoritative source for the client's update check.

3.  **Build the executable:** Run PyInstaller using the `run.spec` file.
    ```sh
    pyinstaller run.spec
    ```

4.  **Locate the new executable and version file:** The new `run.exe` will be in the `dist` folder. The `version.json` file is in `static/`.

5.  **Upload to Render Static Assets:** Upload both the new `run.exe` (from `dist/`) and the updated `version.json` file (from `static/`) to your Render web service's static assets hosting. Ensure they are accessible at the URLs configured in `src/app/main.py` (`https://stock-project-nnei.onrender.com/static/main.exe` and `https://stock-project-nnei.onrender.com/static/version.json`).

When users run their existing version of the application, it will detect the new version on Render and prompt them to update.

## Notes
- If your antivirus deletes the `.exe`, add an exclusion for your project folder.
- For any issues with missing modules in the executable, let us know or check PyInstaller documentation.

## License
MIT License 