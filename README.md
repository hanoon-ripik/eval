# eval

```
python3 -m venv eval
source eval/bin/activate
pip install -r requirements.txt
```

This is the complete Evaluation for Ripik Vision Platform
The repository contains folder for different types of tasks - Counting, OCR, Classification, along with the use cases in them, within it.

Each folder mentioned above has 3 dfferent folders under it - Data, Evaluation and Inference, under each, there will be seperate folder for hte use case mentione above

The Data folder contains all the data needed for that type.
Each use case folder here will have a
1. clean.json - Manually annotated data, consider it as golden dataset
2. raw.json - Raw data downloaded from production data

Inference folder contains all files needed to run inference/test for the use case

Evaluation folder contains all the files needed to get the metrics ready for the use case.