"""
File providing entity search functionality for the R-IBES system.
"""

from collections import namedtuple, deque
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
from PIL import Image

import json
import time
import pygraphviz as pgv

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


def print_results(root, questions):
    for child in root.get_children():
        question = child.get_in_question()
        tabs = '\t' * questions.index(question)
        print(f"{tabs}{question}: {child.get_resource()}")
        print_results(child, questions)


def tree_to_dict(node):
    if node is None:
        return None

    return {
        "resource": node.get_resource(),
        "in_question": node.get_in_question(),
        "children": [tree_to_dict(child) for child in node.get_children()]
    }


def print_tree_dict(tree):
    print(json.dumps(tree, indent=4))


def add_edges(graph, node):
    for child in node.get_children():
        graph.add_edge(node.get_resource(), child.get_resource(), label=child.get_in_question())
        add_edges(graph, child)


def visualize_tree(root):
    graph = pgv.AGraph(directed=True)
    add_edges(graph, root)
    graph.layout(prog='dot')
    graph.draw('tree.png')


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

    root = _run_query(dbpedia_name, questions.copy(), root, debug=debug)
    root.set_root()

    jsonified_tree = tree_to_dict(root)
    print_tree_dict(jsonified_tree)
    visualize_tree(root)
    img = Image.open('tree.png')
    img.show()
    time.sleep(1000)


if __name__ == '__main__':
    query = 'child birthPlace areaCode'
    name = 'George_W._Bush'
    main(query, name, debug=False)

# /mnt/c/IR_Project/test_images/George_W_Bush/img_1.jpg
# child birthPlace areaCode
