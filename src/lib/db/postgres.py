"""
PostgreSQL database utility module.

This module provides reusable functions for connecting to and interacting with
PostgreSQL databases. It follows the recurring pattern used across projects.

Usage:
    from lib.db.postgres import open_connection, close_connection, execute_query

    open_connection()
    results = execute_query("SELECT * FROM users", is_select_query=True)
    close_connection()
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env.local
load_dotenv(find_dotenv('.env.local'))

# Global connection object
_connection = None


def create_connection(db_name, user, password, host, port):
    """
    Create a connection to the PostgreSQL database.

    Args:
        db_name (str): Database name
        user (str): Database user
        password (str): Database password
        host (str): Database host
        port (str): Database port

    Returns:
        psycopg2.connection: Database connection object or None if failed
    """
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        print("Connection to the database successful")
    except psycopg2.Error as e:
        print(f"The error '{e}' occurred")
    return connection


def open_connection():
    """
    Open a database connection using environment variables.

    Reads database credentials from environment variables prefixed with DB_SERVICE_PREFIX.
    Expected env vars:
        - DB_SERVICE_PREFIX
        - {PREFIX}_PG_DB_NAME
        - {PREFIX}_PG_DB_USER
        - {PREFIX}_PG_DB_PASSWORD
        - {PREFIX}_PG_DB_HOST
        - {PREFIX}_PG_DB_PORT

    Returns:
        bool: True if connection successful, False otherwise
    """
    global _connection

    service_prefix = os.getenv('DB_SERVICE_PREFIX')
    if not service_prefix:
        print('Error: DB_SERVICE_PREFIX not set in environment')
        return False

    dbname = os.getenv(f'{service_prefix}_PG_DB_NAME')
    user = os.getenv(f'{service_prefix}_PG_DB_USER')
    password = os.getenv(f'{service_prefix}_PG_DB_PASSWORD')
    host = os.getenv(f'{service_prefix}_PG_DB_HOST')
    port = os.getenv(f'{service_prefix}_PG_DB_PORT')

    _connection = create_connection(dbname, user, password, host, port)

    if _connection:
        return True
    else:
        print('Error opening connection')
        return False


def close_connection():
    """Close the global database connection."""
    global _connection
    if _connection:
        _connection.close()
        print("Connection closed")


def insert_record(record, schema_and_table, inserted_columns):
    """
    Insert a single record into the database.

    Args:
        record (tuple): Values to insert
        schema_and_table (str): Table name (e.g., 'public.users' or 'users')
        inserted_columns (list): List of column names

    Returns:
        int: -1 if connection not available, None otherwise
    """
    if not _connection:
        return -1

    inserted_columns_string = ', '.join(inserted_columns)
    values_placeholder_string = ', '.join(['%s' for _ in inserted_columns])
    cursor = _connection.cursor()

    try:
        cursor.execute(f"""
            INSERT INTO {schema_and_table} ({inserted_columns_string})
            VALUES ({values_placeholder_string})
        """, record)
        _connection.commit()
        print("Record inserted successfully")
    except psycopg2.Error as e:
        _connection.rollback()
        print(f"The error '{e}' occurred")


def execute_query(query, params=None, is_select_query=False, is_insert_or_update_query=False):
    """
    Execute a SQL query.

    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters
        is_select_query (bool): If True, returns fetched results
        is_insert_or_update_query (bool): If True, commits the transaction

    Returns:
        list: Query results if is_select_query=True
        int: -1 if connection not available
        None: Otherwise
    """
    if not _connection:
        return -1

    cursor = _connection.cursor()

    try:
        cursor.execute(query, params)

        if is_select_query:
            return cursor.fetchall()

        if is_insert_or_update_query:
            _connection.commit()
            print("Query executed successfully")
    except psycopg2.Error as e:
        _connection.rollback()
        print(f"The error '{e}' occurred")


def insert_multiple_records(records, schema_and_table, inserted_columns, ignore_conflicts=False):
    """
    Insert multiple records into the database efficiently.

    Args:
        records (list): List of tuples containing values to insert
        schema_and_table (str): Table name (e.g., 'public.users' or 'users')
        inserted_columns (list): List of column names
        ignore_conflicts (bool): If True, adds ON CONFLICT DO NOTHING clause

    Returns:
        int: -1 if connection not available, None otherwise
    """
    if not _connection:
        return -1

    inserted_columns_string = ', '.join(inserted_columns)
    cursor = _connection.cursor()

    query_string = f"""
        INSERT INTO {schema_and_table} ({inserted_columns_string})
        VALUES %s
    """

    if ignore_conflicts:
        query_string += " ON CONFLICT DO NOTHING"

    try:
        execute_values(cursor, query_string, records)
        _connection.commit()
        print("Records inserted successfully")
    except psycopg2.Error as e:
        _connection.rollback()
        print(f"The error '{e}' occurred")


def upsert_multiple_records(records, schema_and_table, inserted_columns, conflict_columns, update_columns):
    """
    Upsert multiple records efficiently using ON CONFLICT DO UPDATE.

    Args:
        records (list): List of tuples containing values to insert
        schema_and_table (str): Table name (e.g., 'luma.linkedin_profiles')
        inserted_columns (list): List of all column names for INSERT
        conflict_columns (list): List of columns for conflict detection
        update_columns (list): List of columns to update on conflict

    Returns:
        int: -1 if connection not available, None otherwise
    """
    if not _connection:
        return -1

    inserted_columns_string = ', '.join(inserted_columns)
    conflict_columns_string = ', '.join(conflict_columns)
    cursor = _connection.cursor()

    # Build UPDATE SET clause
    update_set_parts = [f"{col} = EXCLUDED.{col}" for col in update_columns]
    # Add timestamp update
    update_set_parts.append("last_refreshed_at = (extract(epoch FROM now())*1000)::BIGINT")
    update_set_parts.append("_updated_at = (extract(epoch FROM now())*1000)::BIGINT")
    update_set_string = ', '.join(update_set_parts)

    query_string = f"""
        INSERT INTO {schema_and_table} ({inserted_columns_string})
        VALUES %s
        ON CONFLICT ({conflict_columns_string})
        DO UPDATE SET {update_set_string}
    """

    try:
        execute_values(cursor, query_string, records)
        _connection.commit()
        print(f"Successfully upserted {len(records)} records")
    except psycopg2.Error as e:
        _connection.rollback()
        print(f"Upsert error: {e}")
        raise
