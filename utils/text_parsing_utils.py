import re
from lxml import etree
from typing import List

def get_text_inside_parens(text: str) -> list:
	"""
	Function that extracts the text within parentheses from a string
	@return: a list in which the elements correspond to the text
	previously in parentheses
	"""
	matches = re.findall(r'\(([^)]+)\)', text)
	return list(map(str.strip, matches))

def extract_doi_from_url(url):
    # Regular expression to match the DOI pattern
    doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
    match = re.search(doi_pattern, url, re.IGNORECASE)
    if match:
        return match.group(0)
    else:
        return None
    
def extract_long_text(text : str, max_paragraph_len : int) -> List[str]:
	paragraphs = re.split(r'\n\n+', text)
	long_paragraphs = [
		p for p in paragraphs if len(p.split()) > max_paragraph_len
	]
	return long_paragraphs

def clean_text(string : str) -> str:
	output = ''
	try:
		output = string.strip().replace('\n', '')
	except AttributeError as e:
		return ''
	return output 
	
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

def solve_or(test_string: str, boolean_expression: str):
	# Solves Atomic Disjunctions
	# the boolean expression should be written as a combination of
	# literals separated by the or operator written as 'or'
	literals = re.split("or", boolean_expression, flags=re.IGNORECASE)
	return any(
		literal.strip().lower() in test_string.lower() for literal in literals
	)

def solve_and(test_string: str, boolean_expression: str):
	# Solves Atomic Conjunctions
	# the boolean expression should be written as a combination of
	# literals separated by the and operator written as 'and'
	literals = re.split("and", boolean_expression, flags=re.IGNORECASE)
	return all(
		literal.strip().lower() in test_string.lower() for literal in literals
	)

def solve_cnf(test_string: str, boolean_expression: str):
	"""
	Function that solves boolean expressions in Conjunctive Normal Form (CNF)
	"""
	# solve first literals within the parenthesis
	nested_literals = get_text_inside_parens(boolean_expression)
	# literals in parentheses are disjunctions
	# check if all the disjunction are true
	if all(solve_or(test_string, x) for x in nested_literals):
		for x in nested_literals:
			boolean_expression = boolean_expression.replace(f'({x})', '')
		return solve_and(test_string, boolean_expression)
	return False


