python ../eval_with_api/api_eval_with_sum.py \
  --run_model gpt-4o \
  --book_loc ../../dataset/books_json/ \
  --sum_loc ../../dataset/summaries/ \
  --output_loc ../outputs/sum_based/gpt-4o/run_1/ \
  --prompt_template ../prompt_template/no_criteria.txt \
  --book_info_loc ../../dataset/all_book_info.json \
  --debug