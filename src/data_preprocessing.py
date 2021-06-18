import ijson
import pickle
import csv
import os
import sys

import gc

# Path to the 12gb arxiv dataset
path_dataset = "..\data\dblp.v12.json"

# Path were we will store the dataset as a python dict
path_pickled_dataset = "..\data\dblp.v12.pickle"

path_csv_folder = "..\data"

def get_prefixes():
    '''
    Outputs and returns all prefixes in the data_set (except indexed_abstract)
    '''
    prefixes = []

    with open(path_dataset, "rb") as input_file:
        # load json iteratively
        parser = ijson.parse(input_file)
        for prefix, event, value in parser:
            if prefix not in prefixes and "indexed_abstract" not in prefix:
                prefixes.append(prefix)
                print(prefix)
    return prefixes

def main():
    '''
    Takes the big arxiv dataset and transforms it to a CSV that Neo4J can import as  a knowledge graph
    '''
    transform_dict_to_csv()




def transform_dict_to_csv(dataset = None):
    '''
    Takes the processed dataset and turns it into several CSVs
    '''

    if dataset is None:
        print("\nLoad dictionary, this might take a long time")
        inputfile = open(path_pickled_dataset,'rb')

        # disable garbage collector
        gc.disable()

        dataset = pickle.load(inputfile)

        gc.enable()
        inputfile.close()

    papers = [["paper_id", "title", "year"]]
    authors = [["paper_id", "name", "org"]]
    keywords = [["paper_id", "name", "weight"]]

    print("Transform dictionary")
    for (idx,paper) in enumerate(dataset):
        if(idx % 100000 == 0):
            print(f"\r>> Transformed {idx/1000000.0} million entries", end = '', flush=True)

        papers.append([idx, clean_string(paper["title"]), paper["year"]])

        for author in paper["authors"]:
            authors.append([idx, clean_string(author["name"]), clean_string(author["org"])])

        for keyword in paper["keywords"]:
            keywords.append([idx, clean_string(keyword["name"]), keyword["weight"]])

    #print(authors)
    #return

    print("Storing CSVs:")
    export_to_csv(papers, "papers")
    export_to_csv(authors, "authors")
    export_to_csv(keywords, "keywords")

def clean_string(string):
    return string.replace(",","")


def export_to_csv(data, name):
    '''
    Takes a list of lines and stores that as a csv in the csv folder under <name>.csv
    '''
    filename = os.path.join(path_csv_folder, name + ".csv")
    print(f"Writing to {filename}")
    with open(filename, mode='w', encoding='utf-8') as file:
        csv_writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for row in data:
            csv_writer.writerow(row)



def compress_to_dict(max_lines_to_process = -1):
    '''
    Takes the big arxiv dataset and removes unneeded data and stores it as a dict
    '''
    data_set = []
    processed_lines = 0

    with open(path_dataset, "rb") as input_file:
        parser = ijson.parse(input_file)
        for prefix, event, value in parser:
            if(processed_lines % 100000 == 0):
                print(f"\r>> Read {processed_lines/1000000.0} million lines", end = '', flush=True)

            if(processed_lines == max_lines_to_process):
                break

            if "indexed_abstract" not in prefix:
                # Open or close a new paper
                if prefix == "item" and event == "start_map":
                    curr_paper = {"title":"", "authors":[], "keywords":[], "arxiv_id":0, "year":0,
                    "venue":{"arxiv_id":0, "name":""}, "publisher":""}
                elif prefix == "item" and event == "end_map":
                    data_set.append(curr_paper)

                # Keywords
                elif prefix == "item.fos.item" and event == "start_map":
                    curr_keyword = {"name":"", "weight":0}
                elif prefix == "item.fos.item" and event == "end_map":
                    curr_paper["keywords"].append(curr_keyword)
                elif prefix == "item.fos.item.name":
                    curr_keyword["name"] = value
                elif prefix == "item.fos.item.w":
                    curr_keyword["weight"] = float(value)

                # Authors
                elif prefix == "item.authors.item" and event == "start_map":
                    curr_author = {"name":"", "org":"", "arxiv_id":0}
                elif prefix == "item.authors.item" and event == "end_map":
                    curr_paper["authors"].append(curr_author)
                elif prefix == "item.authors.item.name":
                    curr_author["name"] = value
                elif prefix == "item.authors.item.org":
                    curr_author["org"] = value
                elif prefix == "item.authors.item.id":
                    curr_author["arxiv_id"] = value

                # Everything else
                elif prefix == "item.publisher":
                    curr_paper["publisher"] = value
                elif prefix == "item.title":
                    curr_paper["title"] = value
                elif prefix == "item.id":
                    curr_paper["arxiv_id"] = value
                elif prefix == "item.year":
                    curr_paper["year"] = value
                elif prefix == "item.year":
                    curr_paper["year"] = value
                elif prefix == "item.publisher":
                    curr_paper["publisher"] = value
                elif prefix == "item.venue.raw":
                    curr_paper["venue"]["name"] = value
                elif prefix == "item.venue.id":
                    curr_paper["venue"]["arxiv_id"] = value

            processed_lines += 1


        print("Storing dictionary (pickle)")
        # Store dataset as dict
        outputfile = open(path_pickled_dataset,'wb')
        pickle.dump(data_set,outputfile)
        outputfile.close()
        return data_set


if __name__ == "__main__":
    main()


def print_dataset():
    '''
    Prints the JSON (except indexed_abstract)
    '''
    with open(path_dataset, 'rb') as input_file:
        parser = ijson.parse(input_file)
        for prefix, event, value in parser:
            if "indexed_abstract" not in prefix:
                print('prefix={}, event={}, value={}'.format(prefix, event, value))




'''
Prefixes except indexed_abstract:
    item
    item.id
    item.authors
    item.authors.item
    item.authors.item.name
    item.authors.item.org
    item.authors.item.id
    item.title
    item.year
    item.n_citation
    item.page_start
    item.page_end
    item.doc_type
    item.publisher
    item.volume
    item.issue
    item.doi
    item.references
    item.references.item
    item.fos
    item.fos.item
        Contains a topic of the paper, e.g. "Computer Science" or "Communications protocol"
    item.fos.item.name
    item.fos.item.w
    item.venue
    item.venue.raw
    item.venue.id
    item.venue.type
'''
