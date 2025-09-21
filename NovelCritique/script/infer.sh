CUDA_VISIBLE_DEVICES=0 \
  python ../predict/infer.py \
    --pretrained_model_loc ../pretrained/Meta-Llama-3.1-8B-Instruct/ \
    --tuned_model_loc ../output/long_story_eval/checkpoint/ \
    --prompt_format_loc ../predict/prompt_format/ \
    --test_file ../data/test_infos.json \
    --temperature 0.0 \
    --output_loc ../predict/output/long_story_eval/run_0/Overall/