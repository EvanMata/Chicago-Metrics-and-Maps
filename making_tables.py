import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def main():
	#Database filepath
    database = "/home/student/cs122-project/Crime_Weights2.db"
 
    sql_create_IUCR_table = """ 
    		CREATE TABLE IF NOT EXISTS IUCR (
                IUCR_code integer PRIMARY KEY,
                felony_class integer NOT NULL,
                FOREIGN KEY (felony_class) REFERENCES felonies (felony_id)
            ); """
 
    sql_create_felonies_table = """
    		CREATE TABLE IF NOT EXISTS felonies (
                felony_id integer PRIMARY KEY,
                min_time integer NOT NULL,
                max_time integer,
                mean_time integer,
                min_charge integer NOT NULL,
                max_charge integer,
                mean_charge integer
            );"""
 
    # create a database connection
    conn = create_connection(database)
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_felonies_table)
        # create tasks table
        create_table(conn, sql_create_IUCR_table)
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()