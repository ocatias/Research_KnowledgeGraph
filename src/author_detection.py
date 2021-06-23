from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'pw'))

def get_authors_by_name(name, session):
    """
    Returns a list of authors that have the given name
    """
    query = \
"""MATCH (n:Authors)
WHERE n.name = '{0}'
RETURN n""".format(name)

    result = session.run(query)
    result_list = []
    for record in result.data():
        result_list.append(record["n"])
    return result_list

def apply_sameperson_transitivity(session, surpress_print = False):
    if not surpress_print:
        print("Applying SAMEPERSON transitivity")
    query = \
"""MATCH (a:Authors)-[:SAMEPERSON]-(b:Authors)-[:SAMEPERSON]-(c:Authors)
WHERE NOT (a)-[:SAMEPERSON]-(c) AND ID(a) <> ID(b) AND ID(b) <> ID(c) AND ID(a) <> ID(c) AND ID(a) < ID(c)
CREATE (a)-[:SAMEPERSON]->(c)"""
    session.run(query)

def create_same_person_edge_for_author(name, session):
    """
    Checks if authors with the given name are the same person, if they are then it creates a SAMEPERSON edge
    """
    print("Creating SAMEPERSON edges for '{0}'".format(name))

    query = \
"""MATCH (n:Authors), (m:Authors), path=allShortestPaths( (n)-[*..4]-(m))
WHERE n.name = '{0}' AND n.name = m.name AND ID(n) <> ID(m)
WITH n,m, path, count(path) as cnt
WHERE NOT (n)-[:SAMEPERSON]-(m) AND  cnt > 0 AND NONE (x IN nodes(path) WHERE 'Keywords' in Labels(x)) AND NONE (x IN nodes(path) WHERE 'Countries' in Labels(x)) AND (NONE (x IN nodes(path) WHERE 'Cities' in Labels(x)) or SINGLE  (x IN nodes(path) WHERE 'Cities' in Labels(x)))
CREATE (n)-[r:SAMEPERSON]->(m)
WITH n, path
MATCH  (m:Authors)
WHERE n.name = m.name
return n,m, path""".format(name)

    made_changes = False
    result = session.run(query)
    while(len(result.data()) > 0):
        made_changes = True
        result = session.run(query)

    if made_changes:
        apply_sameperson_transitivity(session, True)

with driver.session() as session:
    print("Session started")
    create_same_person_edge_for_author("", session)
