# trailSomeAlphas Pipeline

This folder bundles **brain-data-feature-engineering** and **brain-feature-implementation** so it can run independently.

## Setup

1) Fill BRAIN credentials:
- Edit skills/brain-feature-implementation/config.json

2) Set Moonshot API key (do not store in files):
- Windows PowerShell:
  - $Env:MOONSHOT_API_KEY = "<your_api_key>"

Optional:
- Set base URL if needed: MOONSHOT_BASE_URL (default https://api.moonshot.cn/v1)

## Run

From this folder:

- Generate ideas + implement expressions:
  - python run_pipeline.py --data-category analyst --region USA --delay 1 --universe TOP3000

- Use an existing ideas markdown:
  - python run_pipeline.py --data-category analyst --region USA --delay 1 --ideas-file <path_to_ideas.md>

## Output

- Ideas report:
  - skills/brain-data-feature-engineering/output_report/{region}_delay{delay}_{datasetId}_ideas.md

- Final expressions:
  - skills/brain-feature-implementation/data/{datasetId}_{region}_delay{delay}/final_expressions.json

## Notes

- The ideas report must include `Implementation Example` entries that use {variable} placeholders.
- The implementation step reads templates from backticks with `{variable}` placeholders.
