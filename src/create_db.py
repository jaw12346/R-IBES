"""
Create the database and tables.
"""

import sqlite3
from alive_progress import alive_bar

from conversions import split_camelcase_to_lowercase

SPLITTER = '=' * 100


def create_db():
    """
    Create the database and tables.
    """
    conn = sqlite3.connect('./r-ibes.db')  # DB file is stored outside the src directory
    print(SPLITTER)
    print('***CREATING DATABASE***\n')
    print('Opened database successfully')
    try:
        conn.execute('''CREATE TABLE NAME_DIRECTORY
                            (NAME             TEXT    NOT NULL,
                             DIRECTORY        TEXT    NOT NULL,
                             ENCODING_COUNT   INT     NOT NULL);''')
        print('NAME_DIRECTORY table created successfully')
    except sqlite3.OperationalError as exception:
        if 'already exists' in str(exception):
            print('NAME_DIRECTORY table already exists. No action taken!')
        else:
            raise exception

    try:
        conn.execute('''CREATE TABLE NAME_ENCODING
                            (NAME         TEXT    NOT NULL,
                             ENCODING     BLOB    NOT NULL,
                             FILE_NAME    TEXT    NOT NULL,
                             SOURCE       TEXT    NOT NULL);''')
        print('NAME_ENCODING table created successfully')
    except sqlite3.OperationalError as exception:
        if 'already exists' in str(exception):
            print('NAME_ENCODING table already exists. No action taken!')
        else:
            raise exception

    ontologies_exist = False
    try:
        conn.execute('''CREATE TABLE ONTOLOGIES
                            (ONTOLOGY       TEXT NOT NULL,
                             SPLIT_ONTOLOGY TEXT DEFAULT '');''')
        print('ONTOLOGIES table created successfully')
    except sqlite3.OperationalError as exception:
        if 'already exists' in str(exception):
            print('ONTOLOGIES table already exists. No action taken!')
            ontologies_exist = True
        else:
            raise exception
    print(SPLITTER, '\n')
    if not ontologies_exist:
        fill_ontologies(conn)
    conn.close()


def fill_ontologies(conn):
    """
    Fill the ontology table with the data from mappingbased_objects_en.ttl.
    Data originates from https://downloads.dbpedia.org/current/core/mappingbased_objects_en.ttl.bz2

    :param conn: SQLite3 connection
    :type conn: sqlite3.Connection
    """
    line_count = 18746177  # Number of lines in mappingbased_objects_en.ttl at the time of writing
    i = 0
    try:
        print(SPLITTER)
        print('***FILLING ONTOLOGIES TABLE***\n')
        print('Attempting to open mappingbased_objects_en.ttl')
        try:
            with open('./mappingbased_objects_en.ttl', 'r') as file:
                print('Successfully opened mappingbased_objects_en.ttl')
                with alive_bar(line_count, force_tty=True) as bar:  # Progress bar, force_tty=True for PyCharm
                    for line in file:
                        if line.startswith('<http'):  # Don't include non-link lines
                            # Extract the resource, ontology and target uri from the line
                            # Example: <http://dbpedia.org/resource/Barack_Obama> <http://dbpedia.org/ontology/residence> <http://dbpedia.org/resource/White_House>
                            # --> http://dbpedia.org/resource/Barack_Obama || residence || http://dbpedia.org/resource/White_House
                            ontology_uri = line.split(' ')[1][1:-1]
                            if '/ontology/' in ontology_uri:  # Some links are not ontologies (w3)
                                ontology = ontology_uri.split('/')[-1]
                                conn.execute(f"INSERT INTO ONTOLOGIES (ONTOLOGY) VALUES (\"{ontology}\");")
                        if i % 100000 == 0:
                            # Needed to prevent the database from locking up
                            conn.commit()
                        i += 1
                        bar()  # Update progress bar
                # Make sure the last changes are committed
                conn.commit()
                print('ONTOLOGIES table filled successfully')

                # Remove duplicate ontologies from the ONTOLOGY column
                print('Removing duplicates from ONTOLOGIES table...')
                print('\tThis may take a while depending on the number of duplicates!')
                remove_duplicates(conn)
                print('Duplicates removed successfully')

                # Split camelCase ontologies into distinct lowercase words
                print('Splitting camelCase ontologies...')
                split_ontologies(conn)
                print('CamelCase ontologies split successfully')

                print(SPLITTER, '\n')
        except FileNotFoundError as exception:
            print("Error opening mappingbased_objects_en.ttl.\n"
                  "Please make sure it's located in the project root directory.")
            raise exception
    except sqlite3.OperationalError as exception:
        print(f'Error filling ONTOLOGIES on line {i}')
        raise exception


def split_ontologies(conn):
    """
    Split camelCase ontologies into distinct lowercase words and save them in the SPLIT_ONTOLOGY column.

    :param conn: SQLite3 connection
    :type conn: sqlite3.Connection
    """
    cursor = conn.execute('SELECT ONTOLOGY FROM ONTOLOGIES')
    ontologies = cursor.fetchall()
    ontologies = [value[0] for value in ontologies]
    with alive_bar(len(ontologies), force_tty=True) as bar:  # Progress bar, force_tty=True for PyCharm
        for ontology in ontologies:
            split_ontology = split_camelcase_to_lowercase(ontology)
            conn.execute(
                f"UPDATE ONTOLOGIES SET SPLIT_ONTOLOGY = \"{split_ontology}\" WHERE ONTOLOGY = \"{ontology}\";"
            )
            bar()
        conn.commit()


def remove_duplicates(conn):
    """
    Remove duplicates from the ONTOLOGIES table.

    :param conn: SQLite3 connection
    :type conn: sqlite3.Connection
    """
    conn.execute("CREATE TABLE new_table AS SELECT DISTINCT ONTOLOGY FROM ONTOLOGIES;")
    conn.commit()
    conn.execute("DROP TABLE ONTOLOGIES;")
    conn.commit()
    conn.execute("ALTER TABLE new_table RENAME TO ONTOLOGIES;")
    conn.commit()
    conn.execute("ALTER TABLE ONTOLOGIES ADD COLUMN SPLIT_ONTOLOGY TEXT DEFAULT '';")
    conn.commit()


if __name__ == '__main__':
    create_db()
