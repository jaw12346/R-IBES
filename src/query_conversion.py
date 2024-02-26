"""
The purpose of this file is to provide a space for drafting methods necessary for
converting user queries into exclusively ontologies.
"""
import spacy
import sqlite3

from conversions import bytes_to_nlp


def get_ontologies_from_db():
    """
    Get the ontologies from the database.

    :return: All ontologies from the ONTOLOGIES table in the database (sorted alphabetically).
    :rtype: list(str)
    """
    conn = sqlite3.connect('./r-ibes.db')
    print('Opened database successfully')
    cursor = conn.execute('SELECT ONTOLOGY, SPLIT_ONTOLOGY, NLP FROM ONTOLOGIES ORDER BY ONTOLOGY ASC')
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


def read_ontology_bytes():
    """
    Read the ontology bytes from the database.
    """
    conn = sqlite3.connect('./r-ibes.db')
    cursor = conn.execute('SELECT SPLIT_ONTOLOGY, NLP FROM ONTOLOGIES')
    ontologies = cursor.fetchall()
    conn.close()

    returnable = {}
    nlp = spacy.load('en_core_web_md')
    for ontology, ont_bytes in ontologies:
        nlp_obj = bytes_to_nlp(ont_bytes, nlp)
        returnable[ontology] = nlp_obj
    return returnable


if __name__ == '__main__':
    query = 'areacode of birth place'
    # queries_to_ontologies(query)
