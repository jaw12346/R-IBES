"""
File providing entity search functionality for the R-IBES system.

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
from collections import namedtuple
import spacy
from SPARQLWrapper import SPARQLWrapper, JSON

from server import conversions

# Namedtuple for storing a label, property pair
LabelProperty = namedtuple('LabelProperty', ['label', 'property'])


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
        except Exception as exception:
            # Failed to run the query
            print(f'ERROR: {exception}')
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
                inner_result = _run_query(answer, questions[1:], entity_link=True, debug=debug)  # Recursive call
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


def get_entity_properties(entity):
    """
    Get the DBPedia properties and ontologies of a given entity.

    :param entity: Entity to get properties and ontologies of from DBPedia
    :type entity: str
    :return: Dictionaries of properties and ontologies for the given entity. properties, ontologies
    :rtype: dict{str}, dict{str}
    """
    # Generate property/ontology query
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(
        "select distinct ?property ?label {"
        f"{{ dbr:{entity} ?property ?o }}"
        "union"
        f"{{ ?s ?property dbr:{entity} }}"
        "optional {"
        "?property rdfs:label ?label ."
        "filter langMatches(lang(?label), 'en')"
        "}"
        "}"
    )
    sparql.setReturnFormat(JSON)  # Set the return format to JSON
    results = sparql.query().convert()

    label_property = {}
    label_ontology = {}
    bindings = results['results']['bindings']
    for binding in bindings:
        binding_property = binding['property']['value']
        if 'ontology' not in binding_property and 'property' not in binding_property:
            # Invalid property
            continue
        try:
            label = binding['label']['value']
        except KeyError:
            # Invalid property
            continue

        split_property = binding_property.split('/')[-1]  # Get the property/ontology name from the full URL
        if 'ontology' in binding_property:
            label_ontology[label] = split_property
        elif 'property' in binding_property:
            label_property[label] = split_property

    return label_property, label_ontology


def remove_extraneous_words(query):
    """
    Remove extraneous prepositional and auxiliary words from a query.

    :param query: Query to remove extraneous words from.
    :type query: str
    :return: List of words from the query with extraneous words removed.
    :rtype: list(str)
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(query)
    sanitized = []
    for token in doc:
        if token.dep_ in ('prep', 'aux'):
            # Prepositional or auxiliary word -- Skip!
            continue
        sanitized.append(token.text)  # Append valid word
    return sanitized


def convert_to_ontology(words, ontologies):
    """
    Convert a list of words to their corresponding ontologies generated by a given entity.

    :param words: List of words corresponding to a sanitized version of the user's query.
    :type words: list(str)
    :param ontologies: Ontologies generated by a given entity.
    :type ontologies: dict{str: str}
    :return:
    """
    # Example: "area code of child birth place" -> ['area', 'code', 'child', 'birth', 'place']
    # -> ['areaCode', 'child' 'birthPlace']
    # ENTITY doesn't have areaCode but has child and birthPlace
    # -> TAKE FIRST; return 'child', ['areaCode', 'birthPlace']
    # -> ENTITY 'child' doesn't have areaCode but has birthPlace
    # ----> TAKE FIRST; return 'birthPlace', ['areaCode']
    # ----> ENTITY 'birthPlace' has areaCode! Return 'areaCode'

    vals = ontologies.values()
    found_ontologies = []
    unused_words = []
    skip_next = False
    for i, word in enumerate(words):
        if skip_next:
            # Previous word generated a valid word pair. Skip this word.
            skip_next = False
            continue

        found = False
        if i+1 < len(words):
            # Generate a word pair -- Prefer this over a single word
            next_word = words[i+1]
            lower_word_pair = f'{word} {next_word}'
            camel_word_pair = f'{word}{next_word.title()}'
            if camel_word_pair in vals:
                # Valid word pair ontology
                print(f'Found PAIR ontology: "{lower_word_pair}" | "{camel_word_pair}"')
                found_ontologies.append(camel_word_pair)
                found = True
                skip_next = True

        if word in vals and not found:
            # Valid single word ontology
            print(f'Found BASE ontology: {word} | {ontologies[word]}')
            found_ontologies.append(ontologies[word])
            continue
        if word not in vals and not found:
            # Word not in ENTITY ontologies
            unused_words.append(word)

    print('FOUND: ', found_ontologies)
    print('UNUSED: ', unused_words)


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


def independent_main():
    """
    Main method for the entity search module.

    :return: A list or single string corresponding to the result of the question asked by the user's query.
    :rtype: list(str) or str
    """
    while True:
        query = input("Enter a question in the form '<entity> <biographical_term> <biographical_term> ...'\n"
                      "Example intention: 'What is the area code of each of George H. W. Bush's children's "
                      "birthplaces?'\n"
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
    bio_terms = query.split()
    response = _run_query(dbpedia_name, bio_terms, debug=debug)
    if debug:
        print('FINAL RESPONSE: ', response)
    return response




if __name__ == '__main__':
    independent_main()
    # properties, ontologies = get_entity_properties('George_H._W._Bush')
    # query = 'area code of child birth place'
    # removed = remove_extraneous_words(query)
    # convert_to_ontology(removed, ontologies)
