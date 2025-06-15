# Stock Management System

A modern stock management system with a user-friendly interface and comprehensive data management capabilities.

## Features
- Real-time stock tracking and management
- Modern, responsive user interface
- Data export functionality with date range selection
- Product management with detailed information
- Transaction history tracking
- Search and filter capabilities
- Data migration support

## Local Setup (Single Machine)

### 1. Install dependencies
```sh
pip install -r requirements.txt
```

### 2. Run the migration script (if migrating from PostgreSQL):
```sh
python src/app/database/migrate_data.py
```

### 3. Run the Tkinter client application
```sh
python run.py
```

Alternatively, if you have built the executable, run `run.exe` from the `dist` folder.

## Key Features

### Data Export
- Select one or more products in the main window
- Click "Export to CSV"
- Choose a start and end date using the calendar widgets
- Save the exported CSV file with detailed transaction data

### Product Management
- Add, edit, and delete products
- Track product details including:
  - Product name
  - Description
  - Current stock level
  - Price information
  - Transaction history

### Search and Filter
- Search products by name or description
- Filter products by various criteria
- Sort data by different columns

## Building and Releasing a New Version (Windows)
To build a new version:

1. **Ensure you have PyInstaller installed:**
    ```sh
    pip install pyinstaller
    ```

2. **Update the application version:** Manually update the `CURRENT_VERSION` string in `src/app/main.py`.

3. **Build the executable:**
    ```sh
    pyinstaller run.spec
    ```

4. **Locate the new executable:** The new `run.exe` will be in the `dist` folder.

## Notes
- If your antivirus deletes the `.exe`, add an exclusion for your project folder
- For any issues with missing modules in the executable, let us know or check PyInstaller documentation
- The application uses SQLite for data storage by default
- Regular backups of your data are recommended

## License
MIT License 