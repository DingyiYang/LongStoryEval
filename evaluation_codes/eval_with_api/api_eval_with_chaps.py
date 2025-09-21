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
    tfile, run_model, book_loc, sum_loc, prompt_loc, all_book_info, output_loc = args
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
    prompt_start = open("{}/beginning.txt".format(prompt_loc)).read()
    prompt_update = open("{}/incremental.txt".format(prompt_loc)).read()
    summ_info = []
    eval_info = []
    t_sum = ""
    char = ""

    # get the chapters
    chap_contents = []
    long_chap = ""
    for t_chap in chaps[:]:
        chap_c = "\n".join(t_chap["content"])
        if (len(t_chap["title"]) > 0): chap_c = "### "+ t_chap["title"] + "\n\n" + chap_c
        if(long_chap!=""):long_chap+= ("\n\n\n"+chap_c)
        else:long_chap=chap_c
        if(len(str(long_chap).split(" "))>4096):
            chap_contents.append(long_chap)
            long_chap =""
    if(long_chap!=""):chap_contents.append(long_chap)
    

    # start the evaluation
    chap_1 =chap_contents[0]

    # evaluate the first chapter
    response = 'TIMEOUT'
    while(response == 'TIMEOUT'):
        response = openai_model.chat(str(prompt_start.replace("{Beginning}", chap_1).replace("{Title}",t_title).replace("{Genre}",t_genre).replace("{Premise}",t_premise)))
    
    cur_eval = process_response(response)
    if(len(cur_eval.split(" "))>15):overall_eval = cur_eval
    else:overall_eval=response
    print("output",overall_eval)

    t_sum_i = 0
    eval_info.append({"response":response,"eval":overall_eval})
    # the summary to help understand the next chapter
    overall_sum = sum_infos[t_sum_i]["overall_sum"].replace("In this chapter, ","Later, ").replace("In this segment, ","Later, ")

    for chap_i,chap_1 in enumerate(tqdm(chap_contents[1:])):
        temp_update_prompt = prompt_update.replace("{Beginning}", chap_1).replace("{Sum}", overall_sum).replace("{Title}",t_title).replace("{Genre}",t_genre).replace("{Premise}",t_premise)
        temp_update_prompt = temp_update_prompt.replace("{Eval}",overall_eval)
        if(chap_i==len(chap_contents)-2):
            print("now is the ending of {}".format(tfile))
            temp_update_prompt.replace("a segment","the ending").replace("current segment","ending part").replace("this segment","the ending")

        response = openai_model.chat(temp_update_prompt)
        while (response == 'TIMEOUT'):
            response = openai_model.chat(temp_update_prompt)
        cur_eval = process_response(response)
        if(cur_eval!=""):overall_eval = cur_eval
        else:overall_eval=response
        eval_info.append({"content":chap_1,"response":response,"eval":overall_eval})
        print("output",overall_eval)

        t_sum_i+=1
        if(t_sum_i>=len(sum_infos)):break
        new_sum=sum_infos[t_sum_i]["overall_sum"].replace("In this chapter, ","Later, ").replace("In this segment, ","Later, ")
        if(new_sum!=""):overall_sum = new_sum


    with open(output_loc +"/" + tfile + ".json", "w") as fout:
        json.dump(eval_info, fout, indent=2, ensure_ascii=False)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_model", type=str, default="gpt-4o")
    parser.add_argument("--book_loc", type=str, default="../../dataset/books_json/")
    parser.add_argument("--sum_loc", type=str, default="../../dataset/summaries/")
    parser.add_argument("--output_loc", type=str, default="../outputs/aggregation/gpt-4o/")
    parser.add_argument("--prompt_loc", type=str, default="../prompt_template/aggregation/")
    parser.add_argument("--book_info_loc", type=str, default="../../dataset/all_book_info.json")
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    sum_loc = args.sum_loc
    book_loc = args.book_loc
    book_info_loc = args.book_info_loc

    if args.debug:
        book_info_loc = "../../dataset/book_debug_info.json"
        sum_loc = "../../dataset/summaries_debug/"

    all_book_info = json.load(open(book_info_loc))

    if not os.path.exists(args.output_loc):
        os.makedirs(args.output_loc)
    processed_files = os.listdir(args.output_loc)

    if(args.debug):
        ori_files = os.listdir(sum_loc)
        ori_files = [tfile.split(".json")[0] for tfile in ori_files]
    else:
        test_files = json.load(open("../../dataset/test_infos.json"))
        ori_files = []
        for genre in test_files.keys():
            ori_files += [tfile["id"] for tfile in test_files[genre]]

    files_with_args = []

    # sorted by book size
    for ti, fname in enumerate(ori_files):
        ori_files[ti] =   book_loc + fname+".json"
    sorted_file_paths = sorted(ori_files, key=os.path.getsize)
    for file_path in sorted_file_paths:
        if(file_path.split("/")[-1] in processed_files):
            print("processed",file_path.split("/")[-1])
            continue
        files_with_args.append((file_path.split("/")[-1].replace(".json",""), args.run_model, book_loc, sum_loc, args.prompt_loc, all_book_info, args.output_loc))

    # evaluate
    with Pool(processes=50) as pool:
        results = pool.map(evaluate_book, files_with_args)