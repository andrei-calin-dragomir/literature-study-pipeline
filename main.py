import os
import json
import argparse
import csv
import pandas as pd
import traceback
from datetime import datetime
from dotenv import load_dotenv
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

def create_new_results_file(file_name, target_directory, field_names):
    if not os.path.isdir(target_directory):
        raise NotADirectoryError(f"The directory {target_directory} does not exist or is not a directory.")
    
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)
    
    # Define the path to the new CSV file
    file_path = os.path.join(target_directory, file_name)
    
    # Create an empty CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
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
        results_directory = './results/'
        os.makedirs(results_directory, exist_ok=True)

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
        current_date = datetime.now().strftime("%d%m%Y")
        current_run_index = sum(os.path.isdir(os.path.join(results_directory, item)) and item.startswith(current_date) for item in os.listdir(results_directory))
        
        results_directory = os.path.join('./results/', args.resume if args.resume else f"{current_date}_{current_run_index}")
        os.makedirs(results_directory, exist_ok=True)
        
        run_summary = {}
        old_run_summary = load_json_data(os.path.join(results_directory, 'run_summary.json')) if args.resume else {}

        run_summary['batch_size'] = args.batch_size if args.batch_size else old_run_summary['batch_size'] if args.resume else None
        run_summary['study_design'] = old_run_summary['study_design'] if args.resume else load_json_data(args.study_design)
        run_summary['dblp_file'] = old_run_summary['dblp_file'] if args.resume else args.dblp
        run_summary['dblp_version'] = old_run_summary['dblp_version'] if args.resume else args.dblp if args.dblp.rfind('dblp') == -1 else args.dblp[args.dblp.rfind('dblp'):]

        run_summary['papers_collected'] = 0
        run_summary['abstracts_extracted'] = 0
        run_summary['assessments_processed'] = 0

        print(f"Loaded study design for study: {run_summary['study_design']['study_name']}")
        print(f"Running with this dblp: {run_summary['dblp_version']}")
        print(f"Desired batch size: {run_summary['batch_size']}")

        run_start = datetime.now()

        # Step 2: Paper extraction
        print("Next Step: Paper Extraction")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)
            
        if args.resume: 
            papers_file = os.path.join(results_directory, 'papers.csv') 
        else: 
            papers_file = create_new_results_file('papers.csv', results_directory, ['hit','title','year','authors','key','ee'])
        number_of_papers = old_run_summary['papers_collected'] if args.resume else 0

        # If number of papers does not satisfy batch size
        if number_of_papers < run_summary['batch_size']:
            number_of_papers = extract_dblp_papers(run_summary['dblp_file'], run_summary['study_design']['venue_codes'], 
                                run_summary['study_design']['year_min'], run_summary['study_design']['year_max'], 
                                run_summary['study_design']['search_words'], papers_file)
        
        if number_of_papers < run_summary['batch_size']:
            print(f'Number of papers collected does not satisfy desired batch size ({run_summary['batch_size']}) found only {number_of_papers}')
            if not user_confirmation("Proceed with this selection?", args.auto):
                return
            run_summary['batch_size'] = number_of_papers

        run_summary['papers_collected'] = number_of_papers
        print(f"Total papers collected: {number_of_papers}")

        # Step 3: Abstracts extraction
        print("Next Step: Abstracts Extraction")
        if not user_confirmation("Proceed with this step?", args.auto):
            return

        if args.resume:
            abstracts_file = os.path.join(results_directory, 'abstracts.csv') 
        else:
            abstracts_file = create_new_results_file('abstracts.csv', results_directory, ['index','abstract'])

        abstracts_file_size = old_run_summary['abstracts_extracted'] if args.resume else 0

        # If number of abstracts does not satisfy batch_size
        if abstracts_file_size < run_summary['batch_size']:
            if abstracts_file_size > 1:
                print('Abstracts found but incomplete. Resuming previous abstract extraction...')
            else:
                print('No abstracts found. Starting new abstract extraction...')
            run_summary['abstracts_extracted'] = extract_abstracts_from_papers(papers_file, abstracts_file, run_summary['batch_size'], abstracts_file_size)
            print(f"Total abstracts collected: {run_summary['abstracts_extracted']}")
        else:
            print("Abstracts found are sufficient.")

        # Step 4: Criteria assessments
        print("Next Step: Criteria assessments based on abstracts")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)

        if args.resume:
             criteria_file = os.path.join(results_directory, 'criteria_assessments.csv') 
        else:
            criteria_file = create_new_results_file('criteria_assessments.csv', results_directory,
                                    ['index','inclusion_results','exclusion_results','inclusion_comments','exclusion_comments','conclusion'])
        criteria_file_size = old_run_summary['assessments_processed'] if args.resume else 0
            
        if criteria_file_size < run_summary['batch_size']:
            if criteria_file_size > 1:
                print("Assessments found but incomplete. Resuming previous criteria assessments process...")
            else:
                print('No criteria assessments found. Starting new criteria assessments process...')
            run_summary['assessments_processed'] = assess_abstracts(run_summary['study_design']['inclusion_criteria'], run_summary['study_design']['exclusion_criteria'], 
                                abstracts_file, criteria_file, run_summary['batch_size'], criteria_file_size)
            print(f"Total criteria assessments: {run_summary['assessments_processed']}")
        else:
            print("Criteria assessments found are sufficient.")
    
    except Exception as e:
        print(traceback.format_exc())
        # print(e)
    finally:
        run_summary['run_duration'] = str(datetime.now() - run_start)
        print(f'Process finished/terminated. This run took: {run_summary['run_duration']}')
        with open(os.path.join(results_directory, 'run_summary.json'), 'w') as run_summary_file:
                json.dump(run_summary, run_summary_file, indent=4)

if __name__ == "__main__":
    load_dotenv()
    main()
