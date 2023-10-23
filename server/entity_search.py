"""
Example usage:

ENTITY - DBO/DBP - DBO/DBP - ...
Example: Michael_Jackson - child - birthPlace - areaCode
Result: "310"

User intention: Where was Barack Obama born?
Allowable query: Barack_Obama birthPlace
Result: "Honolulu, Hawaii"

User intention: What are George H. W. Bush's children's birthplaces' area codes?
Allowable query: George_H._W._Bush child birthPlace areaCode
Result: ['UNKNOWN', '203/475', '432', 'UNKNOWN', '432', '432']  # UNKNOWN due to missing value in DBPedia
"""

from SPARQLWrapper import SPARQLWrapper, JSON


def _run_query(entity, questions, entity_link=False, debug=False):
    """
    Run a SPARQL query on DBpedia.
    This method allows for recursive searches through n-levels of DBpedia for a given entity.

    :param entity: Entity to search for (can be the original query's entity or a derived entity).
    :type entity: str
    :param questions: DBO/DBP (biographical) tags to search for on a given entity page.
    :type questions: list(str)
    :param entity_link: Whether the provided entity is a dbpedia link (occurs during recursive search).
                        True if a link; False otherwise.
    :type entity_link: bool
    :param debug: Enable debug mode
    :type debug: bool
    :return: A list corresponding to the result of the question asked by the entity/questions pair.
    :rtype: list(str)
    """
    # Create the SPARQL query
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    for i, question in enumerate(questions):
        if debug:
            print(f'RUNNING QUERY: <{entity}> : <{question}>')
        if entity_link:
            # Entity is a resource link from a previous recursive call
            sparql.setQuery(f"""
                        SELECT ?answer WHERE {{
                            <{entity}> <http://dbpedia.org/ontology/{question}> ?answer .
                        }}
            """)
        else:
            # Entity is a string from the original query / not a resource link
            sparql.setQuery(f"""
                SELECT ?answer WHERE {{
                    <http://dbpedia.org/resource/{entity}> <http://dbpedia.org/ontology/{question}> ?answer .
                }}
            """)

        sparql.setReturnFormat(JSON)  # Set the return format to JSON

        try:
            # Run the query and convert the results to JSON
            results = sparql.query().convert()
        except Exception as e:
            # Failed to run the query
            print(f'ERROR: {e}')
            return ['ERROR']

        answers = []
        if results["results"]["bindings"]:
            # Parse top-level results
            for result in results["results"]["bindings"]:
                answer = result["answer"]["value"]
                if answer != '':  # Ignore empty results
                    answers.append(answer)
                    if debug:
                        print(answer)

        if i != len(questions) - 1:
            # Continue to next question if one is available
            final_results = []
            for answer in answers:
                # Run the query (previous answer) on the next question
                inner_result = _run_query(answer, questions[1:], entity_link=True)  # Recursive call
                if inner_result != '':  # Ignore empty results
                    if debug:
                        print(inner_result)
                    final_results.append(inner_result)
            if len(final_results) > 0:  # Ignore empty results
                flattened = [item for sublist in final_results for item in sublist]  # Flatten possible >1D list
                return flattened
            return ['UNKNOWN']  # No results
        # No more questions to ask
        return answers if answers else ['UNKNOWN']


def module_main(entity, bio_terms, debug=False):
    """
    Method to act as the entry point for the entity search module.

    :param entity: Entity to search for (can be the original query's entity or a derived entity).
    :type entity: str
    :param bio_terms: DBO/DBP (biographical) tags to search for on a given entity page.
    :type bio_terms: list(str)
    :param debug: Enable debug mode
    :type debug: bool
    :return: A list or single string corresponding to the result of the question asked by the user's query.
    :rtype: list(str) or str
    """
    response = _run_query(entity, bio_terms, debug=debug)
    if len(response) == 1:
        # Convert single response to string
        response = response[0]
    return response


def main():
    """
    Main method for the entity search module.

    :return: A list or single string corresponding to the result of the question asked by the user's query.
    :rtype: list(str) or str
    """
    while True:
        query = input("Enter a question in the form '<entity> <biographical_term> <biographical_term> ...'\n"
                      "Example intention: 'What is the area code of each of George H. W. Bush's children's birthplaces?'\n"
                      "Example query: 'George_H._W._Bush child birthPlace areaCode'\n")
        if len(query.split()) < 2:
            # Query must consist of (at least) an entity and a biographical term
            print("Invalid query. Please try again.")
            continue
        break
    # query = 'George_H._W._Bush child birthPlace areaCode'

    # Parse the query
    entity = query.split()[0]
    bio_terms = query.split()[1:]

    # for question in dbo_dbp:
    response = _run_query(entity, bio_terms)
    if len(response) == 1:
        # Convert single response to string
        response = response[0]
    print('FINAL RESPONSE: ', response)


if __name__ == '__main__':
    main()
