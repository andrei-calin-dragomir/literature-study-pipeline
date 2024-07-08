import os
import argparse
import traceback
from dotenv import load_dotenv
from study_runner import StudyRunner

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

def main():
    try:
        parser = argparse.ArgumentParser(description="Process the study design pipeline with various options.")
        parser.add_argument('--study_design_path', type=str, help='The path to the study to be used')
        parser.add_argument('--dblp_path', type=str, help='Specify the path to your dblp')
        parser.add_argument('--output_path', type=str, help='Specify where to store outputs')
        parser.add_argument('--batch_size', type=int, help='Number of papers to process in current run')
        parser.add_argument('--resume', type=str, help='Specify the path to your results directory to resume processing')
        parser.add_argument('--auto', action='store_true', help='Do not ask for user confirmation before moving to the next step')

        args = parser.parse_args()

        # Step 0: Parse run arguments
        if args.resume:
            if not os.path.exists(args.resume):
                print(f"Path to provided previous study not found on: {args.study_design}")
                exit(0)
            if args.study_design_path or args.dblp_path:
                print('You must start a fresh run if you do not want to use the same study design/dblp file as the previous run')
                exit(0)
            if args.batch_size:
                print('You must start a fresh run if you want a different batch size.')
                exit(0)
            if args.output_path:
                print('Output path will not be changed, you will find the outputs in the previous results directory.')
                exit(0)
        else:
            if not args.study_design_path or not args.dblp_path:
                print('For a new run, both a study as well as a dblp file need to be specified')
                exit(0)
            elif not os.path.exists(args.study_design_path):
                print(f"Study design file not found on path {args.study_design_path}")
                exit(0)
            elif not os.path.exists(args.dblp_path):
                print(f"Dblp file not found on path {args.dblp}")
                exit(0)

        results_path = args.output_path if args.output_path else os.getenv('OUTPUT_DIRECTORY') 
        llm_key = os.getenv('OPENAI_API_KEY')

        # Step 1: Setup configuration of the current run
        study = StudyRunner(args.study_design_path, args.dblp_path, results_path, llm_key) if not args.resume else StudyRunner.reload(args.resume, llm_key)
        study.gather_papers(args.batch_size if args.batch_size else -1)
    
    except Exception as e:
        print(traceback.format_exc())

if __name__ == "__main__":
    load_dotenv()
    main()
