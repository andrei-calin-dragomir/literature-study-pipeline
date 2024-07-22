from openai import OpenAI
from utils.json_utils import load_json, load_json_from_string, validate
from database.models import CriteriaAssessment, CriteriaType
import os
from typing import List, Optional

class PaperInterpreter:
    def __init__(self, api_key : str | None):
        # Replace with your OpenAI API key
        self.client = OpenAI(api_key=api_key)

        # Load validation schemas
        self.criteria_assessment_schema = load_json(os.path.join('schemas', 'criteria_assessment_schema.json'))
        
    def get_criteria_assessments(self, content: str, inclusion_criteria: list[str], exclusion_criteria: list[str]) -> Optional[List[CriteriaAssessment]]:
            # Construct the prompt
            inclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(inclusion_criteria)])
            exclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(exclusion_criteria)])
            
            prompt = f"""
            You are a text parser that receives sections extracted from research papers and generates a JSON response.
            Given the user provided content, assess whether the research paper meets the following inclusion and exclusion criteria:

            Inclusion Criteria:
            {inclusion_criteria_text}

            Exclusion Criteria:
            {exclusion_criteria_text}

            Your should only provide a RFC8259 compliant JSON response following this format without deviation:
            {{
                "inclusion_criteria_assessments": [
                    {{
                        "assessment": "Description of reasoning behind assessment.",
                        "value": true
                    }}
                ],
                "exclusion_criteria_assessments": [
                    {{
                        "assessment": "Description of reasoning behind assessment.",
                        "value": false
                    }}
                ]
            }}

            Lastly, keep the same order for both inclusion and exclusion criterias.
            """
            try:
                # Call the OpenAI API to evaluate the abstract
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    response_format={ "type": "json_object" },
                    messages=[{"role": "system", "content": prompt},
                            {"role": "user", "content": content}],

                    max_tokens=50 * (len(inclusion_criteria) + len(exclusion_criteria))
                )

                response_data = load_json_from_string(response.choices[0].message.content)
                if response_data:
                    validate(instance=response_data, schema=self.criteria_assessment_schema)
                    assessments : list[CriteriaAssessment] = self._wrap_criteria_assessments(response_data['inclusion_criteria_assessments'],
                                                                                             inclusion_criteria, CriteriaType.inclusion)
                    assessments.extend(self._wrap_criteria_assessments(response_data['exclusion_criteria_assessments'],
                                                                       inclusion_criteria, CriteriaType.exclusion))
                    return assessments
            except Exception as e:
                print(e)
                return None
    
    @staticmethod
    def _wrap_criteria_assessments(assessment_data, criteria, assessment_type) -> List[CriteriaAssessment]:
        result = []
        for index, data in enumerate(assessment_data):
            assessment = CriteriaAssessment(
                type = assessment_type,
                criteria = criteria[index],
                reason = data['assessment'],
                fulfilled = data['value']
            )
            result.append(assessment)
        return result
    
# class LLM_PDF_Processor(LLM_Processor):
#     def __init__(self, unique_id: str, pdf_path: str):
#         self.unique_id = unique_id
#         self.document = apdf.Document(pdf_path)
#         self.index_map = self._create_index_map()
            
#     def _create_index_map(self) -> dict:
#         """
#         Create an index map of section titles to their respective starting positions in the PDF.
#         """
#         index_map = {}
#         titles = SECTION_HEADERS
#         for i, page in enumerate(self.document.pages):
#             text = page.extract_text()
#             for title in titles:
#                 if title in text:
#                     index_map[title] = i
#         return index_map

#     def get_section_content(self, title: str) -> str:
#         """
#         Get the content of a given section by its title.
        
#         :param title: The title of the section.
#         :return: The content of the section.
#         """
#         if title not in self.index_map:
#             return ""
        
#         start_page = self.index_map[title]
#         end_page = len(self.document.pages) - 1
        
#         titles = list(self.index_map.keys())
#         current_title_index = titles.index(title)
        
#         if current_title_index < len(titles) - 1:
#             next_title = titles[current_title_index + 1]
#             end_page = self.index_map[next_title] - 1
        
#         section_content = ""
#         for page_num in range(start_page, end_page + 1):
#             section_content += self.document.pages[page_num].extract_text()
        
#         return section_content.strip()

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

    processor = PaperInterpreter({
        'inclusion_criteria' : inclusion_criteria,
        'exclusion_criteria' : exclusion_criteria
    })

    # Call the function
    results = processor.request_criteria_assessments(abstract)

    print(results)
