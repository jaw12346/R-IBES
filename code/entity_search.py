"""
File providing entity search functionality for the R-IBES system.
"""

from collections import namedtuple
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
import texttable

import conversions

# Namedtuple for storing a label, property pair
LabelProperty = namedtuple('LabelProperty', ['label', 'property'])


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


def _run_query(resource, questions, question_tracker, resource_link=False, debug=False):
    """
    Run a recursive SPARQL query on DBpedia.

    :param resource: Resource to search for (can be the original query's entity or a derived entity).
    :type resource: str
    :param questions: A list of DBO/DBP (biographical) tags to search for on a given entity page.
    :type questions: list(str)
    :param resource_link: Whether the provided resource is a dbpedia link (occurs during recursive search).
                          True if a link; False otherwise.
    :type resource_link: bool
    :param question_tracker: Keeps track of the answers for all the original questions in order
    :type question_tracker: dict(list(str))
    :param debug: Enable debug mode
    :type debug: bool
    :return: A dictionary of the results of the questions asked by the resource/question pairs.
    :rtype: dict
    """
    # Base case: no more questions to ask
    if not questions:
        return {}

    # Recursive case: call the single query method with the first question
    question = questions[0]
    answers = call_dbpedia(resource, question, resource_link, debug)

    # Initialize the output dictionary with the resource as the key and an empty list as the value
    output = {resource: []}

    # Loop through the answers and recursively call the method with the remaining questions
    for answer in answers:
        if answer == 'UNKNOWN':
            for q in questions:
                question_tracker[q].append('UNKNOWN')
            break

        question_tracker[question].append(answer)
        # Create a sub-dictionary with the question as the key and the answer as the value
        sub_dict = {question: answer}
        # Check if the answer is a dbpedia link
        if answer.startswith('http://dbpedia.org/'):
            # Recursively call the method with the answer as the new resource and the remaining questions
            sub_output, question_tracker = _run_query(answer, questions[1:], question_tracker, resource_link=True,
                                                      debug=debug)
            # Update the sub-dictionary with the sub-output
            sub_dict.update(sub_output)
        # Append the sub-dictionary to the output list
        output[resource].append(sub_dict)

    # Return the output dictionary
    return output, question_tracker


def make_table(tracker, questions):
    """
    Method to generate a table for the entity search's query output.

    :param tracker: Question results
    :type tracker: dict(list(str))
    :param questions: Questions asked by the user
    :type questions: list(str)
    """
    rows = [questions]
    for row_num in range(len(tracker[questions[0]])):
        vals = []
        for question in questions:
            vals.append(tracker[question][row_num])
        rows.append(vals)

    tableObj = texttable.Texttable(120)
    tableObj.set_cols_align(['c' for _ in range(len(questions))])
    tableObj.set_cols_valign(['m' for _ in range(len(questions))])
    tableObj.set_cols_dtype(['t' for _ in range(len(questions))])
    tableObj.add_rows(rows)
    print(tableObj.draw())


def main(query, name, debug=False):
    """
    Main method for the entity search module.

    :param query: Query to run on the given entity. Query terms must be in the form of DBO/DBP tags.
    :type query: str
    :param name: Normalized name of the entity to search for.
    :type name: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: Query result
    :rtype: list(str)
    """
    dbpedia_name = conversions.get_dbpedia_name(name)
    questions = query.split()
    question_tracker = {question: [] for question in questions}
    response, question_tracker = _run_query(dbpedia_name, questions, question_tracker, debug=debug)
    if debug:
        print('FINAL RESPONSE: ', response)
        print('TRACKER: ', question_tracker)
    make_table(question_tracker, questions)
    return response


if __name__ == '__main__':
    query = 'child birthPlace areaCode'
    name = 'George_H._W._Bush'
    main(query, name, debug=True)
