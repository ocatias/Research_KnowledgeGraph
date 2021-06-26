from neo4j import GraphDatabase
import pandas as pd


driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'pw'))

graphname = "EmbeddingGraph1"
df_path = r"..\data\DF\graphsage_2dim.pickle"

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
    result = session.run("""CALL gds.fastRP.stream(\"{0}\",
{{embeddingDimension: 4,
iterationWeights: [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]}})""".format(name))
    for rec in result.data():
        # print(rec)
        if(rec['embedding'] != [0.0, 0.0, 0.0, 0.0]):
            print(rec)

def train_node2vec(session, name, emb_dim = 100):
    print("Training node2vec on {0}, dim: {1}".format(name, emb_dim))
    result = session.run(
"""CALL gds.alpha.node2vec.stream(\"{0}\",
{{ embeddingDimension: {1},
iterations: 100
}})""".format(name, emb_dim))

    # Store results
    train_results_df = pd.DataFrame([dict(r) for r in result])
    train_results_df.to_pickle(df_path)

def train_graphsage(session, name, emb_dim = 100):
    print("Training GraphSage on {0}, emb_dim: {1}".format(name, emb_dim))
    query = \
"""CALL gds.beta.graphSage.stream(
'{0}',
{{
modelName: 'exampleTrainModel1',
degreeAsProperty: True,
aggregator: 'mean',
activationFunction: 'sigmoid',
embeddingDimension: {1},
sampleSizes: [200, 500, 1000],
epochs: 1
}})""".format(name, emb_dim)

    results = session.run(query)
    for rec in results.data():
        print(rec)

    # Store results
    train_results_df = pd.DataFrame([dict(r) for r in results])
    train_results_df.to_pickle(df_path)

with driver.session() as session:
    print("Session started")
    print("Result will be store in {0}".format(df_path))
    create_graph(session, graphname)
    train_graphsage(session, graphname, 2)
