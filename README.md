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
- sqlite3 (included with Python) (Note: Database is now managed by the backend service)

## Setup
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd stock_project
   ```
2. **Install dependencies:**
   ```sh
   pip install tkcalendar requests
   ```

## Usage
Run the application with:
```sh
python main.py
```

Alternatively, if you have built the executable, run `main.exe` from the `dist` folder.

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

2.  **Update the application version:** Run the `update_version.py` script. This script will automatically increment the `CURRENT_VERSION` string in `main.py` and create/update the `version.json` file with the new version number.
    ```sh
    python update_version.py
    ```

3.  **Build the executable:** Run PyInstaller on your updated `main.py`.
    ```sh
    pyinstaller --onefile --windowed main.py
    ```

4.  **Locate the new executable and version file:** The new `main.exe` will be in the `dist` folder. The `version.json` file is in your project root directory.

5.  **Upload to Render Static Assets:** Upload both the new `main.exe` (from `dist/`) and the updated `version.json` file (from your project root) to the static assets hosting of your Render service. Ensure they are accessible at the URLs configured in `main.py` (`https://stock-project-nnei.onrender.com/static/main.exe` and `https://stock-project-nnei.onrender.com/static/version.json`).

When users run their existing version of the application, it will detect the new version on Render and prompt them to update.

## Notes
- If your antivirus deletes the `.exe`, add an exclusion for your project folder.
- For any issues with missing modules in the executable, let us know or check PyInstaller documentation.

## License
MIT License

# Version Update Script

This script provides functionality to automatically update version numbers in your Python project and maintain version information in a JSON file.

## Features

### 1. Version Update in main.py
- Automatically increments the minor version number in `main.py`
- Preserves the format: `CURRENT_VERSION = "X.Y"`
- Maintains any existing comments or formatting
- Handles error cases gracefully

### 2. Version JSON Management
- Creates or updates a `version.json` file
- Stores the latest version information in JSON format
- Maintains a clean, formatted JSON structure

## Usage

### Basic Usage
```python
from update_version import update_version_in_main_py, create_version_json

# Update version in main.py
new_version = update_version_in_main_py()

# Create/update version.json
if new_version:
    create_version_json(new_version)
```

### Command Line Usage
Run the script directly to update versions:
```bash
python update_version.py
```

## Build Process Integration

After running the version update script, follow these steps to complete the build process:

1. Run PyInstaller to build the new executable:
   ```bash
   pyinstaller --onefile main.py
   ```

2. Upload the generated `main.exe` from the `dist` folder to your Render static assets

3. Upload the updated `version.json` to your Render static assets

## Backend and Database Deployment

### Backend Service Setup
1. **Create a new Web Service on Render:**
   - Go to your Render dashboard
   - Click "New +" and select "Web Service"
   - Connect your repository
   - Set the following configurations:
     - Name: `stock-project-backend`
     - Environment: `Python`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python app.py`
     - Plan: Free or paid based on your needs

2. **Environment Variables:**
   Set these in your Render dashboard:
   ```
   DATABASE_URL=your_database_url
   SECRET_KEY=your_secret_key
   ```

### Database Setup
1. **Create a PostgreSQL Database:**
   - In Render dashboard, click "New +" and select "PostgreSQL"
   - Configure the database:
     - Name: `stock_project_db`
     - Database: `stock_project`
     - User: `stock_user`
     - Region: Choose closest to your users

2. **Database Migration:**
   ```bash
   # Install Flask-Migrate
   pip install Flask-Migrate

   # Initialize migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **Database Connection:**
   Update your backend configuration to use the Render PostgreSQL database URL:
   ```python
   SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
   ```

### Static Assets Hosting
1. **Configure Static Assets:**
   - In Render dashboard, go to "Static Sites"
   - Create a new static site
   - Connect your repository
   - Set build command: `npm install && npm run build` (if needed)
   - Set publish directory: `static`

2. **Update Application URLs:**
   Ensure your application points to the correct Render URLs:
   ```python
   UPDATE_CHECK_URL = "https://stock-project-nnei.onrender.com/static/version.json"
   UPDATE_DOWNLOAD_URL = "https://stock-project-nnei.onrender.com/static/main.exe"
   ```

### Monitoring and Maintenance
- Monitor your backend service in the Render dashboard
- Set up automatic deployments from your main branch
- Configure health checks for your backend service
- Set up logging and error tracking
- Regularly backup your database

## Error Handling

The script includes comprehensive error handling for:
- Missing files
- Invalid version formats
- File permission issues
- JSON creation/update failures

## Requirements

- Python 3.x
- No external dependencies required

## File Structure

- `update_version.py`: Main script containing version update functionality
- `main.py`: Your application file containing the `CURRENT_VERSION` variable
- `version.json`: Generated file containing the latest version information

## Notes

- The script increments only the minor version number (e.g., 1.0 → 1.1)
- Version format must follow the pattern: `CURRENT_VERSION = "X.Y"`
- The script preserves any comments or formatting in the version line 