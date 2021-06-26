from neo4j import GraphDatabase
import pandas as pd
import  pickle
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import argparse

driver = GraphDatabase.driver('neo4j://localhost:7687', auth=('neo4j', 'pw'))
df_path = r"..\data\DF\node2vec_2dim.pickle"
# df_path = r"..\data\DF\node2vec_100dim.pickle"

def get_authors(session):
    query = \
"""MATCH (n:Authors)
RETURN ID(n), n.name
"""
    authors_id = []
    authors = {}
    results = session.run(query)
    for rec in results.data():
        authors[rec["ID(n)"]] = rec["n.name"]
        authors_id.append(rec["ID(n)"])

    return authors, authors_id

def get_cities(session, select_all = False):
    if select_all:
        query = \
"""MATCH (n:Cities)
RETURN ID(n), n.cityId
"""
    else:
        query = \
"""MATCH (n:Cities)
WHERE size((:Papers)-[:WRITTENIN]->(n)) > 250
RETURN ID(n), n.cityId
"""

    cities_id = []
    cities_name = []
    cities = {}
    results = session.run(query)
    for rec in results.data():
        cities[rec["ID(n)"]] = rec["n.cityId"]
        cities_id.append(rec["ID(n)"])
        cities_name.append(rec["n.cityId"])

    return cities, cities_id

def get_keywords(session, select_all = False):
    if select_all:
        query = \
"""MATCH (n:Keywords)
RETURN ID(n), n.name
"""
    else:
        query = \
"""MATCH (n:Keywords)
WHERE n.name in [\"Physics\", \"Knowledge graph\", \"Machine learning\", \"Discrete mathematics\", "Ontology", "Description logic", "Knowledge management"]
RETURN ID(n), n.name LIMIT 10
"""
    keywords_id = []
    keywords_name = []
    keywords = {}
    results = session.run(query)
    for rec in results.data():
        keywords[rec["ID(n)"]] = rec["n.name"]
        keywords_id.append(rec["ID(n)"])
        keywords_name.append(rec["n.name"])

    return keywords, keywords_id

def plot_cluster_general(dataframes_embeddings, lists_colors, list_sizes, list_labels, title, do_PCA, lists_names = None):
    embedded_vectors = []
    names = []
    start_idx = []
    end_idx = []
    for i in range (len(dataframes_embeddings)):
        embedded_vectors+= dataframes_embeddings[i]

        if lists_names is not None:
            names += lists_names[i]

        if len(end_idx) == 0:
            start_idx = [0]
            end_idx = [len(dataframes_embeddings[i])]
        else:
            start_idx.append(end_idx[-1])
            end_idx.append(end_idx[-1] + len(dataframes_embeddings[i]))

    if do_PCA:
        pca = PCA(n_components=2)
        data = pca.fit_transform(embedded_vectors).transpose()
    else:
        data = embedded_vectors
    fig, ax = plt.subplots(figsize=(4, 3))

    for i in range (len(dataframes_embeddings)):
        x, y = data[0][start_idx[i]:end_idx[i]], data[1][start_idx[i]:end_idx[i]]
        ax.scatter(x, y, c=lists_colors[i], s=list_sizes[i], label=list_labels[i])
    ax.legend(loc='lower right')
    if lists_names is not None:
        for i, name in enumerate(names):
            ax.annotate(name, (data[0][i], data[1][i]))

    plt.show()

def plot_cluster(dataframes_embeddings, lists_colors, list_sizes, list_labels, title, lists_names = None):
    return plot_cluster_general(dataframes_embeddings, lists_colors, list_sizes, title, False, lists_names)

def plot_cluster_PCA(dataframes_embeddings, lists_colors, list_sizes, list_labels, title, lists_names = None):
    return plot_cluster_general(dataframes_embeddings, lists_colors, list_sizes, list_labels, title, True, lists_names)

def get_ranking(emb_target, emb_data, names_data, metric):
    def get_score(pt):
        return pt.get('score')

    data = []
    for emb, name in zip(emb_data, names_data):
        data.append({"score": metric(np.array(emb_target)-np.array(emb)), "name": name})
    data.sort(key=get_score)
    return data

parser = argparse.ArgumentParser(description='')
parser.add_argument('--visualize', dest='visualize', action='store_true')
parser.add_argument('--ranking', dest='visualize', action='store_false')
args = parser.parse_args()
do_visualize = args.visualize

# Load datafroma
print("Loading embedding from {0}".format(df_path))
pickleFile = open(df_path, 'rb')
df = pickle.load(pickleFile)
pickleFile.close

with driver.session() as session:
    print("Session started")

    select_all = do_visualize
    authors, authors_id = get_authors(session)
    authors_df = df.query('nodeId in @authors_id')
    authors_names = [authors[id] for id in authors_df['nodeId'].tolist()]
    authors_emb = authors_df['embedding'].tolist()

    keywords, keywords_id = get_keywords(session, select_all)
    keywords_df = df.query('nodeId in @keywords_id')
    keywords_names = [keywords[id] for id in keywords_df['nodeId'].tolist()]
    keywords_emb = keywords_df['embedding'].tolist()

    cities, cities_id = get_cities(session, select_all)
    cities_df = df.query('nodeId in @cities_id')
    cities_names = [cities[id] for id in cities_df['nodeId'].tolist()]
    cities_emb = cities_df['embedding'].tolist()

    if do_visualize:
        plot_cluster_PCA([authors_emb, keywords_emb, cities_emb],  ['g', 'r', 'b'], [2, 2, 5],
        ["Authors", "Keywords", "Cities"], "Node2Vec 2D Embedding")

    # plot_cluster([cities_emb, keywords_emb, authors_emb],  ['b', 'r', 'g'])

    if not do_visualize:
        for k_emb, k_name in zip(keywords_emb, keywords_names):
            results = get_ranking(k_emb, cities_emb, cities_names, np.linalg.norm)
            print(k_name, ": ")
            vienna_rank = -1
            for i,r in enumerate(results):
                if i < 10:
                    print("\t", r["name"], ": ", r["score"])
                if r["name"] == "vienna":
                    vienna_rank = i + 1
            print("Vienna is ranked {0} / {1} in {2}".format(vienna_rank, len(results), k_name))
