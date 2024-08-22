from openai import OpenAI
from utils.json_utils import load_json, load_json_from_string, validate
from database.models import CriteriaAssessment, LickertScale
import os
from typing import List, Optional

class PaperInterpreter:
    def __init__(self, api_key : str | None):
        # Replace with your OpenAI API key
        self.client = OpenAI(api_key=api_key)

        # Load validation schemas
        self.criteria_assessment_schema = load_json(os.path.join('schemas', 'criteria_assessment_schema.json'))
        
    def get_criteria_assessments(self, content: str, inclusion_criteria: list[str]) -> Optional[List[CriteriaAssessment]]:
            # Construct the prompt
            inclusion_criteria_text = "\n".join([f"{i+1}. {criteria}" for i, criteria in enumerate(inclusion_criteria)])
            
            prompt = f"""
            “Assume you are a software engineering researcher conducting a systematic literature review (SLR). 
            Consider the title and abstract of a primary study.
            Using a 1-7 Likert scale (1 - Strongly disagree, 2 - Disagree, 3 - Somewhat disagree, 4 - Neither agree nor disagree, 5 - Somewhat agree, 6 - Agree, and 7 - Strongly agree) rate your agreement with each of the following statements:

            {inclusion_criteria_text}

            Your should only provide a RFC8259 compliant JSON response following this format without deviation:
            {
                "ratings": [
                    "2",
                    "4",
                    "1",
                    ...
                ]
            }

            Lastly, keep the same order in your ratings as the order of the provided statements.
            """
            try:
                # Call the OpenAI API to evaluate the abstract
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    response_format={ "type": "json_object" },
                    messages=[{"role": "system", "content": prompt},
                            {"role": "user", "content": content}],
                    temperature=0,
                    top_p=0.1,
                )

                response_data = load_json_from_string(response.choices[0].message.content)
                if response_data:
                    validate(instance=response_data, schema=self.criteria_assessment_schema)
                    assessments : list[CriteriaAssessment] = self._wrap_criteria_assessments(response_data['ratings'],
                                                                                             inclusion_criteria)
                    return assessments
            except Exception as e:
                print(e)
                return None
    
    @staticmethod
    def _wrap_criteria_assessments(assessment_data, criteria) -> List[CriteriaAssessment]:
        result = []
        for index, data in enumerate(assessment_data):
            assessment = CriteriaAssessment(
                criteria = criteria[index],
                lickert_value = LickertScale['_' + data],
            )
            result.append(assessment)
        return result
