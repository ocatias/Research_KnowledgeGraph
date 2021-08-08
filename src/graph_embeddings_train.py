from neo4j import GraphDatabase
import pandas as pd


driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'pw'))

graphname = "EmbeddingGraph1"
df_path = r"..\data\DF\fastRP.pickle"

def delete_graph(session, name):
        print("Deleting graph {0}".format(name))
        session.run("CALL gds.graph.drop(\"{0}\")".format(name))

def create_graph_just_cities_countries(session, name):
    query = \
"""CALL gds.graph.create(
"{0}",
["Cities", "Countries"],
["ISIN"])""".format(name)
    session.run(query)

def create_graph(session, name):
    print("Training creating graph {0}".format(name))
    query = \
"""CALL gds.graph.create(
"{0}",
["Papers", "Authors", "Keywords", "Cities", "Countries"],
["ISABOUT", "AUTHEREDBY", "WORKSIN", "WRITTENIN", "ISIN"])""".format(name)
    print("Create graph")
    results = session.run(query)
    for rec in results.data():
        print(rec)

def train_fastRP(session, name):
    query = \
"""CALL gds.fastRP.stream(\"{0}\",
{{embeddingDimension: 512,
iterationWeights: [1, 2, 3],
nodeLabels: ["Papers", "Authors", "Keywords", "Cities", "Countries"],
relationshipTypes: ["ISABOUT", "AUTHEREDBY", "WORKSIN", "WRITTENIN", "ISIN"],
normalizationStrength: -1,
randomSeed: 1246546
}})""".format(name)
    results = session.run(query)
    # Store results
    train_results_df = pd.DataFrame([dict(r) for r in results])
    train_results_df.to_pickle(df_path)
    print(train_results_df)


def create_node_properties(session, name):
    """
    GraphSage needs at least one node property so we will add the degree as a property
    """
    query = \
"""
CALL gds.degree.mutate(
  'EmbeddingGraph1',
  {
    mutateProperty: 'degree'
  }
) YIELD nodePropertiesWritten
"""
    session.run(query)

def train_node2vec(session, name, emb_dim = 100):
    print("Training node2vec on {0}, dim: {1}".format(name, emb_dim))
    result = session.run(
"""CALL gds.alpha.node2vec.stream(\"{0}\",
{{ embeddingDimension: {1},
iterations: 100
}})""".format(name, emb_dim))

    result = session.run(query)
    # Store results
    train_results_df = pd.DataFrame([dict(r) for r in result])
    train_results_df.to_pickle(df_path)

def train_graphsage(session, name, emb_dim = 100):
    print("Training GraphSage on {0}, emb_dim: {1}".format(name, emb_dim))
    query = \
"""CALL gds.beta.graphSage.train(
'{0}',
{{
modelName: 'graphSage',
featureProperties: ['degree'],
embeddingDimension: {1},
sampleSizes: [100, 50],
epochs: 2
}})""".format(name, emb_dim)
    print(query)
    session.run(query)

    query = \
"""CALL gds.beta.graphSage.stream(
'{0}',
{{
modelName: 'graphSage'
}})""".format(name)
    print(query)
    print("Streaming model")
    results = session.run(query)
    # Store results
    train_results_df = pd.DataFrame([dict(r) for r in results])
    train_results_df.to_pickle(df_path)

with driver.session() as session:
    print("Session started")
    print("Result will be store in {0}".format(df_path))
    delete_graph(session, graphname)
    create_graph(session, graphname)
    #create_node_properties(session, graphname)
    train_fastRP(session, graphname)
