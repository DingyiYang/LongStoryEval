python ../eval_with_api/api_eval_with_chaps.py \
  --run_model gpt-4o \
  --book_loc ../../dataset/books_json/ \
  --sum_loc ../../dataset/summaries/ \
  --output_loc ../outputs/aggre_based/gpt-4o/run_1/ \
  --prompt_loc ../prompt_template/aggregation/ \
  --book_info_loc ../../dataset/all_book_info.json \
  --debug