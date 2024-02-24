"""
Create the database and tables.
"""

import sqlite3
from alive_progress import alive_bar


def main_db():
    """
    Create the database and tables.
    """
    conn = sqlite3.connect('./r-ibes.db')  # DB file is stored outside the src directory
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
    Create the ontology table from https://downloads.dbpedia.org/current/core/mappingbased_objects_en.ttl.
    """
    conn = sqlite3.connect('./r-ibes.db')
    print('Opened database successfully')
    try:
        conn.execute('''CREATE TABLE ONTOLOGIES
                            (RESOURCE       TEXT   NOT NULL,
                             ONTOLOGY       TEXT   NOT NULL,
                             TARGET_URI     TEXT   NOT NULL);''')
        print('ONTOLOGIES table created successfully')
    except sqlite3.OperationalError as exception:
        print(f'Error creating ONTOLOGIES:\n{exception}')


def fill_ontologies():
    """
    Fill the ontology table with the data from mappingbased_objects_en.ttl.
    """
    conn = sqlite3.connect('./r-ibes.db')
    print('Opened database successfully')
    line_count = 18746177  # Number of lines in mappingbased_objects_en.ttl
    i = 1
    try:
        print('Attempting to open mappingbased_objects_en.ttl')
        with open('./mappingbased_objects_en.ttl', 'r') as file:
            print('Successfully opened mappingbased_objects_en.ttl')
            print('Filling ONTOLOGIES table...')
            with alive_bar(line_count, force_tty=True) as bar:  # Progress bar, force_tty=True for PyCharm
                for line in file:
                    if line.startswith('<http'):  # Don't include non-link lines
                        # Extract the resource, ontology and target uri from the line
                        # Example: <http://dbpedia.org/resource/Barack_Obama> <http://dbpedia.org/ontology/residence> <http://dbpedia.org/resource/White_House>
                        # --> http://dbpedia.org/resource/Barack_Obama || residence || http://dbpedia.org/resource/White_House
                        resource = line.split(' ')[0][1:-1]
                        ontology_uri = line.split(' ')[1][1:-1]
                        if '/ontology/' in ontology_uri:  # Some links are not ontologies (w3)
                            ontology = ontology_uri.split('/')[-1][:-1]
                            target_uri = line.split(' ')[2][1:]
                            conn.execute(f"INSERT INTO ONTOLOGIES (RESOURCE, ONTOLOGY, TARGET_URI) "
                                         f"VALUES (\"{resource}\", \"{ontology}\", \"{target_uri}\");")
                    if i % 100000 == 0:
                        # Needed to prevent the database from locking up
                        conn.commit()
                    i += 1
                    bar()  # Update progress bar
            # Make sure the last changes are committed
            conn.commit()
            print('ONTOLOGIES table filled successfully')
    except sqlite3.OperationalError as exception:
        print(f'Error filling ONTOLOGIES on line {i}:\n{exception}')


if __name__ == '__main__':
    main_db()
    ontology_db()
    fill_ontologies()
