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
    text = text.replace("Score: ","**Score:** ")
    text = text.replace("*Score:* ","**Score:** ")
    text = text.replace("a score of ","**Score:** ")
    text = text.replace("rate the book ","**Score:** ")
    text = text.replace("**Rating:** ","**Score:** ")
    text = text.replace("Rating: ","**Score:** ")
    text = text.replace(")", "").replace("(", "")
    
    pattern = r"\*\*Score:\*\* \d+(?:\.\d+)?"
    matches = re.findall(pattern, text)
    
    if len(matches) < len(ASPECTS_ORDER):
        return []
    return matches

def process_score(score_value):
    #return score_value
    return round(score_value, 1)

def get_scores(out_loc, file_runs, test_files, book_info, eval_type):
    book_scores = {}
    
    # Assuming run_1 exists and contains the superset of files to check
    run_1_path = os.path.join(out_loc, "run_{}".format(file_runs[0]))
    if not os.path.exists(run_1_path):
        print(f"Error: directory not found in {out_loc}. Cannot determine files to process.")
        return {}

    for filename in os.listdir(run_1_path):
        if not filename.endswith(".json"):
            continue

        book_id = filename.replace(".json", "")
        if book_id not in test_files:
            continue

        try:
            ground_truth_score = book_info[book_id]["score"]
            new_score = round(float(ground_truth_score), 1)
        except (KeyError, TypeError, ValueError):
            print(f"Warning: Could not get ground truth score for {book_id}. Skipping.")
            continue

        match_infos = []
        is_valid = True
        for run_num in file_runs:
            run_loc = os.path.join(out_loc, f"run_{run_num}")
            file_path = "{}/{}".format(run_loc, filename)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    # The file contains chunk-by-chunk evaluations
                    chunk_evals = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                print(f"File missing or invalid for run {run_num}: {file_path}")
                is_valid = False
                break

            run_aspect_scores = [0] * len(ASPECTS_ORDER)
            valid_chunks = 0
            if(eval_type == "incre_updated"):
                chunk_evals = chunk_evals[-1:]
            for chunk in chunk_evals:
                eval_text = chunk.get("eval", "")
                #print(eval_text)
                chunk_matches = match_scores(eval_text)
                if chunk_matches:
                    valid_chunks += 1
                    for i in range(len(ASPECTS_ORDER)):
                        score_str = chunk_matches[i].split(" ")[-1]
                        run_aspect_scores[i] += float(score_str)

            if valid_chunks > 0:
                avg_run_scores = [score / valid_chunks for score in run_aspect_scores]
                match_infos.append(avg_run_scores)
            else:
                print(f"No valid scores found in any chunk for {file_path}")
                is_valid = False
                break
        
        if not is_valid or not match_infos:
            continue

        book_aspect_scores = []
        for i in range(len(ASPECTS_ORDER)):
            aspect_runs = [match_info[i] for match_info in match_infos]
            
            if not aspect_runs: 
                continue

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
        test_files = [tf.split(".json")[0] for tf in test_files]
        print(test_files)
        book_info = json.load(open("{}/book_debug_info.json".format(BASE_PATH)))

    evaluation_loc = args.evaluation_result_loc
    file_runs = args.file_runs
    print(f"Processing evaluation results from: {evaluation_loc}")
    print(f"Using runs: {file_runs}")

    all_book_scores = get_scores(evaluation_loc, file_runs, test_files, book_info, args.eval_type)

    if not all_book_scores:
        print("No valid book scores were processed. Exiting.")
        return

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
    print("Correlations (%):", correlations)
    print("P-values:", p_values)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation_result_loc", type=str, required=True, default = "../evaluation_codes/outputs/aggre_based/gpt-4o/")
    parser.add_argument("--eval_type", type=str, default = "aggre_based")
    parser.add_argument("--file_runs", nargs='+')
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    main()