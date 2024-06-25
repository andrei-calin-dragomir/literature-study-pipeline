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
# If not installed previously
pip install poetry

poetry install
```

## Usage
### 1. Defining a Literature Study Design

Create a study design file (e.g., `study_design.json`):
Save this file in the project directory.

Provide a copy of a `dblp.xml` file to the project's directory
_(You can download it from [here](https://dblp.uni-trier.de/xml/dblp.xml.gz))_

### 2. Running the Pipeline

**NOTE** Run the experiment in the poetry shell: 
```bash
poetry shell
```

Execute the main script with your study design file and dblp of choice:

```bash
python main.py --study_design input/study_design.json --dblp dblp27052024.xml
```

The pipeline will process the literature and provide you with a selection of papers filtered based on your inclusion/exclusion criteria.

**NOTE** You can specify the number of papers to be assessed by using the `--batch` flag followed by the desired number. Otherwise the pipeline will attempt processing all papers extracted.

**NOTE** You can resume a pipeline process that was stopped midway by setting the `--resume` flag followed by the directory name in results that you want to resume.

**NOTE** You can let the pipeline run on its own by adding the `--auto` flag. (It will not ask for your confirmation on each step)

### 3. Output

The outputs of each run of the pipeline will be found in the `results` directory.
The output of your current run will be named based on the current date and the experiment number of today (`<date>_<number>/`).
In this directory, you will find the output data separated per each pipeline phase along with an experiment overview.
