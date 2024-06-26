import os
import csv
import json
from openai import OpenAI

# Replace with your OpenAI API key
client = OpenAI(
    api_key=''
)

json_assessment_schema : json = {
    "type": "object",
    "properties": {
        "inclusion_criteria_assessments": {
            "type": "array",
            "description": "Assessment results for each inclusion criteria.",
            "items": {
                "type": "object",
                "properties": {
                    "assessment": {
                        "type": "string",
                        "description": "Description of reasoning behind assessment."
                    },
                    "value": {
                        "type": "boolean",
                        "description": "Criteria assessment result."
                    }
                }
            }
        },
        "exclusion_criteria_assessments": {
            "type": "array",
            "description": "Assessment results for each exclusion criteria.",
            "items": {
                "type": "object",
                "properties": {
                    "assessment": {
                        "type": "string",
                        "description": "Description of reasoning behind assessment."
                    },
                    "value": {
                        "type": "boolean",
                        "description": "Criteria assessment result."
                    }
                }
            }
        },
        "conclusion": {
            "type": "string",
            "description": "Brief conclusion based on the criteria assessments"
        }
    },
    "required": ["inclusion_criteria_assessments", "exclusion_criteria_assessments", "conclusion"]
}

def request_assessment(abstract, inclusion_criteria, exclusion_criteria):
    # Construct the prompt
    inclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(inclusion_criteria)])
    exclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(exclusion_criteria)])
    
    prompt = f"""
    Given the user provided abstract, assess whether the abstract meets the following inclusion and exclusion criteria:

    Inclusion Criteria:
    {inclusion_criteria_text}

    Exclusion Criteria:
    {exclusion_criteria_text}

    Provide the assessment in JSON format following this schema:
    {json_assessment_schema}
    """

    # Call the OpenAI API to evaluate the abstract
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": abstract}],
        # max_tokens=300
    )

    # Return the result
    return response.choices[0].message.content

def assess_abstracts(inclusion_criteria, exclusion_criteria, input_csv, output_csv, total_runs, starting_point=0):
    assessments_processed = 0
    # Initialize the language model pipeline
    try:
        with open(input_csv, newline='', encoding='utf-8') as input_file, open(output_csv, 'a', newline='', encoding='utf-8') as output_file:
            csv_reader = csv.reader(input_file)
            rows = list(csv_reader)
            csv_writer = csv.DictWriter(output_file, fieldnames=rows[0])

            # 1 starting index for the header
            for _, row in enumerate(rows[starting_point if starting_point > 0 else 1:total_runs], starting_point):
                paper_index = row[0]
                abstract = row[1]

                results = request_assessment(abstract, inclusion_criteria, exclusion_criteria)
                results_data = json.loads(results)

                # Write the result to the CSV file
                csv_writer.writerow({
                    'index': paper_index,
                    'inclusion_results': [result['value'] for result in results_data['inclusion_criteria_assessments']],
                    'exclusion_results': [result['value'] for result in results_data['exclusion_criteria_assessments']],
                    'inclusion_comments': [result['assessment'] for result in results_data['inclusion_criteria_assessments']],
                    'exclusion_comments': [result['assessment'] for result in results_data['exclusion_criteria_assessments']],
                    'conclusion': results_data['conclusion']
                })
                assessments_processed += 1
            return assessments_processed
    except OSError or Exception as e:
        raise(f"Error during processing:{e}")

if __name__ == "__main__":
    # Example usage
    abstract = """
    Microservices enable a fine-grained control over the cloud applications that they constitute and thus became widely-used in the industry. Each microservice implements its own functionality and communicates with other microservices through language- and platform-agnostic API. The resources usage of microservices varies depending on the implemented functionality and the workload. Continuously increasing load or a sudden load spike may yield a violation of a service level objective (SLO). To characterize the behavior of a microservice application which is appropriate for the user, we define a MicroService Capacity (MSC) as a maximal rate of requests that can be served without violating SLO. The paper addresses the challenge of identifying MSC individually for each microservice. Finding individual capacities of microservices ensures the flexibility of the capacity planning for an application. This challenge is addressed by sandboxing a microservice and building its performance model. This approach was implemented in a tool Terminus. The tool estimates the capacity of a microservice on different deployment configurations by conducting a limited set of load tests followed by fitting an appropriate regression model to the acquired performance data. The evaluation of the microservice performance models on microservices of four different applications shown relatively accurate predictions with mean absolute percentage error (MAPE) less than 10%. The results of the proposed performance modeling for individual microservices are deemed as a major input for the microservice application performance modeling.
    """

    inclusion_criteria = [
        "Study is written in English",
        "Must contain methods that orchestrate containers",
        "The method(s) used must take into account measurements and/or predictions",
        "Study contains an empirical evaluation of the policies presented"
    ]

    exclusion_criteria = [
        "Methods presented are orchestrating VMs or containers deployed within VMs",
        "The method does not produce policies that optimize performance resource-wise"
    ]

    # Call the function
    # result = request_assessment(abstract, inclusion_criteria, exclusion_criteria)
    result = assess_abstracts(inclusion_criteria, exclusion_criteria)
    print(result)
