"""
Running this file clears the database of all images, encodings, and names.
"""

import shutil
import sqlite3
import time


def main(proceed=False):
    """
    Clear the database, delete all images, and delete file structure.
    """
    if not proceed:
        print('Permission not granted to clear database. ABORTING!')
        return

    print('DANGER ZONE!\tDANGER ZONE!\tDANGER ZONE!\n')
    print('You have provided permission to delete all images, encodings, and names from the database!')
    print('You have 30 seconds to abort this operation by pressing Ctrl+C.')
    print('DANGER ZONE!\tDANGER ZONE!\tDANGER ZONE!\n')
    for i in range(30, 0, -1):
        print(f'Clearing database in {i} second{"s" if i > 1 else ""}...', end='\r')
        time.sleep(1)

    shutil.rmtree('./images', True)
    conn = sqlite3.connect('./hw2.db')
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM NAME_DIRECTORY")
        cursor.execute("DELETE FROM NAME_ENCODING")
        conn.commit()
        conn.close()
        print('Database cleared successfully.')
    else:
        print('Failed to connect to database.')


if __name__ == '__main__':
    user_confirm = input('Are you sure you want to clear the database? (y/n): ')
    if user_confirm.lower() == 'y':
        main(proceed=True)
    else:
        print('DATABASE CLEAR ABORTED!')
