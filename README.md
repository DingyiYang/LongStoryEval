<div align="center">

<h2>What Matters in Evaluating Book-Length Stories? <br> A Systematic Study of Long Story Evaluation</h2>

Dingyi Yang, Qin Jin 

</div>

## Abstract
In this work, we conduct systematic research in a challenging area: the automatic evaluation of book-length stories (>100K tokens). Our study focuses on two key questions: (1) understanding which evaluation aspects matter most to readers, and (2) exploring effective methods for evaluating lengthy stories. We introduce the first large-scale benchmark, **LongStoryEval**, comprising 600 newly published books with an average length of 121K tokens (maximum 397K). Each book includes its average rating and multiple reader reviews, presented as critiques organized by evaluation aspects. By analyzing all user-mentioned aspects, we propose an *evaluation criteria structure* and conduct experiments to identify the most significant aspects among the 8 top-level criteria. For evaluation methods, we compare the effectiveness of three types: *aggregation-based, incremental-updated*, and  *summary-based* evaluations. Our findings reveal that aggregation- and summary-based evaluations perform better, with the former excelling in detail assessment and the latter offering greater efficiency. Building on these insights, we further propose **NovelCritique**, an 8B model that leverages the efficient summary-based framework to review and score stories across specified aspects. NovelCritique outperforms commercial models like GPT-4o in aligning with human evaluations. 

## Release :loudspeaker:
- **2025/05**: Our work is accepted to ACL 2025 main conference. All our datasets and codes will be released soon!
