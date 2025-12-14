# Database connection helper for Chinook Music Store
# Uses pyodbc to connect to SQL Server

import pyodbc
import pandas as pd
from contextlib import contextmanager

# Connection configuration
SERVER = r'AMD-PC\SQLEXPRESS'
DATABASE = 'Chinook'
DRIVER = '{ODBC Driver 17 for SQL Server}'

def get_connection_string():
    """Get the connection string for SQL Server."""
    return f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'

@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = pyodbc.connect(get_connection_string())
        yield conn
    finally:
        if conn:
            conn.close()

def execute_query(query, params=None):
    """Execute a SELECT query and return results as DataFrame."""
    with get_connection() as conn:
        if params:
            return pd.read_sql(query, conn, params=params)
        return pd.read_sql(query, conn)

def execute_non_query(query, params=None):
    """Execute INSERT/UPDATE/DELETE query."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.rowcount

def execute_procedure(proc_name, params=None, fetch_results=True):
    """Execute a stored procedure."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if params:
            # Build parameter placeholders
            placeholders = ', '.join(['?' for _ in params])
            query = f"EXEC {proc_name} {placeholders}"
            cursor.execute(query, params)
        else:
            cursor.execute(f"EXEC {proc_name}")
        
        conn.commit()
        
        if fetch_results:
            try:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                return pd.DataFrame.from_records(rows, columns=columns)
            except:
                return None
        return None

def execute_procedure_with_output(proc_name, input_params, output_param_name):
    """Execute a stored procedure with OUTPUT parameter."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Build the query with output parameter
        param_list = []
        for key, value in input_params.items():
            if isinstance(value, str):
                param_list.append(f"@{key} = N'{value}'")
            elif value is None:
                param_list.append(f"@{key} = NULL")
            else:
                param_list.append(f"@{key} = {value}")
        
        param_list.append(f"@{output_param_name} = @out OUTPUT")
        
        query = f"""
            DECLARE @out INT;
            EXEC {proc_name} {', '.join(param_list)};
            SELECT @out AS {output_param_name};
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        conn.commit()
        
        return result[0] if result else None

def test_connection():
    """Test the database connection."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            return True, version
    except Exception as e:
        return False, str(e)


# Quick reference data functions
def get_all_artists():
    """Get all artists for dropdowns."""
    return execute_query("SELECT ArtistId, Name FROM Artist ORDER BY Name")

def get_all_albums():
    """Get all albums with artist names."""
    return execute_query("""
        SELECT a.AlbumId, a.Title, ar.Name AS Artist, ar.ArtistId
        FROM Album a
        INNER JOIN Artist ar ON a.ArtistId = ar.ArtistId
        ORDER BY a.Title
    """)

def get_all_genres():
    """Get all genres for dropdowns."""
    return execute_query("SELECT GenreId, Name FROM Genre ORDER BY Name")

def get_all_media_types():
    """Get all media types."""
    return execute_query("SELECT MediaTypeId, Name FROM MediaType ORDER BY Name")

def get_all_customers():
    """Get all customers."""
    return execute_query("""
        SELECT CustomerId, FirstName + ' ' + LastName AS Name, Email, Country
        FROM Customer
        ORDER BY LastName, FirstName
    """)

def get_all_employees():
    """Get all employees."""
    return execute_query("""
        SELECT EmployeeId, FirstName + ' ' + LastName AS Name, Title
        FROM Employee
        ORDER BY LastName, FirstName
    """)

def get_tracks(search_term=None, genre_id=None, limit=100):
    """Get tracks with optional filters."""
    query = """
        SELECT TOP (?) t.TrackId, t.Name, a.Title AS Album, ar.Name AS Artist,
               g.Name AS Genre, t.Milliseconds / 1000 AS Seconds, t.UnitPrice
        FROM Track t
        INNER JOIN Album a ON t.AlbumId = a.AlbumId
        INNER JOIN Artist ar ON a.ArtistId = ar.ArtistId
        INNER JOIN Genre g ON t.GenreId = g.GenreId
        WHERE 1=1
    """
    params = [limit]
    
    if search_term:
        query += " AND (t.Name LIKE ? OR ar.Name LIKE ? OR a.Title LIKE ?)"
        search = f'%{search_term}%'
        params.extend([search, search, search])
    
    if genre_id:
        query += " AND t.GenreId = ?"
        params.append(genre_id)
    
    query += " ORDER BY t.Name"
    
    return execute_query(query, params)
