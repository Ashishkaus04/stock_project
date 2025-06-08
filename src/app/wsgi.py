from .api.app import app

# This is the application variable that gunicorn expects
application = app

if __name__ == "__main__":
    application.run() 