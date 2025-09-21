import os
import sys
import argparse
import json
import torch
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
import argparse

adapter_name = "self"
aspects_order = [
    "Plot and Structure", "Characters", "Writing and Language", "World-Building and Setting", "Themes", "Emotional Impact", "Enjoyment and Engagement", "Expectation Fulfillment"
]

def get_result(model_inputs, model, tokenizer, temperature=0.0, do_sample=False, top_p=1.0, max_new_tokens=1000):
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_new_tokens,
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
    parser.add_argument("--output_loc", type=str, default="../predict/output/long_story_eval/run_0/")
    parser.add_argument("--test_file", type=str, default="../data/test_infos.json")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--do_sample", action="store_true")
    parser.add_argument("--top_p", type=float, default=0.8)

    args = parser.parse_args()

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

    test_data = json.load(open(args.test_file))

    for aspect_index, current_aspect in enumerate(aspects_order):
        print(f"Processing aspect: {current_aspect}")
        aspect_output_dir = "{}/{}".format(args.output_loc,current_aspect.split(" ")[0])
        if not os.path.exists(aspect_output_dir):
            os.makedirs(aspect_output_dir)

        for genre in test_data.keys():
            for book in test_data[genre]:
                book_id = book["id"]
                score = book["score"]
                right_score = book["score"]
                prompt = open("{}/{}".format(question_loc, book["id"]+".txt")).read()
                
                # the pregenerated output
                full_review_text = open("{}/Overall/{}: {}".format(args.output_loc,right_score,book["id"]+".txt"),"r").read()

                if("### Review:\n" in full_review_text):full_review_text = full_review_text.split("### Review:\n")[1]
                try:
                    t_aspect_out = full_review_text.split("\n\n")[aspect_index]
                    aspect_content = "\n".join(t_aspect_out.split("\n")[1:])
                    t_aspect_out = "### Review:\n**{}:**\n".format(current_aspect)+aspect_content            
                    t_aspect_out += ("\n\n### Overall Assessment:\n"+aspect_content+"\n\n")                 
                    t_aspect_out +=("### Score")
                except Exception as e:
                    print(e)
                    print("error in aspect {} of {}".format(aspect_index,book["id"]))
                    t_aspect_out = ""
                    continue

                # replace the aspect
                prompt = prompt.replace("\nCharacters\n\n","\n**{}:**\n".format(current_aspect)+"Review of "+current_aspect+".\n\n")

                messages = [
                    {"role": "system", "content": "You are a helpful assistant for story evaluation."},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": t_aspect_out}
                ]

                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )

                eot_marker = "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
                text = eot_marker.join(text.split(eot_marker)[:-1])

                model_inputs = tokenizer([text], return_tensors="pt").to(device)

                try:
                    base_model_response = get_result(model_inputs, model, tokenizer, temperature=args.temperature, do_sample=args.do_sample, top_p=args.top_p)
                    print(t_aspect_out+base_model_response)
                    with open("{}/{}: {}".format(aspect_output_dir,right_score,book["id"]+".txt"),"w") as fout:
                        fout.write(t_aspect_out+base_model_response)
                except:
                    continue