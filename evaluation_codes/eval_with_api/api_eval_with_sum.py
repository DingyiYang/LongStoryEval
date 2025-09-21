import os
import json
import time
import requests
import json
import sys
import openai
from tqdm import tqdm
from multiprocessing import Pool
import time
import argparse
import random 


class OpenAIClient():
    def __init__(self,
                 model="gpt-4o",
                 temperature=0.0,
                 system_prompt=""):

        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.api_key = "" # replace by your own api key

        self.url = "" # replace by your own api url
            

    def chat(self, prompt):
        try:
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
            })
            headers = {
                'Content-Type': 'application/json',
                "Authorization": f"Bearer {self.api_key}",
            }

            response = requests.request("POST", self.url, headers=headers, data=data, timeout=(180, 180))
            # print(response)
            response_data = response.json()

            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(e)
            print('TIMEOUT. Sleeping and trying again.')
            time.sleep(3)
            return 'TIMEOUT'

def process_the_characters(char_sum):
    chars = char_sum.split("\n\n")
    rights = []
    for char in chars:
        # not mentioned remove
        if("not mentioned" in char.lower()):
            continue
        if("---" in char):continue
        if("Overall Experience" not in char or "Profile" not in char):
            if("**New Character" not in char):continue
        rights.append(char)
    return "\n\n".join(rights[:8])

def get_excerpt(content, max_length=500):
    t_content = []
    para_length = 0
    for i,t_line in enumerate(content):
        if("chapter " in t_line.lower()):continue
        t_len = len(content[i].split(" "))
        para_length+=t_len
        if(para_length>max_length):
            break
        t_content.append(content[i].replace("\n"," ").strip())
    return "\n".join(t_content[:])

def process_response(response):
    response = response.replace("Updated Review","Review")
    response = response.replace("Updated Assessment","Overall Assessment")
    response = response.replace("Updated Score","Score")
    detailed_reviews = response.split("\n")
    left_reviews = []
    for t_review in detailed_reviews:
        if("current review" not in t_review.lower() and "current assessment" not in t_review.lower()):left_reviews.append(t_review)
    try:
        return "\n".join(left_reviews)
    except:
        print("error")
        return ""

def evaluate_book(args):
    tfile, run_model, book_loc, sum_loc, prompt_template, all_book_info, output_loc = args
    t_title = all_book_info[tfile]["title"]
    try:
        t_premise = str(all_book_info[tfile]["premise"])
    except:
        t_premise = str(all_book_info[tfile]["basic"])
    temp_genres = all_book_info[tfile]["genres"][0:3]

    t_genre = ", ".join(temp_genres)
    openai_model = OpenAIClient(model=run_model,
                                temperature=0,
                                system_prompt="")

    chaps = json.load(open(book_loc + tfile + ".json"))["chaps"]
    sum_infos = json.load(open(sum_loc + tfile + ".json"))
    prompt_template = open(prompt_template).read()

    # get the prompt
    char_summary = process_the_characters(sum_infos[-1]["overall_char"])
    event_summary = sum_infos[-1]["overall_sum"]
    event_summary  = event_summary.replace("In this segment, ","Later, ") 

    
    chap_num = len(chaps)
    chap_i = random.randrange(0, chap_num, 1) #0

    t_excerpt = get_excerpt(chaps[chap_i]["content"],max_length=500)
        
    t_prompt = prompt_template.replace("{Title}",t_title).replace("{Genre}",t_genre).replace("{Premise}",t_premise).replace("{Plot_Summary}",event_summary).replace("{Character_Summary}",char_summary).replace("{Excerpt}",t_excerpt)

    #print("input",t_prompt)

    # evaluate the first chapter
    response = 'TIMEOUT'
    while(response == 'TIMEOUT'):
        response = openai_model.chat(str(t_prompt))

    print("output",response)

    with open(output_loc +"{}: {}.txt".format(all_book_info[tfile]["score"], tfile), "w") as fout:
        fout.write(response)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_model", type=str, default="gpt-4o")
    parser.add_argument("--book_loc", type=str, default="../../dataset/books_json/")
    parser.add_argument("--sum_loc", type=str, default="../../dataset/summaries/")
    parser.add_argument("--output_loc", type=str, default="../outputs/sum_based/gpt-4o/run_1/")
    parser.add_argument("--prompt_template", type=str, default="../prompt_template/no_criteria.txt")
    parser.add_argument("--book_info_loc", type=str, default="../../dataset/all_book_info.json")
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    sum_loc = args.sum_loc
    book_info_loc = args.book_info_loc

    if args.debug:
        book_info_loc = "../../dataset/book_debug_info.json"
        sum_loc = "../../dataset/summaries_debug/"

    all_book_info = json.load(open(book_info_loc))

    if not os.path.exists(args.output_loc):
        os.makedirs(args.output_loc)
    processed_files = os.listdir(args.output_loc)

    if(args.debug):
        files_to_eval = os.listdir(sum_loc)
        files_to_eval = [tfile.split(".json")[0] for tfile in files_to_eval]
    else:
        test_files = json.load(open("../../dataset/test_infos.json"))
        files_to_eval = []
        for genre in test_files.keys():
            files_to_eval += [tfile["id"] for tfile in test_files[genre]]

    files_with_args = []

    for tfile in files_to_eval:
        if("{}: {}.txt".format(all_book_info[tfile]["score"], tfile) in processed_files):
            print("processed",tfile)
            continue
        files_with_args.append((tfile, args.run_model, args.book_loc, sum_loc, args.prompt_template, all_book_info, args.output_loc))

    # evaluate
    with Pool(processes=50) as pool:
        results = pool.map(evaluate_book, files_with_args)