import os
import csv
import json
from openai import OpenAI
from utils.file_io import load_json_data

CRITERIA_ASSESSMENT_SCHEMA : json = {
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

class LLM_Processor:
    def __init__(self, study_design, api_key):
        # Replace with your OpenAI API key
        self.client = OpenAI(
            api_key=api_key
        )
        self.study_design = study_design
        
    def request_criteria_assessment(self, content):
            inclusion_criteria = self.study_design['inclusion_criteria']
            exclusion_criteria = self.study_design['exclusion_criteria']

            # Construct the prompt
            inclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(inclusion_criteria)])
            exclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(exclusion_criteria)])
            
            prompt = f"""
            You are a text parser that receives sections extracted from research papers.

            Given the user provided section, assess whether the section meets the following inclusion and exclusion criteria:

            Inclusion Criteria:
            {inclusion_criteria_text}

            Exclusion Criteria:
            {exclusion_criteria_text}

            Provide the assessment in JSON format following this schema:
            {CRITERIA_ASSESSMENT_SCHEMA}
            """

            # Call the OpenAI API to evaluate the abstract
            response = self.client.chat.completions.create(
                model="gpt-4o",
                response_format={ "type": "json_object" },
                messages=[{"role": "system", "content": prompt},
                        {"role": "user", "content": content}],
                # max_tokens=300
            )

            response_data = load_json_data(response.choices[0].message.content, CRITERIA_ASSESSMENT_SCHEMA)
            
            if response_data:
                return {
                        'inclusion_results': [bool(result['value']) for result in response_data['inclusion_criteria_assessments']],
                        'exclusion_results': [bool(result['value']) for result in response_data['exclusion_criteria_assessments']],
                        'inclusion_comments': [result['assessment'] for result in response_data['inclusion_criteria_assessments']],
                        'exclusion_comments': [result['assessment'] for result in response_data['exclusion_criteria_assessments']],
                        'conclusion': response_data['conclusion']
                }
            else:
                return None 

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

    processor = LLM_Processor({
        'inclusion_criteria' : inclusion_criteria,
        'exclusion_criteria' : exclusion_criteria
    })

    # Call the function
    result = processor.request_criteria_assessment(abstract)

    print(result)
