# Research Knowledge Graph
In this project I create a knowledge graph with Python and Neo4j that models the relations between computer science papers, authors, citites and countries. The resulting knowledge graph has 11 million nodes and contains 5 million papers. I use logical methods to determine whether two researchers with the same name are the same person, and to compute Erdős numbers. Furthermore, I use graph embedding methods to rank the influence of cities on research areas and to detect whether two researchers are the same person. In summary, the logical methods yield good results that can intuitively understood.  The embedding methods did not give good results, which I think is mostly due to inaccaruacies with respect to cities in the dataset. Unfortunately, all these methods are very computationally expensive and I could not use them on the entire graph.

![TransE_graph](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/TransE_graph.png)
This figure shows the different information stored in the knowledge graph. The orange node in the center belongs to the [TransE](https://papers.nips.cc/paper/2013/file/1cecc7a77928ca8133fa24680a88d2f9-Paper.pdf) paper, the red nodes are the researchers of this paper and the green nodes are the topics of the paper. Finally, yellow nodes belong to the cities in which researchers work and blue nodes are the countries.

## How to generate the knowledge graph

1. Download dataset [dblp.v12](https://www.aminer.org/citation) and put into `data`
2. Do the preprocessing:  `cd src` and `python data_preprocessing.py`
3. Take all files in `data/CSV` and export them into Neo4j using the admin tool:
    - Create project and DBMS
    - Click on the three points next to the DBMS: Open Folder / DBMS
    - Copy the files into import
    - Start a terminal here and run
```
      ..\bin\neo4j-admin import --database DATABASENAME --nodes=Papers="papers_header.csv,papers.csv" --nodes=Authors="authors_header.csv,authors.csv" --nodes=Keywords="keywords_header.csv,keywords.csv" --nodes=Cities="cities_header.csv,cities.csv" --nodes=Countries="countries_header.csv,countries.csv"   --relationships=AUTHEREDBY="paper_author_header.csv,paper_author.csv" --relationships=ISABOUT="paper_keyword_header.csv,paper_keyword.csv" --relationships=WORKSIN="authors_cities_header.csv,authors_cities.csv" --relationships=ISIN="cities_countries_header.csv,cities_countries.csv"
```

  This is for windows. If you are on another OS then you need to change `..\bin\neo4j-admin`.

## Same Person Detection
The dataset contains many researchers with the same name, but different affiliated organizations. Detecting whether two authors with the same name are the same person is not a trivial problem. Here we use the shortest path distance between two author nodes to decide wether they are the same person. First we need to create *WRITTENIN* edges between papers and the cities they were written in.
```
MATCH (p:Papers)-[:AUTHOREDBY]->(:Authors)-[:WORKSIN]->(c:Cities)
	WHERE NOT (p)-[:WRITTENIN]->(c)
	CREATE (p)-[:WRITTENIN]->(c)
```
Then we can use the following query to detect whether researchers with the name *$Name* are the same person. If they are, we create a *SAMEPERSON* edges between them.
```
MATCH (n:Authors), (m:Authors),
   path=allShortestPaths( (n)-[:AUTHOREDBY|WORKSIN|WRITTENIN|SAMEPERSON*..4]-(m))
WHERE n.name = $Name AND n.name = m.name AND ID(n) <> ID(m)
WITH n,m, path, count(path) as cnt
WHERE 
   NOT (n)-[:SAMEPERSON]-(m) 
   AND cnt > 0
   AND 
   (
      NONE (x IN nodes(path) WHERE 'Cities' in Labels(x)) 
      or SINGLE  (x IN nodes(path) WHERE 'Cities' in Labels(x))
   )
CREATE (n)-[r:SAMEPERSON]->(m)
```
This means that two authors with the same name *$Name* will be connected by a *SAMEPERSON* edge if there exists a shortest path of length at most 4 between these two nodes. Note that this path is only allowed is not allowed to use some of the edge types. Due to the nature of the graph, this will only create *SAMEPERSON* edges in very specific situations. The two most important are the following. First, we create a *SAMEPERSON* edge between two researchers with the same name if one of them wrote a paper that was written in the same city as the other works in. Second, if they share a coauthor.

I also tried using graph embeddings and clustering to create *SAMEPERSON* edges, but this did not give good results.

## Erdős Numbers
We can compute Erdős numbers with the following query:
```
MATCH (n:Authors), (m:Authors), path=allShortestPaths( (n)-[:COAUTHORS*..]-(m))
WHERE n.name = $Author and m.name = "Paul Erdös"
RETURN size(nodes(path)) - 1 LIMIT 1
```
Unfortunately to this requires us to have *CoAuthor* edges between coauthors which is really computationally expensive as that would means that we need to create all possible *SAMEPERSON* edges. Since my computation power is limited, I have done only compute Erdős Numbers for three researchers. For two of those authors I got the same results as [csauthors](csauthors.net) which shows that this method works in principles. The easiest way to get it to efficiently work is to just merge all author nodes that have the same name.

## Ranking the Influence of Cities on Research Area
For this we compute a graph embedding and use the L2 distance between a city and a keyword (or topic) embedding. In the following figures I visualize the embeddings. The left column has the graph embedded into 2d space and the right column into 100d space (with PCA down to 2 dimensions). The algorithms used (from top to bottom) are: Node2Vec, TransE, RGCN and TuckER. For TransE, TuckER and RGCN. 

![Node2Vec_2d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/n2v_2d.png)
![Node2Vec_100d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/n2v_100d.png)

![TransE_2d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/transE_2d.png)
![TransE_100d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/transE_100d.png)

![RGCN_2d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/rgcn_2d.png)
![RGCN_100d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/rgcn_100d.png)

![TuckER_2d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/tucker_2d.png)
![TuckER_100d](https://github.com/ocatias/Research_KnowledgeGraph/blob/main/imgs/tucker_100d.png)

Due to my limited computation power, I only used 2% of the data and a small number of epochs for RGCN, TransE and TuckER (10, 10, and 1, respectively). This might be a big part of the reason why using embeddings and clustering for creating *SAMEPERSON* edges did not work out. 

Next we rank the cities (with more than 250 papers written in them) according to their L2 to some research topics. We report how highly Vienna is ranked with respect to the other cities. Note that for the Node2Vec embeddings the ranking is out of 58 cities and for the other embeddings it is out of 159 cities (unfortunately I used a different dataset split for this). 

| Embedding | Physics | Knowledge Management | Discrete math. | Machine Learning | Ontology | Descr. Logic | Knowl. graph |
|---|---|---|---|---|---|---|---|
| Node2Vec (2d) | 16 | 14 | 12 | 6 | 15 | 17 | 17 |
| Node2Vec (100d) | 18 | 2 | 38 | 23 | 7 | 27 | 21 |
| TransE (2d) | 64 | 76 | 74 | 72 | 71 | 70 | 64 |
| TransE (100d) | 49 | 20 | 76 | 89 | 33 | 30 | 14 |
| TuckER (2d) | 44 | 45 | 45 | 43 | 66 | 46 | 111 |
| TuckER (100d) | 122 | 124 | 124 | 124 | 115 | 116 | 80 |
| RGCN (2d) | 152 | 8 | 8 | 8 | 152 | 152 | 152 |
| RGCN (100d) | 126 | 124 | 123 | 123 | 126 | 125 | 125 |

## Datasets
- [dblp.v12](https://www.aminer.org/citation): Contains papers and authors from arxiv
```bibtex
@INPROCEEDINGS{Tang:08KDD,
    AUTHOR = "Jie Tang and Jing Zhang and Limin Yao and Juanzi Li and Li Zhang and Zhong Su",
    TITLE = "ArnetMiner: Extraction and Mining of Academic Social Networks",
    pages = "990-998",
    YEAR = {2008},
    BOOKTITLE = "KDD'08",
}
```
- [cities15000](http://download.geonames.org/export/dump/) from geonames.org ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)): Contains all cities with a population > 15000
- [Countries](https://github.com/umpirsky/country-list/blob/master/data/en/country.txt) from umpirsky: A list of all countries and country codes




4. Create a database with name DATABASENAME

## Data Processing:
Changes to the datasets:
- Add `Kosovo (XK)` to Countries
- Fix tabs in entry 3110143 in cities1500
