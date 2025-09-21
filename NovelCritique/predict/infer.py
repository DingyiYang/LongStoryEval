import os
import sys
from peft import PeftModel, PeftConfig, LoraModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from datasets import load_dataset
import torch
import random
import json
import argparse

adapter_name = "self"

aspects_order = ["Plot and Structure","Characters","Writing and Language","World-Building and Setting","Themes","Emotional Impact","Enjoyment and Engagement","Expectation Fulfillment"]


def get_result(model_inputs, model, tokenizer, temperature=0.0, do_sample=False, top_p=0.8):

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=3000,
        eos_token_id=tokenizer.eos_token_id,
        temperature=temperature,
        do_sample=do_sample,
        top_p=top_p
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretrained_model_loc", type=str, default="../pretrained/Meta-Llama-3.1-8B-Instruct/")
    parser.add_argument("--tuned_model_loc", type=str, default="../output/long_story_eval/checkpoint/")
    parser.add_argument("--prompt_format_loc", type=str, default="../predict/prompt_format/")
    parser.add_argument("--output_loc", type=str, default="../predict/output/long_story_eval/run_0/Overall")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--do_sample", action="store_true")
    parser.add_argument("--top_p", type=float, default=0.8)
    parser.add_argument("--test_file", type=str, default="../data/test_infos.json")
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    output_loc = args.output_loc
    if not os.path.exists(output_loc):
        os.makedirs(output_loc)

    base_model_path = args.pretrained_model_loc
    peft_model_id = args.tuned_model_loc
    question_loc = args.prompt_format_loc
    device = "cuda"
    quantization_config = None
    model = AutoModelForCausalLM.from_pretrained(base_model_path,
                                                device_map="auto",
                                                quantization_config=quantization_config)
    tokenizer = AutoTokenizer.from_pretrained(peft_model_id)
    lora_config = PeftConfig.from_pretrained(peft_model_id)
    model = PeftModel.from_pretrained(model, peft_model_id, adapter_name=adapter_name, config=lora_config)
    model.eval()

    aspects_order = ["**{}:**\n".format(ts)+"Review of "+ts+"." for ts in aspects_order]
    t_aspect = "\n\n".join(aspects_order)

    test_file = json.load(open(args.test_file))
    for genre in test_file.keys():
        for book in test_file[genre]:
            print(book["id"])
            print("score: ", book["score"])
            right_score = book["score"]
            prompt = open("{}/{}".format(question_loc, book["id"]+".txt")).read()

            prompt = prompt.replace("\nCharacters\n\n","\n{}\n\n".format(t_aspect))

            messages = [
                {"role": "system", "content": "You are a helpful assistant for story evaluation."},
                {"role": "user", "content": prompt}
            ]
            
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            model_inputs = tokenizer([text], return_tensors="pt").to(device)
            base_model_response = get_result(model_inputs, model, tokenizer, temperature=args.temperature, do_sample=args.do_sample, top_p=args.top_p)
            print(base_model_response)

            with open("{}/{}: {}.txt".format(args.output_loc,right_score, book["id"]),"w") as fout:
                fout.write(base_model_response)