# Stock Management System

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

## Exporting Data
- Select one or more products in the main window.
- Click "Export to CSV".
- Choose a start and end date using the calendar widgets.
- Save the exported CSV file.

## Building and Releasing a New Version (Windows)
To build a new version:

1.  **Ensure you have PyInstaller installed:**
    ```sh
    pip install pyinstaller
    ```

2.  **Update the application version:** Manually update the `CURRENT_VERSION` string in `src/app/main.py`.

3.  **Build the executable:**
    ```sh
    pyinstaller run.spec
    ```

4.  **Locate the new executable:** The new `run.exe` will be in the `dist` folder.

## Notes
- If your antivirus deletes the `.exe`, add an exclusion for your project folder.
- For any issues with missing modules in the executable, let us know or check PyInstaller documentation.

## License
MIT License 