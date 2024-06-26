import csv
from lxml import etree
from solve_cnf import solve_cnf

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

def extract_dblp_papers(dblp_xml, venues, year_min, year_max, search_words, results_file):
    hits = 0
    search_query = " AND ".join(search_words)
    
    with open(results_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['hit', 'title', 'year', 'authors', 'key', 'ee']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Parse all entries in the DBLP database.
        for dblp_entry in iterate_xml(dblp_xml):
            key = dblp_entry.get('key')
            try:
                if (key.startswith(tuple(venues)) and
                    int(dblp_entry.find('year').text) >= int(year_min) and
                    int(dblp_entry.find('year').text) <= int(year_max)):
                    
                    title = ''.join(dblp_entry.find('title').itertext())
                    
                    if solve_cnf(title, search_query):
                        authors = ' & '.join(''.join(author.itertext()) for author in
                                             dblp_entry.findall('author'))
                        
                        ee = dblp_entry.find('ee')
                        if ee is not None:
                            ee = ee.text
                        
                        # Write the result to the CSV file
                        writer.writerow({
                            'hit': hits,
                            'title': title.replace(',', ';'),
                            'year': dblp_entry.find('year').text,
                            'authors': authors,
                            'key': key,
                            'ee': ee
                        })
                        
                        hits += 1
            except AttributeError as e:
                print(e)
    
    return hits