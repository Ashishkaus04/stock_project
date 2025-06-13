import os
from sqlalchemy import create_engine, MetaData, Table, inspect, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_neon_connection_url():
    """Get the Neon database connection URL from environment variables."""
    return os.getenv('DATABASE_URL')

def create_sqlite_engine():
    """Create SQLite engine."""
    return create_engine('sqlite:///local_stock_management.db')

def get_all_tables(engine):
    """Get all table names from the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()

def generate_sqlite_models(source_engine, target_engine):
    """Generate SQLite-compatible SQLAlchemy models from the Neon PostgreSQL schema."""
    try:
        # Reflect tables from source (PostgreSQL)
        source_metadata = MetaData()
        source_metadata.reflect(bind=source_engine)

        # Create tables in target (SQLite) using reflected schema
        target_metadata = MetaData()
        for table_name, table in source_metadata.tables.items():
            # Create a new table in SQLite without PostgreSQL-specific syntax
            target_table = Table(table_name, target_metadata)
            for column in table.columns:
                # Remove PostgreSQL-specific defaults and type casts
                col_copy = column.copy()
                # Remove server_default if it contains PostgreSQL-specific syntax
                if col_copy.server_default is not None:
                    default_str = str(col_copy.server_default.arg)
                    if 'nextval' in default_str or '::regclass' in default_str or '::text' in default_str:
                        col_copy.server_default = None
                target_table.append_column(col_copy)
            target_metadata.create_all(target_engine, tables=[target_table], checkfirst=True)

        logger.info("SQLite-compatible models generated successfully!")
    except Exception as e:
        logger.error(f"Error generating SQLite models: {str(e)}")

def main():
    # Get connection URLs
    neon_url = get_neon_connection_url()
    if not neon_url:
        logger.error("DATABASE_URL environment variable not found")
        return

    # Create engines
    source_engine = create_engine(neon_url)
    target_engine = create_sqlite_engine()

    try:
        generate_sqlite_models(source_engine, target_engine)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
    finally:
        source_engine.dispose()
        target_engine.dispose()

if __name__ == "__main__":
    main() 