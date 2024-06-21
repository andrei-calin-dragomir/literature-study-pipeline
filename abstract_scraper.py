import os
import csv
import time
import bs4
import requests

def extract_abstracts_from_papers(input_csv, output_csv, total_runs, starting_point=0):
    # Ensure the results directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    try:
        with open(input_csv, newline='', encoding='utf-8') as input_file, open(output_csv, 'a', newline='', encoding='utf-8') as output_file:
            csv_reader = csv.reader(input_file)
            csv_writer = csv.writer(output_file)

            rows = list(csv_reader)
            for index, row in enumerate(rows[starting_point:total_runs], starting_point):
                link = row[-1]
                if link:
                    print(row[0], link)
                    
                    # fetch the page content
                    start = time.time()
                    response = requests.get(link)
                    end = time.time()
                    
                    html_content = response.content
                    time.sleep(5)  # sleep to avoid request overload
                    
                    print('request lasted:', end-start)
                    
                    soup = bs4.BeautifulSoup(html_content, "html.parser")  # parse the content
                    target_element = soup.find(string="Abstract")  # find the element containing the abstract
                    
                    if target_element:
                        closest_elements = []
                        for sibling in target_element.next_siblings:

                            # TODO Refine abstract search within content
                            if isinstance(sibling, bs4.element.Tag) and sibling.name in {'p', 'div'}:  # Consider paragraphs or divs
                                closest_elements.append(sibling.get_text(strip=True))
                            if len(closest_elements) >= 5:  # Limit to 5 elements
                                break
                        
                        abstract_text = ' '.join(closest_elements)
                        csv_writer.writerow([index, abstract_text]) # Write abstracts
                    else:
                        csv_writer.writerow([index, '?'])  # No abstract found, save dummy string
                else:
                    csv_writer.writerow([index, None]) # No link was found

            return
    except OSError or Exception as e:
        raise(f"Error during processing:{e}")


# Example usage
if __name__ == "__main__":
    extract_abstracts_from_papers()
