# literature-study-pipeline
## Overview
The literature-study-pipeline is an application designed to facilitate the process of conducting a literature study. Researchers can define their study design, including the research questions, and the pipeline processes relevant literature to extract information that answers those questions. This streamlined approach aids researchers in composing their papers based on the provided information.

## Installation

To install literature-study-pipeline, follow these steps:

Clone the repository:
```bash
git clone https://github.com/andrei-calin-dragomir/literature-study-pipeline.git
```

Navigate to the project directory:

```bash
cd literature-study-pipeline
```

Install the project using Poetry:
```bash
pip install poetry #If poetry not installed previously
```
```bash
poetry install
```

## Usage
### 1. Required Inputs

#### Study
Create a study file (e.g., `study_input.json`) with the following entries:
| Fields                        | Type       | Description                                                 | Requirement |
|-------------------------------|------------|-------------------------------------------------------------|-------------|
| study_name                    | str        | The name of the study.                                      |**MANDATORY**|
| inclusion_criteria            | [str]      | Criteria for including a paper in the study.                |**MANDATORY**|
| exclusion_criteria            | [str]      | Criteria for excluding a paper from the study.              |**MANDATORY**|
| year_min                      | int        | Earliest year of publication for the papers to be included. |**MANDATORY**|
| year_max                      | int        | Latest year of publication for the papers to be included.   |**MANDATORY**|
| search_word_groups            | [str]      | Search term sets used to find relevant papers.              |**MANDATORY**|
| research_goal                 | str        | The primary objective of the study.                         | OPTIONAL    |
| research_questions            | [str]      | Specific research questions the study aims to address.      | OPTIONAL    |
| accepted_venue_types          | [str]      | Accepted venue types (as codes). E.g. `conf` or `journals`  | OPTIONAL    |
| venue_rank_threshold          | str        | Minimum acceptable rank of the publication venues. E.g. `B` | OPTIONAL    |
| manually_accepted_venue_codes | [str]      | Manually accepted venues E.g. `conf/ipccc`                  | OPTIONAL    |


#### DBLP Source
Provide a copy of a `dblp.xml` file to the project's directory
_(You can download it from [here](https://dblp.uni-trier.de/xml/dblp.xml.gz))_

### 2. Running the Pipeline

Add your OpenAI API key in the `.env` file.

**NOTE** Run the experiment in the poetry shell: 
```bash
poetry shell
```

Execute the main script with your study file and dblp of choice:

```bash
python study_runner.py --study study_input.json --dblp data/dblp20240707.xml
```

The pipeline will process the literature and provide you with a selection of papers filtered based on your inclusion/exclusion criteria.

- **NOTE** You can specify the number of papers to be assessed by using the `--batch` flag followed by the desired number. Otherwise the pipeline will attempt processing papers exhaustively.

- **NOTE** You can also specify if you want the final set of papers to be exported using `--export` flag followed by the export level of detail (`complete` OR `overview`)

### 3. Exported Data (TODO)

## Study Flow
### 1. Paper Scraping and Filtering
_Implemented in the `PaperFactory` class._

Summary of the paper extraction sequence
  - Venue Type Check: Validates if the paper's venue type is accepted.
  - Year Check: Ensures the publication year is within the specified range.
  - Title Check: Matches the paper title against the search query.
  - Metadata Creation: Constructs a ResearchPaper object with initial metadata.
  - Identifier Addition: Adds DOI and publisher source information.
  - Venue Information Addition: Includes venue type, code, and rank.
  - Paper Validation: Validates the paper based on venue key and rank.
  - Data Fetching: Retrieves additional data like the abstract if needed.

### 2. Automated Paper-Criteria Analysis (TODO)
_Implemented in the `PaperInterpreter` class._
