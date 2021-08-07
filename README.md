# Research KnowledgeGraph
In this project I create a knowledge graph with Python and Neo4j that models the relations between computer science papers, authors, citites and countries. The resulting knowledge graph has 11 million nodes and contains 5 million papers. I use logical methods to determine whether two researchers with the same name are the same person, and to compute Erdős numbers. Furthermore, I use graph embedding methods to rank the influence of cities on research areas and to detect whether two researchers are the same person. In summary, the logical methods yield good results that can intuitively understood. Unfortunately, the logical methods are very computationally expensive. The embedding methods did not give good results, which I think is mostly due to inaccaruacies with respect to cities in the dataset.

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
The dataset contains many researchers with the same name, but different affiliated organizations. Detecting whether two authors with the same name are the same person is not a trivial problem. Here we use the shortest path distance between two author nodes to decide wether they are the same person. For this we use the following Cypher query:
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
This means that two authors with the same name *$Name* will be connected by a *SAMEPERSON* edge if there exists a shortest path of length at most 4 between these two nodes. Note that this path is only allowed is not allowed to use some of the edge types. 

## Erdős Numbers
We can compute Erdős numbers with the following query:
```
MATCH (n:Authors), (m:Authors), path=allShortestPaths( (n)-[:COAUTHORS*..]-(m))
WHERE n.name = $Author and m.name = "Paul Erdös"
RETURN size(nodes(path)) - 1 LIMIT 1
```
Unfortunately to this requires us to have *CoAuthor* edges between coauthors which is really computationally expensive as that would means that we need to create all possible *SAMEPERSON* edges. Since my computation power is limited, I have done only compute Erdős Numbers for three researchers. For two of those authors I got the same results as [csauthors](csauthors.net) which shows that this method works in principles. The easiest way to get it to efficiently work is to just merge all author nodes that have the same name.

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
