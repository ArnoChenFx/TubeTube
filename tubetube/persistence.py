import os
import sqlite3
import json
import logging
import threading


class DataPersistence:
    """
    Handles persistent storage of download data including task list, status, and progress using SQLite.
    """

    def __init__(self, config_folder="/config"):
        self.config_folder = config_folder
        self.db_path = os.path.join(self.config_folder, "downloads.db")
        self.lock = threading.Lock()
        self.conn = None

        # Create config folder if it doesn't exist
        os.makedirs(self.config_folder, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create tables if they don't exist"""
        try:
            # Create a persistent connection
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")

            with self.lock:
                cursor = self.conn.cursor()

                # Create downloads table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY,
                    video_identifier TEXT,
                    title TEXT,
                    url TEXT,
                    status TEXT,
                    progress TEXT,
                    folder_name TEXT,
                    audio_only INTEGER,
                    skipped INTEGER,
                    download_settings TEXT
                )
                """)

                self.conn.commit()
                logging.info(f"SQLite database initialized at {self.db_path}")

        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            # If there was an error, make sure to close the connection
            if self.conn:
                try:
                    self.conn.close()
                    self.conn = None
                except:
                    pass
            raise

    def __del__(self):
        """Ensure the database connection is closed when the object is deleted"""
        self.close()

    def close(self):
        """Close the database connection"""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                logging.info("SQLite database connection closed")
            except Exception as e:
                logging.error(f"Error closing database connection: {e}")

    def save_downloads(self, all_items):
        """Save download items to SQLite database"""
        try:
            with self.lock:
                if not self.conn:
                    self._init_db()

                cursor = self.conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Clear existing data
                cursor.execute("DELETE FROM downloads")

                # Insert all items
                for item_id, item in all_items.items():
                    # Convert download_settings dict to JSON string
                    download_settings_json = json.dumps(
                        item.get("download_settings", {})
                    )

                    cursor.execute(
                        """
                    INSERT INTO downloads (
                        id, video_identifier, title, url, status, progress, 
                        folder_name, audio_only, skipped, download_settings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            item.get("id"),
                            item.get("video_identifier"),
                            item.get("title"),
                            item.get("url"),
                            item.get("status"),
                            item.get("progress"),
                            item.get("folder_name"),
                            1 if item.get("audio_only", False) else 0,
                            1 if item.get("skipped", False) else 0,
                            download_settings_json,
                        ),
                    )

                # Commit transaction
                self.conn.commit()
                logging.info(
                    f"Saved {len(all_items)} download items to SQLite database"
                )

        except Exception as e:
            logging.error(f"Error saving download data to SQLite: {e}")
            # Try to reconnect if the connection was lost
            try:
                if self.conn:
                    self.conn.close()
                self._init_db()
            except:
                pass

    def load_downloads(self):
        """Load download items from SQLite database"""
        all_items = {}

        try:
            with self.lock:
                if not self.conn:
                    self._init_db()

                # Set row factory to return rows as dictionaries
                self.conn.row_factory = sqlite3.Row
                cursor = self.conn.cursor()

                cursor.execute("SELECT * FROM downloads")
                rows = cursor.fetchall()

                for row in rows:
                    row_dict = dict(row)
                    item_id = row_dict["id"]

                    # Convert SQLite INTEGER to Python bool
                    row_dict["audio_only"] = bool(row_dict["audio_only"])
                    row_dict["skipped"] = bool(row_dict["skipped"])

                    # Parse download_settings JSON
                    try:
                        row_dict["download_settings"] = json.loads(
                            row_dict["download_settings"]
                        )
                    except:
                        row_dict["download_settings"] = {}

                    all_items[item_id] = row_dict

                logging.info(
                    f"Loaded {len(all_items)} download items from SQLite database"
                )
                return all_items

        except Exception as e:
            logging.error(f"Error loading download data from SQLite: {e}")
            # Try to reconnect if the connection was lost
            try:
                if self.conn:
                    self.conn.close()
                self._init_db()
            except:
                pass
            return {}

    def update_item(self, item_id, status=None):
        """Update a specific item's status in the database"""
        try:
            with self.lock:
                if not self.conn:
                    self._init_db()

                cursor = self.conn.cursor()

                if status is not None:
                    cursor.execute(
                        "UPDATE downloads SET status = ? WHERE id = ?",
                        (status, item_id),
                    )
                    self.conn.commit()

                    if cursor.rowcount > 0:
                        logging.debug(
                            f"Updated status of item {item_id} to '{status}' in SQLite database"
                        )
                        return True
                    else:
                        logging.warning(
                            f"Item {item_id} not found in database for status update"
                        )
                        return False

                return False

        except Exception as e:
            logging.error(f"Error updating item {item_id} status in SQLite: {e}")
            # Try to reconnect if the connection was lost
            try:
                if self.conn:
                    self.conn.close()
                self._init_db()
            except:
                pass
            return False

    def delete_item(self, item_id):
        """Delete a specific item from the database"""
        try:
            with self.lock:
                if not self.conn:
                    self._init_db()

                cursor = self.conn.cursor()

                cursor.execute("DELETE FROM downloads WHERE id = ?", (item_id,))
                self.conn.commit()

                if cursor.rowcount > 0:
                    logging.info(f"Deleted item {item_id} from SQLite database")
                    return True
                else:
                    logging.warning(
                        f"Item {item_id} not found in database for deletion"
                    )
                    return False

        except Exception as e:
            logging.error(f"Error deleting item {item_id} from SQLite: {e}")
            # Try to reconnect if the connection was lost
            try:
                if self.conn:
                    self.conn.close()
                self._init_db()
            except:
                pass
            return False
