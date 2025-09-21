<div align="center">

<h2>What Matters in Evaluating Book-Length Stories? <br> A Systematic Study of Long Story Evaluation</h2>

Dingyi Yang, Qin Jin 

</div>

## Abstract
In this work, we conduct systematic research in a challenging area: the automatic evaluation of book-length stories (>100K tokens). Our study focuses on two key questions: (1) understanding which evaluation aspects matter most to readers, and (2) exploring effective methods for evaluating lengthy stories. We introduce the first large-scale benchmark, **LongStoryEval**, comprising 600 newly published books with an average length of 121K tokens (maximum 397K). Each book includes its average rating and multiple reader reviews, presented as critiques organized by evaluation aspects. By analyzing all user-mentioned aspects, we propose an *evaluation criteria structure* and conduct experiments to identify the most significant aspects among the 8 top-level criteria. For evaluation methods, we compare the effectiveness of three types: *aggregation-based, incremental-updated*, and  *summary-based* evaluations. Our findings reveal that aggregation- and summary-based evaluations perform better, with the former excelling in detail assessment and the latter offering greater efficiency. Building on these insights, we further propose **NovelCritique**, an 8B model that leverages the efficient summary-based framework to review and score stories across specified aspects. NovelCritique outperforms commercial models like GPT-4o in aligning with human evaluations. 

## Release :loudspeaker:
- **2025/05**: Our work is accepted to ACL 2025 main conference. 
- **2025/09**: Our datasets and codes are released.

## Install
1. Clone this repository
```bash
git clone https://github.com/DingyiYang/LongStoryEval
cd LongStoryEval
```

2. Install Environment
```bash
pip install --upgrade pip
conda env create -f environment.yml
```

## Dataset
This dataset contains book metadata, book summaries, book reviews, and reviewer information. Details can be found at:  [Dataset Document](dataset/dataset.md)

## Book Evaluation with API
- **Step 0:** Put the books at ```/dataset/books_json/```
  - Due to copyright problem, we've included example books, which can be replaced with books downloaded using our book metadata `/dataset/all_book_info.json`

- **Step 1: Book Summary** - Summarize the books, achieving the chapter-level summaries
```bash
cd summarize_book
bash summarize_book.sh
```

- **Step 2: Book Evaluation (Aggregation-based & Incremental-updated & Summary-based)**
```bash
  cd evaluation_codes/scripts
  bash aggre_based_eval.sh
  bash incre_updated_eval.sh
  bash sum_based_eval.sh
```

## NovelCritique: Training and Inference 
### Training
- The training data is based on: [finetuning_code](https://github.com/taishan1994/Llama3.1-Finetuning)
- Base model can be downloaded at: [Llama-3.1-8B-Instruct](https://www.modelscope.cn/models/LLM-Research/Meta-Llama-3.1-8B-Instruct)
- The training data can be downloaded at: [train_data.json](https://entuedu-my.sharepoint.com/:u:/g/personal/dingyi_yang_staff_main_ntu_edu_sg/ETyahuNBGWxHksGY6eZU2UUB1M3_EAZfdczsTg3B5fjMnA?e=AxBTvN)
- Model Training
```bash
cd NovelCritique/script/
bash train.sh
```

### Inference
- The checkpoint can be downloaded at: [Checkpoint](https://entuedu-my.sharepoint.com/:u:/g/personal/dingyi_yang_staff_main_ntu_edu_sg/EXIuPLq9Yu9BsNvs_WttO0wBMB8XOX5lung_fJrXr07PAg?e=iQqquU)
- Infer for all aspects
```bash
cd NovelCritique/script/
bash infer.sh
```

- Inference for each aspect
```bash
cd NovelCritique/script/
bash infer_aspects.sh
```

## Evaluation Metrics
### Correlation Metrics for Aggregation-based & Incremental-Updated Outputs
```bash
cd evaluation_codes/scripts
bash aggre_based_corre.sh
bash incre_updated_corre.sh
```

### Correlation Metrics for Summary-Based Outputs
```bash
cd evaluation_codes/scripts
bash sum_based_corre.sh
```