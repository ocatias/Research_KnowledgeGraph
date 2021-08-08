from neo4j import GraphDatabase
import pandas as pd
import  pickle
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import argparse
import torch
from pykeen.triples import TriplesFactory
import os
import torch
import csv

from sklearn.cluster import KMeans

import clustering

raw_data_path = r"..\data\CSV\relations_for_pykeen_final.csv"

# Put authors here:
authors_list = []

parser = argparse.ArgumentParser(description='')
parser.add_argument("-m", "--model", type=str, help="Folder that contains the model in src/pykeen", required=True)
parser.add_argument("-v", '--vis', dest='visualize', action='store_true')
parser.add_argument("-r", '--rank', dest='visualize', action='store_false')
args = parser.parse_args()
do_visualize = args.visualize

data_path  = r"pykeen/{0}".format(args.model)


def extract_data(prefix, name_list, emb_list, embeddings, name, id):
    if str.startswith(name, prefix):
        emb_list.append(embeddings[id])
        name_list.append(name.replace(prefix,""))
        return True
    return False

def extract_big_cities_from_data():
    cities = {}

    with open(raw_data_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file,  delimiter = '\t', fieldnames=["t", "l", "h"])
        line_count = 0
        for row in csv_reader:
            # print(row)
            if row['l'] == "WRITTENIN":
                city_name = row['h'].replace("(CI)", "")
                if city_name not in cities:
                    cities[city_name] = 1
                else:
                    cities[city_name] += 1

    big_cities = []
    for (city, papers_nr) in cities.items():
        if papers_nr >= 250:
            big_cities.append(city)

    return big_cities

def cluster(data_emb, data_names, n_clusters):
    from sklearn.decomposition import PCA
    print("Clustering")
    labels = KMeans(n_jobs = 3, n_clusters=n_clusters, random_state=0).fit_predict(data_emb)
    return labels


def sort_clusters(data_emb, data_names, labels):
    print("Sorting embeddings")
    data_emb_clustered = {}
    data_names_clustered = {}
    for i in range(n_clusters):
        data_emb_clustered[str(i)] = []
        data_names_clustered[str(i)] = []
    for i, label in enumerate(labels):
        data_emb_clustered[str(label)].append(data_emb[i])
        data_names_clustered[str(label)].append(data_names[i])
    return data_emb_clustered, data_names_clustered

def plot_cluster(labels, data_emb, data_names, n_clusters, number_of_max_nodes_in_cluster, numbers_of_clusters_to_print, node_size = 0.01, do_PCA = False):
    if do_PCA:
        print("Performing PCA")
        pca = PCA(n_components=2)
        data_emb = pca.fit_transform(data_emb)

    data_emb_clustered, data_names_clustered = sort_clusters(data_emb, data_names, labels)

    print("Plotting")
    for i in range(numbers_of_clusters_to_print):
        x = [data_emb_clustered[str(i)][j][0] for j in range(min(len(data_emb_clustered[str(i)]), number_of_max_nodes_in_cluster))]
        y = [data_emb_clustered[str(i)][j][1] for j in range(min(len(data_emb_clustered[str(i)]), number_of_max_nodes_in_cluster))]
        plt.scatter(x, y, label = i, s = node_size)
    plt.show()
    return data_emb_clustered, data_names_clustered

def find_clusters_of(name, n_clusters, data_names_clustered):
    print("Entries named {0} and their clusters".format(name))
    for label in range(n_clusters):
        for i, name in enumerate(data_names_clustered[str(label)]):
            if author in name:
                print("\t{0}:{1}".format(name, label))

big_cities = extract_big_cities_from_data()

model = torch.load(os.path.join(data_path, "trained_model.pkl"))

file = open(os.path.join(data_path, "train_relations.pickle"), 'rb')
edges = pickle.load(file)
file.close()

file = open(os.path.join(data_path, "train_nodes.pickle"), 'rb')
nodes = pickle.load(file)
file.close()

node_emb = model.entity_representations[0]().detach().cpu().numpy()
edges_emb = model.relation_representations [0]().detach().cpu().numpy()

keywords_emb = []
keywords_name = []
cities_emb = []
cities_name = []
authors_emb = []
authors_name = []

for (name, id) in nodes.items():
    if extract_data("(K)", keywords_name, keywords_emb, node_emb, name, id):
        pass
    elif extract_data("(CI)", cities_name, cities_emb, node_emb, name, id):
        pass
    elif extract_data("(A)", authors_name, authors_emb, node_emb, name, id):
        pass

print("#cities: {0}\n#authors: {1}\n#keywords: {2}".format(len(cities_name), len(authors_name), len(keywords_name)))

if not do_visualize:
    # Get rid of the unneccessary keywords and cities
    keywords_idx_to_delete = []
    for i, name in enumerate(keywords_name):
        if name not in ["Physics", "Knowledge graph", "Machine learning", "Discrete mathematics", "Ontology", "Description logic", "Knowledge management"]:
            keywords_idx_to_delete.append(i)
    keywords_idx_to_delete.reverse()

    cities_idx_to_delete = []
    for i, name in enumerate(cities_name):
        if name not in big_cities:
            cities_idx_to_delete.append(i)
    cities_idx_to_delete.reverse()

    for i in keywords_idx_to_delete:
        del keywords_emb[i]
        del keywords_name[i]

    for i in cities_idx_to_delete:
        del cities_emb[i]
        del cities_name[i]

    clustering.print_vienna_ranking(keywords_emb, keywords_name, cities_emb, cities_name)
else:
    n_clusters = 20
    labels = cluster(authors_emb, authors_name, n_clusters)
    data_emb_clustered, data_names_clustered = sort_clusters(authors_emb, authors_name, labels)
    for author in authors_list:
       find_clusters_of(author, n_clusters, data_names_clustered)

    plot_cluster(labels, authors_emb, authors_name, n_clusters, 1000, 20, 1, True)


    # clustering.plot_cluster_PCA([authors_emb, keywords_emb, cities_emb],  ['g', 'r', 'b'], [0.2, 0.2, 0.5],
    # ["Authors", "Keywords", "Cities"], "Node2Vec 2D Embedding")
