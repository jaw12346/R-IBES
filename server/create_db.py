import sqlite3


def main():
    """
    Create the database and tables.
    """
    conn = sqlite3.connect('./server/hw2.db')
    print('Opened database successfully')
    try:
        conn.execute('''CREATE TABLE NAME_DIRECTORY
                        (NAME             TEXT    NOT NULL,
                         DIRECTORY        TEXT    NOT NULL,
                         ENCODING_COUNT   INT     NOT NULL);''')
    except sqlite3.OperationalError as exception:
        print(f'Error creating NAME_DIRECTORY:\n{exception}')

    try:
        conn.execute('''CREATE TABLE NAME_ENCODING
                        (NAME         TEXT    NOT NULL,
                         ENCODING     BLOB    NOT NULL,
                         FILE_NAME    TEXT    NOT NULL,
                         SOURCE       TEXT    NOT NULL);''')
    except sqlite3.OperationalError as exception:
        print(f'Error creating NAME_ENCODING:\n{exception}')


if __name__ == '__main__':
    main()
