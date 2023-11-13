"""
File providing entity search functionality for the R-IBES system.
"""

from collections import namedtuple
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
import texttable

from src import conversions

# Namedtuple for storing a label, property pair
LabelProperty = namedtuple('LabelProperty', ['label', 'property'])


class Node:
    def __init__(self, resource, in_question):
        self._resource = resource
        self._in_question = in_question
        self._children = []

    def add_child(self, child):
        if isinstance(child, list):
            self._children.extend(child)
        else:
            self._children.append(child)

    def get_resource(self):
        return self._resource

    def get_in_question(self):
        return self._in_question

    def get_children(self):
        return self._children

    def set_root(self):
        self._in_question = 'root'

    def is_root(self):
        return self.get_in_question() == 'root'

    def set_question(self, question):
        self._in_question = question


def call_dbpedia(resource, question, resource_link=False, debug=False):
    """
    Run a SPARQL query on DBpedia.

    :param resource: Resource to search for (can be the original query's entity or a derived entity).
    :type resource: str
    :param question: DBO/DBP (biographical) tag to search for on a given entity page.
    :type question: str
    :param resource_link: Whether the provided resource is a dbpedia link (occurs during recursive search).
                          True if a link; False otherwise.
    :type resource_link: bool
    :param debug: Enable debug mode
    :type debug: bool
    :return: Result of the question asked by the resource/question pair.
    :rtype: list(str)
    """
    sparql = SPARQLWrapper('http://dbpedia.org/sparql')
    if debug:
        print(f'Running query: <{resource}> : <{question}>')
    if resource_link:
        # Resource is a dbpedia link from a previous recursive call
        sparql.setQuery(f"""
                    SELECT ?answer WHERE {{
                        <{resource}> <http://dbpedia.org/ontology/{question}> ?answer .
                    }}
        """)
    else:
        # Resource is a string from the original query / not a dbpedia link
        # Some dbpedia "resource" redirect to "page". This is a safe redirect and doesn't inhibit the query ops
        sparql.setQuery(f"""
            SELECT ?answer WHERE {{
                <http://dbpedia.org/resource/{resource}> <http://dbpedia.org/ontology/{question}> ?answer .
            }}
        """)

    sparql.setReturnFormat(JSON)  # Set the return format to JSON
    try:
        # Run the query and convert the results to JSON
        results = sparql.query().convert()
        answers = []
        if results['results']['bindings']:
            for result in results['results']['bindings']:
                answer = result['answer']['value']
                if answer != '':
                    answers.append(answer)
        else:
            answers.append('UNKNOWN')
        if len(answers) == 0:
            return answers
        return answers
    except SPARQLExceptions.SPARQLWrapperException as sparql_exception:
        print(f'Sparql DBPedia ERROR: {sparql_exception}')
        return ['ERROR']


def _run_query(resource, questions, root, resource_link=False, debug=False):
    """
    Run a recursive SPARQL query on DBpedia.

    :param resource: Resource to search for (can be the original query's entity or a derived entity).
    :type resource: str
    :param questions: A list of DBO/DBP (biographical) tags to search for on a given entity page.
    :type questions: list(str)
    :param resource_link: Whether the provided resource is a dbpedia link (occurs during recursive search).
                          True if a link; False otherwise.
    :type resource_link: bool
    :param root: Root node of the subtree being searched.
    :type root: Node
    :param debug: Enable debug mode
    :type debug: bool
    :return: A dictionary of the results of the questions asked by the resource/question pairs.
    :rtype: dict
    """
    if len(questions) == 0 or resource == 'UNKNOWN':
        child = Node(resource, root.get_in_question())
        root.add_child(child)
        return child

    question = questions[0]
    questions.pop(0)
    answers = call_dbpedia(resource, question, resource_link, debug)
    if debug:
        print(answers)

    this_node = Node(resource, question)
    for answer in answers:
        if len(questions) > 0:
            copied_questions = questions.copy()  # Needed to copy the list, not just the reference. Otherwise, the list gets emptied
            child = _run_query(answer, copied_questions, this_node, resource_link=True, debug=debug)
            child.set_question(question)
            this_node.add_child(child)
        else:
            child = Node(answer, question)
            this_node.add_child(child)
    return this_node


# def make_table(tracker, questions):
#     """
#     Method to generate a table for the entity search's query output.
#
#     :param tracker: Question results
#     :type tracker: dict(list(str))
#     :param questions: Questions asked by the user
#     :type questions: list(str)
#     """
#     rows = [questions]
#     row_count = len(tracker[questions[0]])
#     for row_num in range(row_count):
#         vals = []
#         for question in questions:
#             vals.append(tracker[question][row_num])
#         rows.append(vals)
#
#     table_obj = texttable.Texttable(120)
#     table_obj.set_cols_align(['c' for _ in range(len(questions))])
#     table_obj.set_cols_valign(['m' for _ in range(len(questions))])
#     table_obj.set_cols_dtype(['t' for _ in range(len(questions))])
#     table_obj.add_rows(rows)
#     print(table_obj.draw())


def main(query, name, debug=False):
    """
    Main method for the entity search module.

    :param query: Query to run on the given entity. Query terms must be in the form of DBO/DBP tags.
    :type query: str
    :param name: Normalized name of the entity to search for.
    :type name: str
    :param debug: Enable debug mode
    :type debug: bool
    """
    dbpedia_name = conversions.get_dbpedia_name(name)
    questions = query.split()
    root = Node(dbpedia_name, 'root')
    root = _run_query(dbpedia_name, questions, root, debug=debug)
    root.set_root()
    pass


if __name__ == '__main__':
    query = 'child birthPlace areaCode'
    name = 'George_H._W._Bush'
    main(query, name, debug=True)
