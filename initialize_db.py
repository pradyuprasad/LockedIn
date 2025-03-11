from database_manager import DatabaseManager

def main():
    """Initialize the database using the DatabaseManager"""
    db_manager = DatabaseManager()
    db_manager.setup_database()

if __name__ == "__main__":
    main()
