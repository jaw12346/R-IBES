import shutil
import sqlite3


def main():
    """
    Clear the database, delete all images, and delete file structure.
    """
    shutil.rmtree('./images', True)
    conn = sqlite3.connect('./server/hw2.db')
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
        main()
    else:
        print('DATABASE CLEAR ABORTED!')
