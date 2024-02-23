"""
Create the database and tables.
"""

import sqlite3


def main_db():
    """
    Create the database and tables.
    """
    conn = sqlite3.connect('../r-ibes.db')  # DB file is stored outside the src directory
    print('Opened database successfully')
    try:
        conn.execute('''CREATE TABLE NAME_DIRECTORY
                            (NAME             TEXT    NOT NULL,
                             DIRECTORY        TEXT    NOT NULL,
                             ENCODING_COUNT   INT     NOT NULL);''')
        print('NAME_DIRECTORY table created successfully')
    except sqlite3.OperationalError as exception:
        print(f'Error creating NAME_DIRECTORY:\n{exception}')

    try:
        conn.execute('''CREATE TABLE NAME_ENCODING
                            (NAME         TEXT    NOT NULL,
                             ENCODING     BLOB    NOT NULL,
                             FILE_NAME    TEXT    NOT NULL,
                             SOURCE       TEXT    NOT NULL);''')
        print('NAME_ENCODING table created successfully')
    except sqlite3.OperationalError as exception:
        print(f'Error creating NAME_ENCODING:\n{exception}')

def ontology_db():
    """
    Create the ontology table from https://downloads.dbpedia.org/current/core/infobox_properties_en.ttl.bz2.
    """
    conn = sqlite3.connect('../r-ibes.db')
    print('Opened database successfully')
    try:
        conn.execute('''CREATE TABLE ONTOLOGIES
                            (RESOURCE       TEXT   NOT NULL,
                             ONTOLOGY       TEXT   NOT NULL,
                             ONTOLOGY_URI   TEXT   NOT NULL);''')
        print('ONTOLOGIES table created successfully')
    except sqlite3.OperationalError as exception:
        print(f'Error creating ONTOLOGIES:\n{exception}')


if __name__ == '__main__':
    main_db()
    ontology_db()
