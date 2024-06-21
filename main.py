import os
import json
import argparse
import pandas as pd
from datetime import datetime
from abstract_scraper import extract_abstracts_from_papers
from paper_scraper import extract_dblp_papers
from filter_papers_on_criteria import assess_abstracts


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


def count_directories_with_prefix(directory_path: str, prefix: str) -> int:
    return sum(
        os.path.isdir(os.path.join(directory_path, item)) and item.startswith(prefix)
        for item in os.listdir(directory_path)
    )


def load_study_design(json_file_path) -> dict:
    try:
        with open(json_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Study design file not found: {json_file_path}")
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

def prepare_results_directory(results_directory, resume=None):
    if resume:
        results_directory = os.path.join(results_directory, resume)
    else:
        current_date = datetime.datetime.now().strftime("%d%m%Y")
        results_directory = os.path.join(
            results_directory, f"{current_date}_{count_directories_with_prefix(results_directory, current_date)}"
        )
    os.makedirs(results_directory, exist_ok=True)
    return results_directory


def handle_dblp_file(dblp_xml_path):
    if not os.path.exists(dblp_xml_path):
        print(f"Dblp file not found on path {dblp_xml_path}")
        exit(0)
    print("Running with the dblp database provided.")


def main():
    try:
        parser = argparse.ArgumentParser(description="Process the study design pipeline with various options.")
        parser.add_argument('--study_design', type=str, help='The path to the study to be used')
        parser.add_argument('--dblp', type=str, help='Specify the path to your dblp')
        parser.add_argument('--batch_size', type=int, help='Number of papers to process in current run')
        parser.add_argument('--resume', type=str, help='Specify the path to your results directory to resume processing')
        parser.add_argument('--auto', action='store_true', help='Do not ask for user confirmation before moving to the next step')

        args = parser.parse_args()

        results_directory = prepare_results_directory('./results/', args.resume)

        run_summary = {}
        old_run_summary = {}
        with open(os.path.join(results_directory, 'run_summary.json'), 'r') as file:
                old_run_summary = json.load(file)
        run_summary['run_start'] = datetime.now()

        # Step 1: Load study design of the current run
        if args.resume and not args.study_design:
            study_design = {}
            study_design = old_run_summary['study_design']
        else:
            study_design = load_study_design(args.study_design)
        
        run_summary['study_design'] = study_design
        print(f"Loaded study design: {args.study_design}")
        
        # Step 2: Paper extraction
        print("Next Step: Paper Extraction")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)

        papers_file = os.path.join(results_directory, 'papers.csv') if args.resume else create_new_file('papers.csv', results_directory)
        

        if args.resume:
            run_summary['dblp'] = old_run_summary['dblp']
        else:
            if args.dblp:
                handle_dblp_file(args.dblp)
                run_summary['dblp'] = args.dblp if args.dblp.rfind('dblp') == -1 else args.dblp[args.dblp.rfind('dblp'):]
            else:
                print("You need to specify a dblp.xml file to be used.")
                exit(0)
            extract_dblp_papers(args.dblp, study_design['venues'], study_design['year_min'], study_design['year_max'], study_design['search_words'], papers_file)
            
        number_of_papers = len(pd.read_csv(papers_file))
        run_summary['papers_collected'] = number_of_papers
        print(f"Total papers collected: {number_of_papers}")

        # Step 3: Abstracts extraction
        print("Next Step: Abstracts Extraction")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)

        abstracts_file = os.path.join(results_directory, 'abstracts.csv') if args.resume else create_new_file('abstracts.csv', results_directory)
        abstracts_file_size = len(pd.read_csv(abstracts_file))

        if args.resume and abstracts_file_size != 0:
            if args.batch:
                if abstracts_file_size < args.batch:
                    print("Abstracts found but insufficient. Resuming previous abstract extraction...")
                    extract_abstracts_from_papers(papers_file, abstracts_file,  args.batch, abstracts_file_size)
                else:
                    print("Abstracts found are sufficient.")
            elif abstracts_file_size < number_of_papers:
                print("Abstracts found but incomplete. Resuming previous abstract extraction...")
                extract_abstracts_from_papers(papers_file, abstracts_file, number_of_papers, abstracts_file_size)
        else:
            extract_abstracts_from_papers(papers_file, abstracts_file, 
                                          args.batch if args.batch else number_of_papers, abstracts_file_size)

        number_of_abstracts = len(pd.read_csv(abstracts_file))
        run_summary['abstracts_collected'] = number_of_abstracts
        print(f"Total abstracts collected: {number_of_abstracts}")

        # Step 4: Criteria assessments
        print("Next Step: Criteria assessments based on abstracts")
        if not user_confirmation("Proceed with this step?", args.auto):
            exit(0)

        criteria_file = os.path.join(results_directory, 'criteria_assessments.csv') if args.resume else create_new_file('criteria_assessments.csv', results_directory)
        criteria_file_size = len(pd.read_csv(criteria_file))
            
        if args.resume and criteria_file_size != 0:
            if args.batch:
                if criteria_file_size < args.batch:
                    print("Assessments found but insufficient. Resuming criteria assessments...")
                    assess_abstracts(study_design['inclusion_criteria'], study_design['exclusion_criteria'], 
                                     abstracts_file, criteria_file, args.batch, criteria_file_size)
                else:
                    print("Assessments found are sufficient.")
            elif criteria_file_size < number_of_papers:
                print("Abstracts found but incomplete. Resuming previous abstract extraction...")
                assess_abstracts(study_design['inclusion_criteria'], study_design['exclusion_criteria'], 
                                 abstracts_file, criteria_file, number_of_papers, criteria_file_size)
        else:
            assess_abstracts(study_design['inclusion_criteria'], study_design['exclusion_criteria'], abstracts_file, 
                             args.batch if args.batch else number_of_papers, criteria_file)
        
        number_of_criteria_assessments = len(pd.read_csv(abstracts_file))
        run_summary['criteria_assessments'] = number_of_criteria_assessments
        print(f"Total criteria assessments: {number_of_criteria_assessments}")
    
    except Exception as e:
        print(e)
    finally:
        run_summary['run_end'] = datetime.now()
        with open(os.path.join(results_directory, 'run_summary.json'), 'w') as run_summary_file:
                json.dump(run_summary, run_summary_file, indent=4)

if __name__ == "__main__":
    main()
