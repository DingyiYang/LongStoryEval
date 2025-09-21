import sys
import json
import re
import os
from scipy.stats import kendalltau
import argparse

ASPECTS_ORDER = ["Plot and Structure", "Characters", "Writing and Language", "World-Building and Setting", "Themes", "Emotional Impact", "Enjoyment and Engagement", "Expectation Fulfillment", "Overall"]

def match_scores(contents):
    text = contents.replace("**Score**:","**Score:**")
    text = text.replace("### Score:","**Score:**")
    text = text.replace("**Overall Score:**","**Score:**")
    text = text.replace(" Score: ","**Score:** ")
    text = text.replace("**Score: ","**Score:** ")
    text = text.replace("Score:** **","Score:** ")
    text = text.replace("Score: ","Score:** ")

    pattern = r"\*\*Score:\*\* \d+(?:\.\d+)?"
    matches = re.findall(pattern, text)
    
    if len(matches) < len(ASPECTS_ORDER):
        return []
    return matches


def process_score(score_value):
    return round(score_value, 1)


def get_scores(out_loc, file_runs, test_files, book_info, split_genre, genre_books, whether_splited_generation):
    # to extract and average scores across multiple runs,

    book_scores = {}

    files_loc = "{}/run_{}/".format(out_loc,file_runs[0])
    if(whether_splited_generation): files_loc = "{}/run_{}/Overall/".format(out_loc,file_runs[0])
    
    for filename in os.listdir(files_loc):
        try:
            # Safely unpack filename like "4.15: book_id.txt"
            ori_score_str, book_id_with_ext = filename.split(": ", 1)
            book_id = book_id_with_ext.replace(".txt", "").strip()
        except ValueError:
            continue  

        if book_id not in test_files or (split_genre and book_id not in genre_books):
            continue

        ground_truth_score = book_info.get(book_id, {}).get("score")
        try:
            new_score = process_score(float(ground_truth_score))
        except (TypeError, ValueError):
            new_score = process_score(float(ori_score_str))
        

        match_infos = []
        is_valid = True
        for run_num in file_runs:
            run_loc = "{}/run_{}/".format(out_loc, run_num)
            file_path = os.path.join(run_loc, filename)
            try:
                if(whether_splited_generation):
                    contents = ""
                    for current_aspect in ASPECTS_ORDER:
                        aspect_file_path = "{}/{}/{}".format(run_loc,current_aspect.split(" ")[0],filename)
                        aspect_content = open(aspect_file_path, "r", encoding="utf-8").read()
                        if("### Review:\n" in aspect_content): aspect_content = aspect_content.split("### Review:\n")[1]
                        aspect_content = aspect_content.split("\n\n")[-1]
                        contents += aspect_content
                    # concat the generations of each aspect
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        contents = f.read()
                
                run_matches = match_scores(contents)
                if not run_matches: 
                    print(f"Insufficient scores in {file_path}")
                    is_valid = False
                    break
                match_infos.append(run_matches)
            except FileNotFoundError:
                print(f"File not found for run {run_num}: {file_path}")
                is_valid = False
                break
        
        if not is_valid:
            continue

        book_aspect_scores = []
        for i in range(len(ASPECTS_ORDER)):
            aspect_runs = []
            for run_idx in range(len(file_runs)):
                try:
                    score_str = match_infos[run_idx][i].split(" ")[-1]
                    aspect_runs.append(float(score_str))
                except (ValueError, IndexError):
                    continue
            
            if not aspect_runs: continue

            avg_score = sum(aspect_runs) / len(aspect_runs)
            if avg_score > 10:
                avg_score /= 20.0
            
            book_aspect_scores.append(avg_score)
 
        if len(book_aspect_scores) == len(ASPECTS_ORDER):
            book_scores[book_id] = {"score": new_score, "aspect": book_aspect_scores}
            
    return book_scores


def main():
    BASE_PATH = "../dataset/"
    TEST_INFO_PATH = os.path.join(BASE_PATH, "test_infos.json")
    BOOK_INFO_PATH = os.path.join(BASE_PATH, "all_book_info.json")
    
    try:
        with open(TEST_INFO_PATH, "r", encoding="utf-8") as f:
            test_info = json.load(f)
        with open(BOOK_INFO_PATH, "r", encoding="utf-8") as f:
            book_info = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Data file not found. {e}")
        sys.exit(1)

    test_files = [book["id"] for genre_books in test_info.values() for book in genre_books]

    if(args.debug):
        test_files = os.listdir("{}/run_{}".format(args.evaluation_result_loc,args.file_runs[0]))
        test_files = [": ".join(tf.split(".txt")[0].split(": ")[1:]).strip() for tf in test_files]
        book_info = json.load(open("{}/book_debug_info.json".format(BASE_PATH)))


    split_genre = False
    genre = "Fantasy"
    genre_books = [book["id"] for book in test_info.get(genre, [])]
    
    # replace by your own evaluation location
    evaluation_loc = args.evaluation_result_loc
    # replace by your own file runs
    file_runs = args.file_runs
    print(evaluation_loc, file_runs)
    all_book_scores = get_scores(evaluation_loc, file_runs, test_files, book_info, split_genre, genre_books, args.splited_generation)

    ori_scores = [data["score"] for data in all_book_scores.values()]
    
    aspect_scores = [[] for _ in range(len(ASPECTS_ORDER))]
    for data in all_book_scores.values():
        for i, aspect_score in enumerate(data["aspect"]):
            aspect_scores[i].append(aspect_score)

    print(f"Processed {len(ori_scores)} books.")

    correlations = []
    p_values = []

    for i, aspect_name in enumerate(ASPECTS_ORDER):

        tau, p_value = kendalltau(aspect_scores[i], ori_scores)
        
        correlations.append(round(tau * 100, 1))
        p_values.append(round(p_value, 3))
        
        print(f"\n--- {aspect_name} ---")
        print(f"Kendall's Tau Correlation: {round(tau * 100, 2)}")

    print("\n" + "="*20 + " SUMMARY " + "="*20)
    print("Correlations:", correlations)
    print("P-values:", p_values)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation_result_loc", type=str, default="../evaluation_codes/outputs/sum_based/gpt-4o/")
    parser.add_argument("--file_runs", nargs='+', help="List of run numbers to process.")
    parser.add_argument("--splited_generation", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    main()