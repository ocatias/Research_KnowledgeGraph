# Research_KnowledgeGraph
In this project I create a knowledge graph that models the relations between computer science papers, authors, citites and countries. The resulting knowledge graph has 11 million nodes and contains 5 million papers. I use logical methods to determine whether two researchers with the same name are the same person, and to compute Erdős numbers. Furthermore, I use graph embedding methods to rank the influence of cities on research areas and to detect whether two researchers are the same person. In summary, the logical methods yield good results that can intuitively understood. Unfortunately, the logical methods are very computationally expensive. The embedding methods did not give good results, which I think is mostly due to inaccaruacies with respect to cities in the dataset.

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

4. Create a database with name DATABASENAME

## Data Processing:
Changes to the datasets:
- Add `Kosovo (XK)` to Countries
- Fix tabs in entry 3110143 in cities1500
