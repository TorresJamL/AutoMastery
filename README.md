# AutoMastery

Automates mastery-based grading for Canvas courses with the Stevens Canvas setup.  Pulls student scores from Gradescope, computes rubric outcomes, and pushes them to Canvas via the Canvas LMS API.

## Setup

### Prerequisites

- Python 3.13+
- A Canvas API token with Teacher-level access to the target course
- A Gradescope account with Instructor access to the matching course

### Credentials

Create a file called `_t_.py` in the project root (it is gitignored):

```python
TOKEN = "your-canvas-api-token"
GS_USR = "your-gradescope-email"
GS_PWD = "your-gradescope-password"
```

### Dependencies

This is a pip package. You can install it with `pip install -e`

---

## Project Structure

### `config/`
This folder gets built automatically as you run "update assessment"
Non-sensitive configuration for each course and assignment. Organized as:

```
config/
  course_id_<CANVAS_COURSE_ID>/
    assignment_data.json          # Cached mapping of assignment IDs to names
    assignment_order.txt          # Newline-delimited list of assignment names, in the order they should be processed (used by sequential_mastery_update.py)
    assignment_<ASSIGNMENT_ID>/
      assignment.json             # Which Assignment class to use (e.g. SingleScoreSingleOutcomeAssignment) and optionally the CSV path
      score_thresholds.json       # Score thresholds for Exceeds Mastery, Mastery, Near Mastery, Below Mastery
      rubric_id_to_question_keys.json  # Maps Canvas rubric IDs to Gradescope CSV column names
```

**`assignment_order.txt`** is especially important for sequential updates (ex. when the assignment order matters) 

Each line is an assignment name as it appears on Canvas (e.g. `Homework 1`, `Test 1 Question 2`). The sequential update script processes them top to bottom.

**`score_thresholds.json`** example:
```json
{"Exceeds Mastery": 0.99, "Mastery": 0.75, "Near Mastery": 0.5, "Below Mastery": 0.25}
```

These thresholds are percentages. A student scoring >= 99% gets "Exceeds Mastery" (rubric score 4), >= 75% gets "Mastery" (3), etc. If this file doesn't exist when an assignment is first created, you'll be prompted interactively to enter values.

**`assignment.json`** stores which Assignment subclass to use. Possible values for `assignment_cls`:
- `SingleScoreSingleOutcomeAssignment` (shorthand: `SS`) — assignments with one total score and one rubric outcome (e.g. labs, homeworks graded on Canvas)
- `MultiScoreMultiOutcomeAssignment` — assignments with multiple graded sub-parts and multiple rubric outcomes (e.g. homeworks graded on Gradescope)
- `ExamQuestion` — a single exam question that maps to rubric outcomes (Canvas has one assignment per exam question)

### `data/`

Sensitive student data (grades, submissions). **Gitignored.** Organized as:

```
data/
  course_id_<CANVAS_COURSE_ID>/
    student_data.json             # Cached student info (Canvas IDs, names, emails, SIS IDs)
    course_data.json              # Cached course metadata from Canvas
    outcome_data.json             # Cached outcome/learning objective details
    Outcomes-<CourseName>.csv     # Learning Mastery export (downloaded or manually placed)
    assignment_<ASSIGNMENT_ID>/
      <scores>.csv                # Gradescope CSV export for this assignment
```

Student data and assignment data JSONs are cached on first run and reused. Pass `overwrite_student_json=True` or `overwrite_assignment_json=True` to the `Course` constructor to force a refresh.

---

## Scripts

All scripts live in `scripts/` and should be run from the **project root directory**.

### Updating Mastery for a Single Assignment

**`scripts/update_assessment.py`** — Updates mastery rubric scores on Canvas for one assignment.

```bash
python scripts/update_assessment.py -c <COURSE_ID> -a "<ASSIGNMENT_NAME>"
```

Arguments:
- `-c` / `--course_id` — Canvas course ID (visible in the Canvas URL)
- `-a` / `--assignment_name` — Assignment name exactly as it appears on Canvas (e.g. `"Test 1 Question 3"`, `"Homework 4"`)
- `-s` / `--student_name_match` — (Optional) Only update a single student whose name contains this string. Useful for testing before running on the whole class.

Example (from the PyCharm run configuration):
```bash
python scripts/update_assessment.py -c 85465 -a "Test 3 Question 1"
```

### Updating Mastery Sequentially (All Assignments)

**`scripts/sequential_mastery_update.py`** — Walks through all assignments listed in `assignment_order.txt` and updates mastery scores for each one, in order.

```bash
python scripts/sequential_mastery_update.py -c <COURSE_ID>
```

Arguments:
- `-c` / `--course_id` — Canvas course ID
- `-s` / `--student_name_match` — (Optional) Only update one student
- `-f` / `--first_assessment` — (Optional) Skip assignments before this one in the order file. Useful for resuming after a failure.

This script requires `config/course_id_<ID>/assignment_order.txt` to exist. If it doesn't, the script will tell you to create one. The file should list assignment names one per line, in the order you want them processed.

Example:
```bash
# Update all assignments for course 84995
python scripts/sequential_mastery_update.py -c 84995

# Resume from "Test 2 Question 1"
python scripts/sequential_mastery_update.py -c 84995 -f "Test 2 Question 1"

# Dry run on one student
python scripts/sequential_mastery_update.py -c 84995 -s "Torres"
```

### Downloading Learning Mastery Data

**`scripts/download_mastery_from_canvas.py`** — Downloads the Learning Mastery (outcome rollups) from Canvas and produces a summary CSV with mastery counts and letter grades.

```bash
python scripts/download_mastery_from_canvas.py -c <COURSE_ID> --download-mastery
```

Arguments:
- `-c` / `--course_id` — Canvas course ID
- `--download-mastery` — Download a fresh Learning Mastery CSV from Canvas via the API. Without this flag, the script reads an existing `Outcomes-*.csv` from the course data directory.
- `--input_path` — (Optional) Path to an existing Learning Mastery CSV to use instead of auto-detecting
- `--mastery_output_path` — (Optional) Where to save the downloaded CSV
- `--summary_output_path` — (Optional) Where to save the summary CSV

Example (from the PyCharm run configuration):
```bash
python scripts/download_mastery_from_canvas.py --download-mastery -c 85398
```

The summary CSV includes columns for each student's name, email, SIS ID, number of outcomes at mastery, number at exceeds mastery, and the computed letter grade.


## How Mastery Grading Works

Each Canvas assignment has a rubric with one or more outcomes (learning objectives). AutoMastery:

1. Fetches the student's score from Canvas or Gradescope
2. Computes a percentage score for each rubric item
3. Converts the percentage to a rubric score (0-4) using the assignment's score thresholds
4. PUTs the rubric assessment back to Canvas via the API

The rubric score mapping (default thresholds):
| Percentage | Rubric Score | Level |
|---|---|---|
| >= 99% | 4 | Exceeds Mastery |
| >= 75% | 3 | Mastery |
| >= 50% | 2 | Near Mastery |
| >= 25% | 1 | Below Mastery |
| < 25% | 0 | — |

### Letter Grade Calculation

Letter grades are derived from the number of outcomes a student has mastered (score >= 3.0) and the number at exceeds mastery (score >= 3.5):

| Mastered | Exceeds Mastery | Grade |
|---|---|---|
| >= 10 | >= 5 | A |
| >= 10 | >= 3 | A- |
| >= 10 | — | B+ |
| >= 8 | — | B |
| >= 6 | — | B- |
| >= 4 | — | C+ |
| >= 3 | — | C |
| >= 2 | — | C- |
| >= 1 | — | D |
| 0 | — | F |

---

## First-Time Setup for a New Assignment

When you run `update_assessment.py` on an assignment for the first time, the tool will interactively prompt you for:

1. **Assignment class** — `SS` (SingleScoreSingleOutcomeAssignment), `EQ` (ExamQuestion), or `MultiScoreMultiOutcomeAssignment`
2. **Score thresholds** — for each mastery level (or press Enter to accept defaults)
3. **Rubric-to-question mapping** (for CSV-based assignments) — the tool shows each rubric item and each Gradescope CSV column and asks you to match them
4. **CSV file path** (for CSV-based assignments) — where the Gradescope export lives

These are saved to the assignment's config directory and reused on subsequent runs.

---

## Canvas Rubric Setup

For AutoMastery to work, each Canvas assignment needs a rubric with outcome-aligned criteria attached. See the Canvas documentation for how to set this up:

- [How do I add a rubric to an assignment?](https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-add-a-rubric-to-an-assignment/ta-p/1058)
- [How do I align an outcome with a rubric in a course?](https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-align-an-outcome-with-a-rubric-in-a-course/ta-p/1130)
- [How do I manage outcomes in a course?](https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-manage-outcomes-in-a-course/ta-p/1035)

Each rubric criterion should be aligned to a learning outcome so that the API can update outcome scores via `rubric_assessment`.

