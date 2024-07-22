import json
import os
from jsonschema import validate

def load_json(file_path):
    """
    Load JSON file from the specified path.
    
    :param file_path: Path to the JSON file.
    :return: Parsed JSON data.
    :raises FileNotFoundError: If the file does not exist.
    :raises json.JSONDecodeError: If the file is not a valid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    return data

def load_json_from_string(json_string):
    """
    Load JSON data from a JSON string.
    
    :param json_string: JSON string.
    :return: Parsed JSON data.
    :raises json.JSONDecodeError: If the string is not a valid JSON.
    """
    data = json.loads(json_string)
    return data

def validate_json(json_file_path, schema_file_path):
    """
    Validate a JSON file against a JSON schema.
    
    :param json_file_path: Path to the JSON file.
    :param schema_file_path: Path to the JSON schema file.
    :return: the JSON object if the JSON file is valid according to the schema.
    :raises ValidationError: If the JSON data does not conform to the schema.
    :raises SchemaError: If the schema itself is invalid.
    :raises FileNotFoundError: If any of the files do not exist.
    :raises json.JSONDecodeError: If any of the files are not valid JSON.
    """
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The JSON file at {json_file_path} does not exist.")
    
    if not os.path.exists(schema_file_path):
        raise FileNotFoundError(f"The schema file at {schema_file_path} does not exist.")
    
    json_data = load_json(json_file_path)
    schema_data = load_json(schema_file_path)
    
    validate(instance=json_data, schema=schema_data)
    
    return json_data
