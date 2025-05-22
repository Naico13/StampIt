import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# This file will manage database operations.
# It will include functions for connecting to the database,
# creating tables, inserting stamp data, and querying information.

# Define the base directory of the application to resolve paths correctly
APP_BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = APP_BASE_DIR / "data" / "database"
DATABASE_NAME = "stamps_collection.db"
DATABASE_PATH = DATABASE_DIR / DATABASE_NAME

def _get_db_connection():
    """Establishes and returns a database connection."""
    try:
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Access columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise # Re-raise the exception to be handled by the caller

def initialize_database():
    """
    Ensures the database directory exists, connects to the SQLite database
    (creating it if it doesn't exist), and creates the 'stamps' table
    if it doesn't already exist.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stamps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_image_ref TEXT,
            detected_stamp_image_path TEXT UNIQUE NOT NULL,
            search_keywords TEXT,
            country TEXT,
            title_suggestion TEXT,
            estimated_price_range TEXT,
            history_notes TEXT,
            source_urls TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        print(f"Database initialized successfully at {DATABASE_PATH}")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def add_stamp_record(stamp_data: dict) -> int | None:
    """
    Adds a new stamp record to the 'stamps' table.

    Args:
        stamp_data: A dictionary containing the stamp data. Keys should
                    correspond to the table columns. 'source_urls'
                    should be a list of strings, which will be JSON encoded.

    Returns:
        The id of the newly inserted row, or None if insertion fails.
    """
    # Ensure all required fields are present, especially the NOT NULL one
    if "detected_stamp_image_path" not in stamp_data:
        print("Error: 'detected_stamp_image_path' is required.")
        return None

    # Convert list of URLs to JSON string if present
    if "source_urls" in stamp_data and isinstance(stamp_data["source_urls"], list):
        stamp_data["source_urls"] = json.dumps(stamp_data["source_urls"])

    # Default values for optional fields if not provided
    fields = [
        "original_image_ref", "detected_stamp_image_path", "search_keywords",
        "country", "title_suggestion", "estimated_price_range",
        "history_notes", "source_urls"
    ]
    
    # Constructing the query dynamically to handle missing optional fields
    # All fields present in `stamp_data` will be used.
    query_fields = [field for field in fields if field in stamp_data]
    query_placeholders = ", ".join(["?"] * len(query_fields))
    query_columns = ", ".join(query_fields)
    
    sql = f"INSERT INTO stamps ({query_columns}) VALUES ({query_placeholders})"
    values = tuple(stamp_data[field] for field in query_fields)

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        last_id = cursor.lastrowid
        print(f"Record added successfully with ID: {last_id}")
        return last_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding record: {e}. 'detected_stamp_image_path' must be unique.")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding record: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_stamp_by_image_path(image_path: str) -> dict | None:
    """
    Retrieves a stamp record by its 'detected_stamp_image_path'.

    Args:
        image_path: The path to the detected stamp image.

    Returns:
        A dictionary representing the stamp record if found, otherwise None.
        'source_urls' will be a list (parsed from JSON).
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stamps WHERE detected_stamp_image_path = ?", (image_path,))
        record = cursor.fetchone()

        if record:
            record_dict = dict(record)
            if record_dict.get("source_urls"):
                try:
                    record_dict["source_urls"] = json.loads(record_dict["source_urls"])
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse source_urls JSON for {image_path}")
                    record_dict["source_urls"] = [] # Default to empty list on error
            return record_dict
        return None
    except sqlite3.Error as e:
        print(f"Database error retrieving record by image path: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_all_stamps() -> list[dict]:
    """
    Retrieves all records from the 'stamps' table.

    Returns:
        A list of dictionaries, where each dictionary represents a stamp record.
        'source_urls' will be a list (parsed from JSON).
        Returns an empty list if the table is empty or an error occurs.
    """
    records = []
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stamps ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        for row in rows:
            record_dict = dict(row)
            if record_dict.get("source_urls"):
                try:
                    record_dict["source_urls"] = json.loads(record_dict["source_urls"])
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse source_urls JSON for ID {record_dict.get('id')}")
                    record_dict["source_urls"] = [] # Default to empty list on error
            records.append(record_dict)
        return records
    except sqlite3.Error as e:
        print(f"Database error retrieving all records: {e}")
        return [] # Return empty list on error
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main_test():
    """
    Demonstrates the usage of the database utility functions.
    """
    print("--- Testing Database Utilities ---")

    # 0. Clean up old database file for a fresh test run (optional)
    if DATABASE_PATH.exists():
        try:
            DATABASE_PATH.unlink()
            print(f"Removed old database file: {DATABASE_PATH}")
        except OSError as e:
            print(f"Error removing old database file: {e}")


    # 1. Initialize Database
    print("\n1. Initializing Database...")
    initialize_database()

    # 2. Add Sample Stamp Records
    #    To manually test the GUI with specific data:
    #    a) Run image_processing.py's main_test() to get detected stamp paths.
    #    b) Copy one of those paths (e.g., 'stamp_app/data/detected_stamps/test_stamp_sheet_stamp_xxxxxxxx.png').
    #    c) Paste it as the value for 'detected_stamp_image_path' in the `realistic_sample_data` below.
    #    d) Run this db_utils.py script to populate the database.
    #    e) Then run main.py, open the original 'test_stamp_sheet.png', detect stamps, and click the one you added data for.
    print("\n2. Adding Sample Stamp Records...")
    
    # IMPORTANT: For manual end-to-end testing, replace the 'detected_stamp_image_path'
    # below with an actual path output by image_processing.py's main_test().
    # Make sure the image file referenced (e.g., 'test_stamp_sheet_stamp_xxxxxxxx.png')
    # actually exists in 'stamp_app/data/detected_stamps/'.
    realistic_sample_data = {
        'original_image_ref': 'stamp_app/data/uploaded_images/test_stamp_sheet.png', # Path to the sheet image
        'detected_stamp_image_path': 'stamp_app/data/detected_stamps/test_stamp_sheet_stamp_xxxxxxxx.png', # CRITICAL: REPLACE THIS
        'search_keywords': 'Canada 1950s Queen Elizabeth',
        'country': 'Canada',
        'title_suggestion': 'Queen Elizabeth II 5c Blue',
        'estimated_price_range': '$0.50 - $1.50',
        'history_notes': 'Common definitive stamp from the mid-century. Part of a series of definitive stamps issued during the early reign of Queen Elizabeth II. Often used for standard postage rates.',
        'source_urls': ['http://example.com/stamp_info/canada_qe2_5c', 'http://anotherstampsite.com/qe2_blue']
    }
    print(f"\nAttempting to add realistic sample data. \n"
          f"IMPORTANT: Ensure 'detected_stamp_image_path' ('{realistic_sample_data['detected_stamp_image_path']}') \n"
          f"is a valid path from image_processing.py's output for the test to work.\n")
    
    record_id_1 = add_stamp_record(realistic_sample_data)
    if record_id_1 is None:
        print(f"WARNING: Could not add the realistic sample data. "
              f"This might be due to the 'detected_stamp_image_path' not being unique (if already added) "
              f"or not being a valid file path that the application expects to exist. "
              f"For the test, this path should correspond to a cropped stamp image.")

    # Add a couple of other generic records for variety
    sample_data_2 = {
        "original_image_ref": "/path/to/album_page_2.jpg", # Generic placeholder
        "detected_stamp_image_path": "/data/detected_stamps/generic_stamp_B_002.png", # Generic placeholder
        "search_keywords": "USA Eagle Stamp",
        "country": "USA",
        "title_suggestion": "Eagle Series - 10c Black",
        "estimated_price_range": "$0.25 - $0.75",
        "history_notes": "A common US stamp featuring an eagle.",
        "source_urls": ["http://stamps.example.com/us/eagle_10c"]
    }
    record_id_2 = add_stamp_record(sample_data_2)
    
    sample_data_3 = { # Minimal data for another generic record
        "detected_stamp_image_path": "/data/detected_stamps/generic_stamp_C_003.png", # Generic placeholder
        "search_keywords": "unknown old German stamp",
    }
    record_id_3 = add_stamp_record(sample_data_3)


    # 3. Retrieve the Specific Realistic Stamp (if added)
    print(f"\n3. Retrieving the Specific Realistic Stamp ('{realistic_sample_data['detected_stamp_image_path']}')...")
    if record_id_1: # Check if the realistic sample was successfully added
        retrieved_stamp = get_stamp_by_image_path(realistic_sample_data['detected_stamp_image_path'])
        if retrieved_stamp:
            print("Retrieved Realistic Stamp:")
            for key, value in retrieved_stamp.items():
                print(f"  {key}: {value}")
        else:
            print(f"Realistic stamp with path '{realistic_sample_data['detected_stamp_image_path']}' not found. This might be expected if it wasn't added.")
    else:
        print(f"Realistic stamp was not added (record_id_1 is None), so not attempting to retrieve it by its specific path.")


    # 4. Retrieve All Stamps
    print("\n4. Retrieving All Stamps (to show what's in the DB)...")
    all_stamps = get_all_stamps()
    if all_stamps:
        print(f"Found {len(all_stamps)} stamps:")
        for i, stamp in enumerate(all_stamps):
            print(f"\n--- Stamp {i+1} (ID: {stamp.get('id')}) ---")
            for key, value in stamp.items():
                print(f"  {key}: {value}")
    else:
        print("No stamps found in the database.")

    # 5. Demonstrate Duplicate detected_stamp_image_path Handling (using the realistic path if it was added)
    print("\n5. Attempting to Add Duplicate Stamp Image Path...")
    path_to_try_duplicating = realistic_sample_data['detected_stamp_image_path'] if record_id_1 else "/data/detected_stamps/generic_stamp_B_002.png"
    
    duplicate_data = {
        "original_image_ref": "/path/to/album_page_1_again.jpg",
        "detected_stamp_image_path": path_to_try_duplicating, # Attempt to duplicate
        "search_keywords": "another canada 1967 5 cent", # Content doesn't matter as much as path
        "country": "Canada",
        "title_suggestion": "Canada 5 Cent 1967 - Second Attempt",
    }
    print(f"Attempting to add a record with duplicate path: {path_to_try_duplicating}")
    duplicate_id = add_stamp_record(duplicate_data)
    if duplicate_id is None:
        print("Successfully handled duplicate: Insertion was prevented as expected.")
    else:
        print(f"Error: Duplicate insertion was not prevented for path {path_to_try_duplicating}. Record ID: {duplicate_id}")

    print("\n--- Database Utilities Test Complete ---")
    print("Remember to check the 'stamp_app/data/database/stamps_collection.db' file if you want to inspect the DB directly.")


if __name__ == "__main__":
    main_test()
