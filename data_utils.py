from pathlib import Path
# Eventually this goes into a single json file per assignment
def assignment_match_to_csv_name(name):
    if "Exam 1" in name:
        csv_name = "exam1all.csv"
    elif "Exam 2" in name:
        csv_name = "exam2all.csv"
    elif "Exam 3" in name:
        csv_name = "exam3all.csv"
    elif "Homework 2" in name:
        csv_name = "Homework_2_Morse_Code_scores.csv"
    elif "Homework 3" in name:
        csv_name = "Homework_3_Navigating_a_City_Grid_scores.csv"
    elif "Homework 4" in name:
        csv_name = "Homework_4_ASCII_Image_Rendering_scores.csv"
    elif "Homework 5" in name:
        csv_name = "Homework_5_Robots_versus_Zombies_Object_Oriented_Programming__scores.csv"
    else:
        raise ValueError(f"Could not find csv file for {name}")
    return Path("data") / csv_name

