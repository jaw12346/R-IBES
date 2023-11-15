"""
File providing entity search functionality for the R-IBES system.
"""

import json
import time
import os
from collections import namedtuple
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
from PIL import Image
import pygraphviz as pgv

from src import conversions

# Namedtuple for storing a label, property pair
LabelProperty = namedtuple('LabelProperty', ['label', 'property'])


class Node:
    """
    Node class for storing a resource and the question that was asked to get to that resource.
    """
    def __init__(self, resource, in_question):
        """
        Node class for storing a resource and the question that was asked to get to that resource.

        :param resource: Resource to store in the node.
        :type resource: str
        :param in_question: Question that was asked to get to the resource.
        :type in_question: str
        """
        self._resource = resource
        self._question = in_question
        self._children = []

    def add_child(self, child):
        """
        Add a child to the node.

        :param child: Child node to add to the node.
        :type child: Node or list(Node)
        """
        if isinstance(child, list):
            self._children.extend(child)
        else:
            self._children.append(child)

    def get_resource(self):
        """
        Get the resource of the node.

        :return: Resource of the node.
        :rtype: str
        """
        return self._resource

    def get_question(self):
        """
        Get the question that was asked to get to the resource.

        :return: Question that was asked to get to the resource.
        :rtype: str
        """
        return self._question

    def set_question(self, question):
        """
        Set the question that was asked to get to the resource.

        :param question: Question that was asked to get to the resource.
        :type question: str
        """
        self._question = question

    def get_children(self):
        """
        Get the children of the node.

        :return: Children of the node.
        :rtype: list(Node)
        """
        return self._children

    def set_root(self):
        """
        Set the node as the root node.
        """
        self._question = 'root'

    def is_root(self):
        """
        Check if the node is the root node.
        :return: True if the node is the root node; False otherwise.
        :rtype: bool
        """
        return self.get_question() == 'root'


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
    :return: A node containing the resource and the question that was asked to get to that resource.
    :rtype: Node
    """
    if len(questions) == 0 or resource == 'UNKNOWN':
        child = Node(resource, root.get_question())
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
            # Needed to copy the list, not just the reference. Otherwise, the list gets emptied
            copied_questions = questions.copy()
            child = _run_query(answer, copied_questions, this_node, resource_link=True, debug=debug)
            child.set_question(question)
            this_node.add_child(child)
        else:
            child = Node(answer, question)
            this_node.add_child(child)
    return this_node


def tree_to_dict(node):
    """
    Convert a tree to a dictionary recursively.

    :param node: Current node to convert to add to the dictionary.
    :type node: Node
    :return: Dictionary representation of the tree.
    :rtype: dict
    """
    if node is None:
        return None

    return {
        "resource": node.get_resource(),
        "in_question": node.get_question(),
        "children": [tree_to_dict(child) for child in node.get_children()]
    }


def print_tree_dict(tree):
    """
    Print the tree in a JSON format.

    :param tree: Dictionary representation of the tree.
    :type tree: dict
    """
    print(json.dumps(tree, indent=4))


def add_edges(graph, node):
    """
    Add edges to the graph recursively.

    :param graph: Graph representation of the tree.
    :type graph: AGraph
    :param node: Current node to add edges for.
    :type node: Node
    """
    for child in node.get_children():
        graph.add_edge(node.get_resource(), child.get_resource(), label=child.get_question())
        add_edges(graph, child)


def visualize_tree(root, image_name='tree.png'):
    """
    Visualize the tree using pygraphviz.

    :param root: Root node of the tree to visualize.
    :type root: Node
    :param image_name: Name of the image to save the tree to.
    :type image_name: str
    """
    graph = pgv.AGraph(directed=True)
    add_edges(graph, root)
    graph.layout(prog='dot')
    graph.draw(image_name)


def save_json(json_dict, file_name):
    """
    Save a JSON dictionary to a file.

    :param json_dict: Dictionary to save to a file.
    :type json_dict: dict
    :param file_name: Name of the file to save the JSON dictionary to.
    :type file_name: str
    """
    with open(file_name, 'w') as json_file:
        json.dump(json_dict, json_file, indent=4)


def generate_file_name(name, questions):
    """
    Generate a file name for the tree visualization.

    :param name: Normalized name of the entity to search for.
    :type name: str
    :param questions: A list of DBO/DBP (biographical) tags to search for on a given entity page.
    :type questions: list(str)
    :return: File name for the tree visualization and file name for JSON dump.
    :rtype: str, str
    """
    file_name = name.replace(' ', '_')
    for question in questions:
        file_name += f'-{question}'
    if not os.path.exists('./results'):
        os.makedirs('./results')
    return f'./results/{file_name}.png', f'./results/{file_name}.json'


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

    graph_file_name, json_file_name = generate_file_name(name, questions)
    visualize_tree(root, graph_file_name)
    save_json(jsonified_tree, json_file_name)
    img = Image.open(graph_file_name)
    img.show(title=graph_file_name)
    time.sleep(1000)


if __name__ == '__main__':
    query = 'child birthPlace areaCode'
    name = 'George_W._Bush'
    main(query, name, debug=False)

# /mnt/c/IR_Project/test_images/George_W_Bush/img_1.jpg
# child birthPlace areaCode
