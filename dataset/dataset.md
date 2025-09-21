# Dataset Documentation

## 📁 Dataset Structure

```
/dataset/
├── all_book_info.json
├── test.txt
├── summaries/
├── reviews_json/
└── all_reviewer_info.json
```

## 📚 Book Metadata
**Location**: `/dataset/all_book_info.json`

**Keys for each book**:
| Key | Description |
|-----|-------------|
| `title` | Book title |
| `author` | Book author |
| `genres` | List of genres |
| `score` | Average rating score |
| `rating_distribution` | Distribution of ratings (5★ to 1★) |
| `premise` | Brief book premise |
| `book_len` | Length of the book |

## 📚 Test set
**Location**: `/dataset/test.txt`

**Info**: Test Set ID List

## 📖 Book Summaries
**Location**: `/dataset/summaries/`

**Description**: Due to copyright restrictions, we only release the overall summary. The complete book content can be downloaded through the metadata, and chapter-level summaries can be generated using our summary code.

**Keys for each book**:
| Key | Description |
|-----|-------------|
| `overall_sum` | Overall Plot Summary |
| `overall_char` | Overall Character Analysis |

## ⭐ Review Data
**Location**: `/dataset/reviews_json/`

**Each file contains multiple book reviews; Keys for each reivew**:
| Key | Description |
|-----|-------------|
| `aspects` | Reviewed aspects of the book |
| `review` | Aspect-specific reviews |
| `conclusion` | Review conclusion |
| `rating` | Reviewer's rating |
| `review_likes` | Number of likes received |
| `reviewer_id` | Unique reviewer identifier |
| `reviewer_followers` | Reviewer's follower count |
| `reviewer_review_nums` | Reviewer's total reviews |
| `reformatted_ori_review` | Original review reformatted by DeepSeek-v2.5 |

## 👤 Reviewer Information
**Location**: Download at [all_reviewer_info](https://entuedu-my.sharepoint.com/:u:/g/personal/dingyi_yang_staff_main_ntu_edu_sg/EcNTlfX6wJNImReki8zHNY4BVyai_TA4SjvlAfneDbOYmQ?e=wA8nVu), then put at `/dataset/all_reviewer_info.json`

**Keys for each reviewer**:
| Key | Description |
|-----|-------------|
| `rating_distribution` | Reviewer's rating distribution |
| `rating_nums` | Total number of ratings given |
| `avg` | Average rating given |
| `sd` | Standard deviation of ratings |
| `others` | Additional personal information |