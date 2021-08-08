import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

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

def print_vienna_ranking(keywords_emb, keywords_names, cities_emb, cities_names):
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
