import re
import os
import json
import sys

def update_version_in_main_py(version_file="main.py"):
    """Reads main.py, finds the CURRENT_VERSION line, increments the minor version,
       and writes the changes back to the file.
       Returns the new version string or None on failure.
    """
    try:
        if not os.path.exists(version_file):
            print(f"Error: File not found: {version_file}")
            return None

        with open(version_file, 'r') as f:
            lines = f.readlines()

        new_lines = []
        current_version = None
        version_updated = False

        # Regex to find the line like: CURRENT_VERSION = "1.0"
        # It captures the prefix, the version string, and the suffix (like comments)
        version_regex = re.compile(r'^(CURRENT_VERSION\s*=\s*)"(\d+)\.(\d+)"(.*)$')

        for line in lines:
            match = version_regex.match(line)
            if match:
                prefix = match.group(1)
                major_str = match.group(2)
                minor_str = match.group(3)
                suffix = match.group(4)

                try:
                    major = int(major_str)
                    minor = int(minor_str)
                    new_version_str = f"{major}.{minor + 1}"
                except ValueError:
                    print(f"Warning: Could not parse version string '{major_str}.{minor_str}' as major.minor. Keeping as is.")
                    new_version_str = f"{major_str}.{minor_str}" # Keep old version if parsing fails

                new_line = f'{prefix}"{new_version_str}"{suffix}\n'
                new_lines.append(new_line)
                current_version = new_version_str
                version_updated = True
                print(f"Updated version from {major_str}.{minor_str} to {new_version_str} in {version_file}")
            else:
                new_lines.append(line)

        if not version_updated:
            print(f"Error: Could not find CURRENT_VERSION line in {version_file}")
            return None # Indicate failure

        # Write the modified content back to the file
        with open(version_file, 'w') as f:
            f.writelines(new_lines)

        return current_version # Return the new version

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def create_version_json(version, output_file="version.json"):
    """Creates or updates the version.json file with the latest version."""
    try:
        version_data = {
            "latest_version": version
        }
        with open(output_file, 'w') as f:
            json.dump(version_data, f, indent=4)
        print(f"Created or updated {output_file} with version {version}")
        return True
    except Exception as e:
        print(f"Error creating or updating {output_file}: {e}")
        return False

if __name__ == "__main__":
    # This block demonstrates how you would use the functions.
    # In a real build script, you might call these functions
    # before your PyInstaller command.

    print("Attempting to update version in main.py...")
    new_version = update_version_in_main_py()

    if new_version:
        print(f"Successfully updated version to: {new_version}")
        print("Creating/updating version.json...")
        if create_version_json(new_version):
            print("version.json created/updated successfully.")
            print("\nNext Steps:")
            print("1. Run PyInstaller on your updated main.py to build the new .exe.")
            print("   Example: pyinstaller --onefile main.py")
            print("2. Upload the newly generated main.exe from the 'dist' folder to your Render static assets.")
            print("3. Upload the newly created/updated version.json to your Render static assets.")
        else:
             print("Failed to create/update version.json.")
    else:
        print("Version update process failed.")
        sys.exit(1) # Exit with an error code if version update failed