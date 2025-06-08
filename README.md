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
   git clone <your-repo-url>
   cd stock_project
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

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