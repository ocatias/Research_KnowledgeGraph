import ijson
import pickle
import csv
import os
import sys

import gc

# Path to the 12gb arxiv dataset
path_dataset = "..\data\dblp.v12.json"

path_dataset_cities = "..\data\cities15000.txt"

# Path were we will store the dataset as a python dict
path_pickled_dataset = "..\data\dblp.v12.small.pickle"

path_csv_folder = "..\data\CSV"

path_countries = "..\data\country.txt"

cities_blacklist = ["university"]

def load_countries():
    '''
    Updates the city blacklist with all names of countries (and their parts)
    Returns code -> country dictionary
    '''

    print("Loading countries dataset and updating blacklist")

    countries = []
    code_to_country = {}
    country_to_code = {}

    with open(path_countries, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in lines:
            split_line = line.split(" (")
            country = split_line[0]
            code = split_line[-1].split(")")[0]
            code_to_country[code] = country
            country_to_code[country] = code
            countries.append(country)

            for part_of_country_name in country.split(" "):
                if part_of_country_name == "":
                    continue
                cities_blacklist.append(clean_string_cities(part_of_country_name))
    return code_to_country, country_to_code


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
    code_to_country, country_to_code = load_countries()
    dict = compress_to_dict(5000)
    dict_all_cities, city_to_country, list_cities = load_cities_data()
    transform_dict_to_csv(dict_all_cities, city_to_country, country_to_code, list_cities, dict)


def org_to_unique_city(org, dict_all_cities, city_to_country, country_to_code, max_words_in_city_name = 3):
    '''
    Given an org name, splits it into all single words and checks if any of them are a city
    Retuns the unique name of that city and country code
    '''
    # Remove all non-alphabet characters
    org_only_alphabet = ""
    for i in org:
        if i.isalpha():
            org_only_alphabet += i
        else:
            org_only_alphabet += " "

    org = org_only_alphabet

    words = org.replace(",", " ").replace("\t", " ").split(" ")
    words = [word for word in words if word != ""]

    possible_names = []
    for i in range(1, max_words_in_city_name + 1):
        possible_names += string_to_windows(words, i)

    found_city_name = False
    unique_name = ""
    country = ""

    for possible_name in possible_names:
        if(possible_name in dict_all_cities):
            if possible_name in cities_blacklist:
                continue

            found_city_name = True
            unique_name = dict_all_cities[possible_name]
            country = city_to_country[unique_name]

    if not found_city_name:
        for possible_name in words:
            if(possible_name in country_to_code):
                country = country_to_code[possible_name]

    return unique_name, country

def string_to_windows(input_list, windows_size):
    '''
    Slides a window over a list and returns everything inside that window
    '''
    output_list = []
    for idx, element in enumerate(input_list):
        if idx + windows_size > len(input_list):
            break
        else:
            output_list.append(clean_string_cities(' '.join([input_list[i] for i in range(idx, idx + windows_size)])))

    return output_list

def clean_string_cities(city):
    return city.lower().replace(" ", "")

def ensure_is_int_or_empty(input):

    if isinstance(input, int):
        return input
    elif isfloat(input):
        return int(float(input))
    elif isinstance(input, str) and input.isnumeric():
        return input
    return ""


def load_cities_data():
    '''
    Loads the cities15000 dataset
    Returns: dict_all_cities, city_to_country, list_cities, list_unique_citynames
    '''

    # Contains all cities from the dataset, key is possible city names, returns unique city names
    dict_all_cities = {}

    # List of all unique city names
    list_cities = []

    # Dictionary
    #   Key: Unique city name
    #   Value: Country Code
    city_to_country = {}

    with open(path_dataset_cities, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in lines:

            # First element is an id, get rid of it
            row = line.split("\t")
            unique_name = clean_string_cities(row[2])

            if(unique_name in cities_blacklist):
                continue

            list_cities.append(unique_name)
            names = [row[1], row[2]] + row[3].split(',')

            country_idx = -1
            for (idx, element) in enumerate(names):

                if isfloat(element):
                    break

                if(element not in dict_all_cities):
                    dict_all_cities[clean_string_cities(element)] = unique_name

            city_to_country[unique_name] = row[8]


    # Remove potential duplicates in list_cities
    list_cities = list(dict.fromkeys(list_cities))

    return dict_all_cities, city_to_country, list_cities

def isfloat(value):
    '''
    Check if a string is a float
    Source: https://stackoverflow.com/a/20929881/6515970
    '''
    try:
        float(value)
        return True
    except ValueError:
        return False

def transform_dict_to_csv(dict_all_cities, city_to_country, country_to_code, list_cities, dataset = None):
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

    # papers = [["paper_id", "title", "year"]]
    # authors = [["paper_id", "name", "org", "city", "country"]]
    # keywords = [["paper_id", "name", "weight"]]
    papers = []
    authors = []
    keywords = []

    paper_keyword_relations = []
    paper_author_relations = []

    authors_last_id = 0
    authors_to_id = {}
    keywords_last_id = 0
    keywords_to_id = {}

    authors_cities = []

    print("Transform dictionary")
    for (id,paper) in enumerate(dataset):
        if(id % 5000 == 0):
            print(f"\r>> Transformed {id/1000000.0} million entries", end = '', flush=True)

        papers.append([id, clean_string(paper["title"]), ensure_is_int_or_empty(paper["year"])])

        for author in paper["authors"]:
            org = clean_string(author["org"])
            city, country =  org_to_unique_city(org, dict_all_cities, city_to_country, country_to_code)
            name = clean_string(author["name"])

            identifier = name + " " + city

            if identifier in authors_to_id:
                author_id = authors_to_id[identifier]
            else:
                author_id = authors_last_id
                authors.append([author_id, name, org, city, country])
                authors_to_id[identifier] = author_id
                authors_last_id += 1

                if city != "":
                    authors_cities.append([author_id, city])

            paper_author_relations.append([id, author_id])

        for keyword in paper["keywords"]:
            name = clean_string(keyword["name"])
            weight = keyword["weight"]

            if name in keywords_to_id:
                keyword_id = keywords_to_id[name]
            else:
                keyword_id = keywords_last_id
                keywords.append([keyword_id, name])
                keywords_to_id[name] = keyword_id
                keywords_last_id += 1

            paper_keyword_relations.append([id, keyword_id, weight])

    print("\nStoring CSVs:")
    export_to_csv(papers, "papers")
    export_to_csv(authors, "authors")
    export_to_csv(keywords, "keywords")
    export_to_csv(paper_author_relations, "paper_author")
    export_to_csv(paper_keyword_relations, "paper_keyword")
    export_to_csv(authors_cities, "authors_cities")

    cities =  list(map(lambda x: [x], list_cities))
    countries = list(map(lambda x: [x], list(country_to_code.values())))
    export_to_csv(cities, "cities")
    export_to_csv(countries, "countries")

    cities_countries = []
    for city in list_cities:
        cities_countries.append([city, city_to_country[city]])

    export_to_csv(cities_countries, "cities_countries")


def clean_string(string):
    return string.replace(",","").replace("\"", "").replace("'", "")

def export_to_csv(data, name):
    '''
    Takes a list of lines and stores that as a csv in the csv folder under <name>.csv
    '''
    filename = os.path.join(path_csv_folder, name + ".csv")
    print(f"Writing to {filename}")
    with open(filename, mode='w', encoding='utf-8', errors='ignore') as file:
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


        print("\nStoring dictionary (pickle)")
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
