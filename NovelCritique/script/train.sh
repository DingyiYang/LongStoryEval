NCCL_P2P_DISABLE=1 \
NCCL_IB_DISABLE=1 \
CUDA_VISIBLE_DEVICES=0,1,2,3 \
python -m torch.distributed.run \
--nproc_per_node 4 \
--nnodes 1 \
--node_rank 0 \
--master_addr localhost \
--master_port 6601 \
../finetune_llama3.py \
--model_name_or_path "../pretrained/Meta-Llama-3.1-8B-Instruct/" \
--data_path "../data/train_data.json" \
--fp16 True \
--output_dir "../output/long_story_eval/" \
--num_train_epochs 4 \
--per_device_train_batch_size 4 \
--per_device_eval_batch_size 4 \
--gradient_accumulation_steps 8 \
--evaluation_strategy "no" \
--save_strategy "steps" \
--save_steps 50 \
--save_total_limit 50 \
--learning_rate 1e-5 \
--weight_decay 0.1 \
--adam_beta2 0.95 \
--warmup_ratio 0.01 \
--lr_scheduler_type "cosine" \
--logging_steps 20 \
--report_to "none" \
--model_max_length 4096 \
--gradient_checkpointing True \
--lazy_preprocess True \
--deepspeed "../config/ds_config_zero2.json" \
--use_lora
