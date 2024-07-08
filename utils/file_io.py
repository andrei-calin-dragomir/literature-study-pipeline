import os
import csv
import json
from lxml import etree
from datetime import datetime
from jsonschema import validate, ValidationError, SchemaError

# Iterate over a large-sized xml file without the need to store it in memory in
# full. Yields every next element. Source:
# https://stackoverflow.com/questions/9856163/using-lxml-and-iterparse-to-parse-a-big-1gb-xml-file
def iterate_xml(xmlfile):
    doc = etree.iterparse(xmlfile, events=('start', 'end'), load_dtd=True)
    _, root = next(doc)
    start_tag = None

    for event, element in doc:
        if event == 'start' and start_tag is None:
            start_tag = element.tag
        if event == 'end' and element.tag == start_tag:
            yield element
            start_tag = None
            root.clear()

def init_results_dir(target_directory) -> str:
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)

    # Create the results directory
    current_date = datetime.now().strftime('%d%m%Y')
    current_run_index = sum(os.path.isdir(os.path.join(target_directory, item)) and item.startswith(current_date) for item in os.listdir(target_directory))
    
    results_directory = os.path.join(target_directory, f"{current_date}_{current_run_index}")
    os.makedirs(results_directory, exist_ok=True)

    return results_directory

def init_results_file(results_directory, table_headers) -> str:
    # Create the new CSV results file
    file_path = os.path.join(results_directory, 'results.csv')
    with open(file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=table_headers)
        writer.writeheader()

    return file_path

def load_json_data(json_dump : str, schema) -> dict:
    try:
        json_data = json.loads(json_dump)
        validate(json_data, schema)
        return json_data
    except ValidationError or SchemaError as e:
        print(e)
        return None
    
def load_json_file(file_path : str, schema) -> dict:
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                json_file_data = json.load(file)
                validate(json_file_data, schema)
    except json.JSONDecodeError or ValidationError or SchemaError as e:
        print(e)
        return None

    return json_file_data