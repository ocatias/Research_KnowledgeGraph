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

import clustering

data_path  = r"pykeen/RGCN_dim100_epoch1"
raw_data_path = r"..\data\CSV\relations_for_pykeen.csv"


parser = argparse.ArgumentParser(description='')
parser.add_argument('--visualize', dest='visualize', action='store_true')
parser.add_argument('--ranking', dest='visualize', action='store_false')
args = parser.parse_args()
do_visualize = args.visualize

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
    clustering.plot_cluster_PCA([authors_emb, keywords_emb, cities_emb],  ['g', 'r', 'b'], [0.2, 0.2, 0.5],
    ["Authors", "Keywords", "Cities"], "Node2Vec 2D Embedding")
