# StockMaster - Inventory Management App

A simple inventory management application built with Python and Tkinter.

## Features
- Add, update, and remove products
- Track product quantity and minimum stock
- View quantity change history for each product
- Highlight low stock items
- Export quantity history for selected items and date range to CSV
- User-friendly GUI

## Requirements
- Python 3.8+
- tkinter (usually included with Python)
- tkcalendar
- sqlite3 (included with Python)

## Setup
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd stock_project
   ```
2. **Install dependencies:**
   ```sh
   pip install tkcalendar
   ```

## Usage
Run the application with:
```sh
python main.py
```

## Exporting Data
- Select one or more products in the main window.
- Click "Export to CSV".
- Choose a start and end date using the calendar widgets.
- Save the exported CSV file.

## Building an Executable (Windows)
1. **Install PyInstaller:**
   ```sh
   pip install pyinstaller
   ```
2. **Build the executable:**
   ```sh
   pyinstaller --onefile --windowed main.py
   ```
3. The `.exe` will be in the `dist` folder. Copy your `inventory.db` file if you want to keep your data.

## Notes
- If your antivirus deletes the `.exe`, add an exclusion for your project folder.
- For any issues with missing modules in the executable, let us know or check PyInstaller documentation.

## License
MIT License 