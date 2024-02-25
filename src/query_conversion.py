"""
The purpose of this file is to provide a space for drafting methods necessary for
converting user queries into exclusively ontologies.
"""
import sqlite3


def get_ontologies_from_db():
    """
    Get the ontologies from the database.

    :return: All ontologies from the ONTOLOGIES table in the database (sorted alphabetically).
    :rtype: list(str)
    """
    conn = sqlite3.connect('./r-ibes.db')
    print('Opened database successfully')
    cursor = conn.execute('SELECT ONTOLOGY, SPLIT_ONTOLOGY FROM ONTOLOGIES ORDER BY ONTOLOGY ASC')
    ontologies = cursor.fetchall()
    conn.close()
    return ontologies


def get_word_variations(index, query):
    """
    Get the variations of a word in a query.
    Example: index=0, query='birth place location' -> ['birth', 'birthplace']
    Example: index=1, query='birth place location' -> ['place', 'placelocation']
    Example: index=2, query='birth place location' -> ['location']

    :param index: Index of the word in the query.
    :type index: int
    :param query: Complete query.
    :type query: str
    :return: Variations of the word in the query.
    :rtype: list(str)
    """
    curr_word = query[index]
    results = [curr_word]
    if index+1 >= len(query):
        return results
    results.append(curr_word + query[index + 1])
    results.append(curr_word + ' ' + query[index + 1])
    return results


if __name__ == '__main__':
    query = 'areacode of birth place'
    # queries_to_ontologies(query)
