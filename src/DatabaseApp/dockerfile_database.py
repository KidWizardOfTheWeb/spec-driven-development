#!/usr/bin/env python3
"""
Dockerfile Database Manager

This module provides a database interface for storing and retrieving Dockerfiles
with timestamp tracking using SQLite3.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import pytz  # For timezone handling


class DockerfileDatabase:
    """
    Database manager for storing and retrieving Dockerfiles.
    
    Stores Dockerfiles with their content, name, and creation timestamp.
    Uses UTC timezone for consistency across different systems.
    """
    
    # TIMEZONE CONFIGURATION
    # Change this parameter to use a different timezone if needed
    # Example: pytz.timezone('America/New_York') or pytz.timezone('Europe/London')
    TIMEZONE = pytz.UTC  # Currently using UTC for consistency
    
    def __init__(self, db_path: str = "dockerfiles.db"):
        """
        Initialize the database connection and create tables if needed.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish connection to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        """Create the dockerfiles table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dockerfiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_date DATE NOT NULL,
                created_time TIME NOT NULL,
                created_timestamp TIMESTAMP NOT NULL,
                timezone TEXT NOT NULL,
                UNIQUE(name, created_date, created_time)
            )
        ''')
        self.conn.commit()
        
        # Create indexes for faster queries
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_date 
            ON dockerfiles(created_date)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_name 
            ON dockerfiles(name)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_name_date 
            ON dockerfiles(name, created_date)
        ''')
        self.conn.commit()
    
    def add_dockerfile(self, name: str, content: str) -> Dict[str, str]:
        """
        Add a Dockerfile to the database with current timestamp.
        
        Args:
            name: Name of the Dockerfile (e.g., 'Dockerfile.flask')
            content: Full content of the Dockerfile
            
        Returns:
            Dictionary with stored information
            
        Raises:
            sqlite3.IntegrityError: If duplicate entry exists
        """
        # Get current timestamp in configured timezone
        now = datetime.now(self.TIMEZONE)
        created_date = now.date().isoformat()
        created_time = now.time().isoformat()
        created_timestamp = now.isoformat()
        timezone_name = str(self.TIMEZONE)
        
        try:
            # Had to add this due to the test case allowing empty names from claude's original code, failing a test case.
            if name is None or name == "":
                # Note: we will NOT allow empty names in our database.
                raise sqlite3.DataError

            self.cursor.execute('''
                INSERT INTO dockerfiles 
                (name, content, created_date, created_time, created_timestamp, timezone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, content, created_date, created_time, created_timestamp, timezone_name))
            
            self.conn.commit()
            
            # Print confirmation
            print(f"\n✓ Dockerfile stored successfully!")
            print(f"  Name: {name}")
            print(f"  Date: {created_date}")
            print(f"  Time: {created_time}")
            print(f"  Timezone: {timezone_name}")
            
            return {
                'id': self.cursor.lastrowid,
                'name': name,
                'created_date': created_date,
                'created_time': created_time,
                'created_timestamp': created_timestamp,
                'timezone': timezone_name
            }
        except sqlite3.DataError as e:
            print(f"\n✗ Error: Unnamed Dockerfile entry")
            print(f"  A Dockerfile with no name cannot be entered into the database.")
            raise e
        except sqlite3.IntegrityError as e:
            print(f"\n✗ Error: Duplicate Dockerfile entry")
            print(f"  A Dockerfile with name '{name}' already exists at this exact timestamp")
            raise e
    
    def add_dockerfile_from_file(self, filepath: str) -> Dict[str, str]:
        """
        Read a Dockerfile from disk and add it to the database.
        
        Args:
            filepath: Path to the Dockerfile
            
        Returns:
            Dictionary with stored information
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Dockerfile not found: {filepath}")
        
        # Read content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use filename as the name
        name = filepath.name
        
        return self.add_dockerfile(name, content)
    
    def get_dockerfiles_by_date(self, date: str) -> List[Dict]:
        """
        Retrieve all Dockerfiles stored on a specific date.
        
        Args:
            date: Date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of dictionaries containing Dockerfile information
        """
        self.cursor.execute('''
            SELECT id, name, content, created_date, created_time, 
                   created_timestamp, timezone
            FROM dockerfiles
            WHERE created_date = ?
            ORDER BY created_time ASC
        ''', (date,))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row['id'],
                'name': row['name'],
                'content': row['content'],
                'created_date': row['created_date'],
                'created_time': row['created_time'],
                'created_timestamp': row['created_timestamp'],
                'timezone': row['timezone']
            })
        
        return results
    
    def get_dockerfile_by_date_and_name(
        self, 
        date: str, 
        name: str
    ) -> Optional[Dict]:
        """
        Retrieve a specific Dockerfile by date and name.
        
        Args:
            date: Date in ISO format (YYYY-MM-DD)
            name: Name of the Dockerfile
            
        Returns:
            Dictionary with Dockerfile information or None if not found
        """
        self.cursor.execute('''
            SELECT id, name, content, created_date, created_time, 
                   created_timestamp, timezone
            FROM dockerfiles
            WHERE created_date = ? AND name = ?
            ORDER BY created_time DESC
            LIMIT 1
        ''', (date, name))
        
        row = self.cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'content': row['content'],
                'created_date': row['created_date'],
                'created_time': row['created_time'],
                'created_timestamp': row['created_timestamp'],
                'timezone': row['timezone']
            }
        
        return None
    
    def get_all_dockerfiles(self) -> List[Dict]:
        """
        Retrieve all Dockerfiles from the database.
        
        Returns:
            List of all Dockerfile entries
        """
        self.cursor.execute('''
            SELECT id, name, content, created_date, created_time, 
                   created_timestamp, timezone
            FROM dockerfiles
            ORDER BY created_timestamp DESC
        ''')
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row['id'],
                'name': row['name'],
                'content': row['content'],
                'created_date': row['created_date'],
                'created_time': row['created_time'],
                'created_timestamp': row['created_timestamp'],
                'timezone': row['timezone']
            })
        
        return results
    
    def get_unique_dates(self) -> List[str]:
        """
        Get all unique dates that have Dockerfiles stored.
        
        Returns:
            List of dates in ISO format
        """
        self.cursor.execute('''
            SELECT DISTINCT created_date
            FROM dockerfiles
            ORDER BY created_date DESC
        ''')
        
        return [row['created_date'] for row in self.cursor.fetchall()]
    
    def get_dockerfile_names_by_date(self, date: str) -> List[str]:
        """
        Get all unique Dockerfile names for a specific date.
        
        Args:
            date: Date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of Dockerfile names
        """
        self.cursor.execute('''
            SELECT DISTINCT name
            FROM dockerfiles
            WHERE created_date = ?
            ORDER BY name ASC
        ''', (date,))
        
        return [row['name'] for row in self.cursor.fetchall()]
    
    def delete_dockerfile(self, dockerfile_id: int) -> bool:
        """
        Delete a Dockerfile by its ID.
        
        Args:
            dockerfile_id: The ID of the Dockerfile to delete
            
        Returns:
            True if deleted, False if not found
        """
        self.cursor.execute('''
            DELETE FROM dockerfiles
            WHERE id = ?
        ''', (dockerfile_id,))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        self.cursor.execute('SELECT COUNT(*) as total FROM dockerfiles')
        total = self.cursor.fetchone()['total']
        
        self.cursor.execute('SELECT COUNT(DISTINCT created_date) as dates FROM dockerfiles')
        unique_dates = self.cursor.fetchone()['dates']
        
        self.cursor.execute('SELECT COUNT(DISTINCT name) as names FROM dockerfiles')
        unique_names = self.cursor.fetchone()['names']
        
        return {
            'total_dockerfiles': total,
            'unique_dates': unique_dates,
            'unique_names': unique_names
        }
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def interactive_mode():
    """Run the database manager in interactive mode."""
    print("="*70)
    print("Dockerfile Database Manager")
    print("="*70)
    
    db = DockerfileDatabase()
    
    try:
        while True:
            print("\n" + "="*70)
            print("Options:")
            print("  1. Add Dockerfile to database")
            print("  2. Retrieve Dockerfiles by date")
            print("  3. Retrieve specific Dockerfile by date and name")
            print("  4. View all stored dates")
            print("  5. View database statistics")
            print("  6. View all Dockerfiles")
            print("  7. Exit")
            print("="*70)
            
            choice = input("\nSelect an option (1-7): ").strip()
            
            if choice == '1':
                # Add Dockerfile
                # NOTE: changed name from "Dockerfile" to file, to indicate multiple supported textfile types
                # \nAdd Dockerfile to Database
                print("\nAdd file to Database")
                print("-" * 40)
                # Enter path to Dockerfile
                filepath = input("Enter path to file: ").strip()
                
                try:
                    result = db.add_dockerfile_from_file(filepath)
                except FileNotFoundError as e:
                    print(f"\n✗ Error: {e}")
                except sqlite3.IntegrityError:
                    pass  # Error already printed
                except Exception as e:
                    print(f"\n✗ Unexpected error: {e}")
            
            elif choice == '2':
                # Retrieve by date
                print("\nRetrieve Dockerfiles by Date")
                print("-" * 40)
                date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
                
                if not date:
                    date = datetime.now(db.TIMEZONE).date().isoformat()
                
                dockerfiles = db.get_dockerfiles_by_date(date)
                
                if dockerfiles:
                    print(f"\nFound {len(dockerfiles)} Dockerfile(s) on {date}:")
                    for i, df in enumerate(dockerfiles, 1):
                        print(f"\n{i}. {df['name']}")
                        print(f"   Time: {df['created_time']}")
                        print(f"   ID: {df['id']}")
                        print(f"   Preview: {df['content'][:100]}...")
                        # NOTE: allow preview to download as well
                else:
                    print(f"\nNo Dockerfiles found for {date}")
            
            elif choice == '3':
                # Retrieve by date and name
                print("\nRetrieve Specific Dockerfile")
                print("-" * 40)
                date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
                
                if not date:
                    date = datetime.now(db.TIMEZONE).date().isoformat()
                
                name = input("Enter Dockerfile name: ").strip()
                
                dockerfile = db.get_dockerfile_by_date_and_name(date, name)
                
                if dockerfile:
                    print(f"\n✓ Found: {dockerfile['name']}")
                    print(f"  Date: {dockerfile['created_date']}")
                    print(f"  Time: {dockerfile['created_time']}")
                    print(f"  ID: {dockerfile['id']}")
                    print(f"\nContent:\n{'-'*40}")
                    print(dockerfile['content'])
                else:
                    print(f"\n✗ No Dockerfile named '{name}' found for {date}")
            
            elif choice == '4':
                # View all dates
                dates = db.get_unique_dates()
                
                if dates:
                    print(f"\nDates with stored Dockerfiles ({len(dates)}):")
                    for date in dates:
                        count = len(db.get_dockerfiles_by_date(date))
                        print(f"  • {date} ({count} Dockerfile(s))")
                else:
                    print("\nNo Dockerfiles stored yet")
            
            elif choice == '5':
                # Statistics
                stats = db.get_statistics()
                print("\nDatabase Statistics:")
                print("-" * 40)
                print(f"  Total Dockerfiles: {stats['total_dockerfiles']}")
                print(f"  Unique Dates: {stats['unique_dates']}")
                print(f"  Unique Names: {stats['unique_names']}")
            
            elif choice == '6':
                # View all Dockerfiles
                dockerfiles = db.get_all_dockerfiles()
                
                if dockerfiles:
                    print(f"\nAll Dockerfiles ({len(dockerfiles)}):")
                    for i, df in enumerate(dockerfiles, 1):
                        print(f"\n{i}. {df['name']}")
                        print(f"   Date: {df['created_date']} {df['created_time']}")
                        print(f"   ID: {df['id']}")
                else:
                    print("\nNo Dockerfiles stored yet")
            
            elif choice == '7':
                print("\nGoodbye!")
                break
            
            else:
                print("\n✗ Invalid option. Please select 1-7.")
    
    finally:
        db.close()


if __name__ == '__main__':
    interactive_mode()
