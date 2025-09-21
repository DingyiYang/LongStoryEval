import os
import json
import time
import requests
import json
from tqdm import tqdm
import argparse
from multiprocessing import Pool

class OpenAIClient():
    def __init__(self,
                 model="gpt-4o",
                 temperature=0.0,
                 top_p=1,
                 system_prompt=""):

        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.top_p = top_p
        self.url = "" # replace by your own api
        
        self.api_key = "" # replace by your own api key

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
                "top_p": self.top_p,
            })
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.post(self.url, headers=headers, data=data,timeout=(180, 180))         
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(e)
            print('TIMEOUT. Sleeping and trying again.')
            time.sleep(3)
            return 'TIMEOUT'


def process_response(response):
    cur_summ, overall_sum, cur_char, all_char = "", "", "", ""
    try:
        if("\n\n### Characters:" in response):
            summ, char = response.split("\n\n### Characters:")
            char = "\n".join(char.split("\n")[1:])
        else:
            summ = response
            char = ""
        
        summ = summ.replace("### Updated Plot Summary","### Overall Plot Summary")
        if ("\n\n### Overall Plot Summary" in summ):
            cur_summ, overall_sum = summ.split("\n\n### Overall Plot Summary")
            overall_sum = "\n".join(overall_sum.split("\n")[1:])
            if("### Summary of Current Segment" in cur_summ):
                cur_summ = "\n".join(cur_summ.split("\n")[1:])
        else:
            if ("### Plot Summary" in summ):
                overall_sum = "\n".join(summ.split("\n")[1:])
            else:
                overall_sum = summ
            cur_summ = overall_sum
        if ("\n- **Current Experience" in char):
            chars = char.split("\n- **Current Experience")
            all_char = chars[0]
            cur_char = char
            for tchar in chars[1:20]:
                all_char += "\n"
                all_char += "\n".join(tchar.split("\n")[1:])
        else:
            all_char = char
            cur_char = all_char
    except Exception as e:
        print(e)
    if("\n---" in cur_summ):cur_summ = cur_summ.replace("\n---","")
    if("\n---" in overall_sum):overall_sum = overall_sum.replace("\n---","")
    return cur_summ.replace("\n\n", "\n"), overall_sum.replace("\n\n", "\n"), cur_char, all_char


def summarize_book(args):
    tfile,file_loc,run_model,prompt_loc,out_loc = args
    openai_model = OpenAIClient(model=run_model,
                                temperature=0,
                                system_prompt="")
    try:
        chaps = json.load(open(file_loc +"/"+ tfile))["chaps"]
    except:
        print("no chaps for ", tfile)
        return

    promt_loc = prompt_loc
    prompt_start = open(promt_loc+"/beginning.txt").read()
    prompt_update = open(promt_loc+"/update.txt").read()
    summ_info = []
    t_sum = ""
    char = ""
    
    # step 1: combine the short chapters
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
    

    # step 2: summarize the first chapter
    chap_1 = chap_contents[0]
    response = openai_model.chat(str(prompt_start.replace("{Beginning}", chap_1)))
    while (response == 'TIMEOUT'):
        response = openai_model.chat(str(prompt_start.replace("{Beginning}", chap_1)))
    cur_summ, overall_sum, cur_char, overall_char = process_response(response)
    summ_info.append({"response": response, "cur_sum": cur_summ, "overall_sum": overall_sum, "cur_char": cur_char,
                      "overall_char": overall_char})

    # continue the summarization
    for chap_i,chap_1 in enumerate(tqdm(chap_contents[1:])):
        temp_update_prompt = prompt_update.replace("{Beginning}", chap_1).replace("{Chars}", overall_char).replace("{Sum}", overall_sum)
        if(chap_i==len(chap_contents)-2):
            if("epilogue" not in temp_update_prompt.lower()):
                temp_update_prompt = "### Epilogue\n\n" + temp_update_prompt
            print("now is the ending of {}".format(tfile))
        response = openai_model.chat(temp_update_prompt)
        while (response == 'TIMEOUT'):
            response = openai_model.chat(temp_update_prompt)
        cur_summ, overall_sum, cur_char, overall_char = process_response(response)

        if(overall_sum=="" or len(overall_sum.split(" "))<20):overall_sum = summ_info[-1]["overall_sum"]
        if(overall_char=="" or len(overall_char.split(" "))<20):overall_char = summ_info[-1]["overall_char"]
        summ_info.append({"response": response, "cur_sum": cur_summ, "overall_sum": overall_sum, "cur_char": cur_char,
                          "overall_char": overall_char})
    with open(out_loc+"/" + tfile, "w") as fout:
        json.dump(summ_info, fout, indent=2, ensure_ascii=False)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_model", type=str, default="gpt-4o")
    parser.add_argument("--prompt_loc", type=str, default="./prompts/")
    parser.add_argument("--file_loc", type=str, default="../dataset/books_json/")
    parser.add_argument("--out_loc", type=str, default="../dataset/summaries_debug/")
    args = parser.parse_args()
    run_model = args.run_model

    ori_files = []
    if not os.path.exists(args.out_loc):
        os.makedirs(args.out_loc)
    
    processed_files = os.listdir(args.out_loc)
    print("processed_files", len(processed_files))
    
    file_loc = args.file_loc
    ori_files = os.listdir(file_loc)
    for ti, fname in enumerate(ori_files):
        ori_files[ti] = file_loc +"/"+ fname
    # sort the book files by size
    sorted_file_paths = sorted(ori_files, key=os.path.getsize)
    files_with_args = []
    for file_path in sorted_file_paths:
        if(file_path.split("/")[-1] in processed_files):continue
        files_with_args.append((file_path.split("/")[-1], args.file_loc, args.run_model, args.prompt_loc, args.out_loc))
    
    with Pool(processes=50) as pool:
        results = pool.map(summarize_book, files_with_args)