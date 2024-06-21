import os
import json
import argparse
import pandas as pd
from datetime import datetime
from abstract_scraper import extract_abstracts_from_papers
from paper_scraper import extract_dblp_papers
from criteria_assessment import assess_abstracts

def user_confirmation(prompt, auto=False):
    if auto:
        print(f"Auto mode is enabled. Proceeding to next step...")
        return True
    while True:
        response = input(f"{prompt} (yes/no): ")
        if response.lower() == 'yes':
            return True
        elif response.lower() == 'no':
            return False
        else:
            print("Unexpected answer. Try again.")

def load_json_data(json_file_path) -> dict:
    try:
        with open(json_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"JSON file not found: {json_file_path}")
        exit(0)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {json_file_path}")
        exit(0)

def create_new_file(file_name, target_directory):
    if not os.path.isdir(target_directory):
        raise NotADirectoryError(f"The directory {target_directory} does not exist or is not a directory.")
    
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)
    
    # Define the path to the new CSV file
    file_path = os.path.join(target_directory, file_name)
    
    # Create an empty CSV file
    with open(file_path, 'w', newline='') as file:
        pass
    
    return file_path

def main():
    try:
        parser = argparse.ArgumentParser(description="Process the study design pipeline with various options.")
        parser.add_argument('--study_design', type=str, help='The path to the study to be used')
        parser.add_argument('--dblp', type=str, help='Specify the path to your dblp')
        parser.add_argument('--batch_size', type=int, help='Number of papers to process in current run')
        parser.add_argument('--resume', type=str, help='Specify the path to your results directory to resume processing')
        parser.add_argument('--auto', action='store_true', help='Do not ask for user confirmation before moving to the next step')

        args = parser.parse_args()

        # Step 0: Parse run arguments
        if args.resume:
            if args.study_design or args.dblp:
                print('You must start a fresh run if you do not want to use the same study design/dblp file as the previous run')
                exit(0)
        else:
            if not args.study_design or not args.dblp:
                print('For a new run, both a study as well as a dblp file need to be specified')
                exit(0)
            elif not os.path.exists(args.study_design):
                print(f"Study design file not found on path {args.study_design}")
                exit(0)
            elif not os.path.exists(args.dblp):
                print(f"Dblp file not found on path {args.dblp}")
                exit(0)

        # Step 1: Setup configuration of the current run
        current_date = datetime.datetime.now().strftime("%d%m%Y")
        current_run_index = sum(os.path.isdir(os.path.join(results_directory, item)) and item.startswith(current_date) for item in os.listdir(results_directory))
        
        results_directory = os.path.join('./results/', args.resume if args.resume else f"{current_date}_{current_run_index}")
        os.makedirs(results_directory, exist_ok=True)

        run_summary = {}
        run_summary['run_start'] = datetime.now()
        old_run_summary = load_json_data(os.path.join(results_directory, 'run_summary.json')) if args.resume else {}

        run_summary['batch_size'] = args.batch if args.batch else old_run_summary['batch_size'] if args.resume else None
        run_summary['study_design'] = old_run_summary['study_design'] if args.resume else load_json_data(args.study_design)
        run_summary['dblp_file'] = old_run_summary['dblp'] if args.resume else args.dblp
        run_summary['dblp_version'] = old_run_summary['dblp'] if args.resume else args.dblp if args.dblp.rfind('dblp') == -1 else args.dblp[args.dblp.rfind('dblp'):]

        print(f"Loaded study design: {run_summary['study_design']}")
        print(f"Running with this dblp: {run_summary['dblp_version']}")
        print(f"Attempting to satisfy this batch size: {run_summary['batch_size']}")

        
        # Step 2: Paper extraction
        print("Next Step: Paper Extraction")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)
            
        papers_file = os.path.join(results_directory, 'papers.csv') if args.resume else create_new_file('papers.csv', results_directory)
        number_of_papers = len(pd.read_csv(papers_file))

        # If number of papers does not satisfy batch size
        if number_of_papers < run_summary['batch_size']:
            extract_dblp_papers(run_summary['dblp_file'], run_summary['study_design']['venues'], 
                                run_summary['study_design']['year_min'], run_summary['study_design']['year_max'], 
                                run_summary['study_design']['search_words'], papers_file, 
                                run_summary['batch_size'] - number_of_papers, 0 if number_of_papers == 0 else number_of_papers)
        
        # If number of papers still does not satisfy batch size
        number_of_papers = len(pd.read_csv(papers_file))
        if number_of_papers < run_summary['batch_size']:
            print(f'Number of papers collected does not satisfy desired batch size ({run_summary['batch_size']}) found only {number_of_papers}')
            if not user_confirmation("Proceed with this selection?", args.auto):
                return
        
        # Update batch size based on number of papers and desired batch size
        if not run_summary['batch_size'] or number_of_papers <= run_summary['batch_size']: run_summary['batch_size'] = number_of_papers

        run_summary['papers_collected'] = number_of_papers
        print(f"Total papers collected: {number_of_papers}")

        # Step 3: Abstracts extraction
        print("Next Step: Abstracts Extraction")
        if not user_confirmation("Proceed with this step?", args.auto):
            return

        abstracts_file = os.path.join(results_directory, 'abstracts.csv') if args.resume else create_new_file('abstracts.csv', results_directory)
        abstracts_file_size = len(pd.read_csv(abstracts_file))

        # If number of abstracts does not satisfy batch_size
        if abstracts_file_size < run_summary['batch_size']:
            if abstracts_file_size != 0:
                print('Abstracts found but incomplete. Resuming previous abstract extraction...')
            else:
                print('No abstracts found. Starting new abstract extraction...')
            extract_abstracts_from_papers(papers_file, abstracts_file, run_summary['batch_size'], abstracts_file_size)
        else:
            print("Abstracts found are sufficient.")

        number_of_abstracts = len(pd.read_csv(abstracts_file))
        run_summary['abstracts_collected'] = number_of_abstracts
        print(f"Total abstracts collected: {number_of_abstracts}")

        # Step 4: Criteria assessments
        print("Next Step: Criteria assessments based on abstracts")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)

        criteria_file = os.path.join(results_directory, 'criteria_assessments.csv') if args.resume else create_new_file('criteria_assessments.csv', results_directory)
        criteria_file_size = len(pd.read_csv(criteria_file))
            
        if criteria_file_size < run_summary['batch_size']:
            if criteria_file_size != 0:
                print("Assessments found but incomplete. Resuming previous criteria assessments process...")
            else:
                print('No criteria assessments found. Starting new criteria assessments process...')
            assess_abstracts(run_summary['study_design']['inclusion_criteria'], run_summary['study_design']['exclusion_criteria'], 
                                abstracts_file, criteria_file, run_summary['batch_size'], criteria_file_size)
        else:
            print("Criteria assessments found are sufficient.")
        
        number_of_criteria_assessments = len(pd.read_csv(abstracts_file))
        run_summary['criteria_assessments'] = number_of_criteria_assessments
        print(f"Total criteria assessments: {number_of_criteria_assessments}")
    
    except Exception as e:
        print(e)
    finally:
        run_summary['run_end'] = datetime.now()
        print(f'Process finished/terminated. This run took: {run_summary['run_start'] - run_summary['run_end']}')
        with open(os.path.join(results_directory, 'run_summary.json'), 'w') as run_summary_file:
                json.dump(run_summary, run_summary_file, indent=4)

if __name__ == "__main__":
    main()
