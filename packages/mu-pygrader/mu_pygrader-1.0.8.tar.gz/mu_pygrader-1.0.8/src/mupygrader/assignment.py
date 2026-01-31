"""
assignment.py
weavebj1 - 2025

Contains tools surrounding assignment object, which relies on pygrader library

Notable features:
    - Create assignment using json file
    - Data output into .csv, .txt, pandas df, or simple dictionary
    - Use self.pypackage_command to get command line prompt needed to package 
      entire assignment into .exe

Part of python-grader library
"""

import os
import json
import datetime
from collections import defaultdict
import pandas as pd
from mupygrader import test_file
from mupygrader import utils
from mupygrader.json_interface import Problem


class Assignment:
    """
    Assignment object represents an assigned set of problems.

    Attributes:
        config_file (str): The name of the json file being used.
        course (str):      Name of the course (optional)
        name (str):        Name of the assignment (optional)
        late_mult (num):   Number multiplied by late assignments
        problems ([json_interface.problem]):    Objects representing each problem
        solutions (test_file.TestFile):         Objects representing solution files
    """

    def __init__(self, config_file):
        """
        Constructor for assignment object

        Parameters:
            config_file (str): The name of the json file being used
        """
        self.config_file = config_file
        self.solutions = []

        try:
            if utils.running_in_exe():
                config_file = os.path.join(utils.exe_resource_path(), config_file)

            with open(config_file, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)

        except FileNotFoundError:
            print(f"Could not find config file {config_file}")
            raise

        self.course = data["course"]
        self.name = data["assignment"]
        self.late_mult = data["late_mult"]

        self.problems = []
        for p in data["problems"]:
            self.problems.append(Problem(self, **p))

        for submdir in data["submission_folders"]:
            self.add_student_submissions(os.path.abspath(submdir))

    def init_resources(self):
        """
        Runs initializations for files, including running solutions
        """
        for p in self.problems:

            if p.runner_file:
                p.init_runner()

            p.init_solution()
            p.solution.code.run()

    def add_student_submissions(self, folder):
        """
        Places student submissions into the correct problem based on the filenames

        Parameters:
            folder (str): Folder to look for submissions in
        """
        files_to_add = test_file.get_pyfiles(folder)

        for p in self.problems:
            for file in files_to_add:
                if p.file_whitelist in file:
                    p.add_submission(os.path.join(folder, file))


    def run_submissions(self):
        """
        Runs all solutions associated with all problems
        """
        self.init_resources()

        for p in self.problems:
            for sub in p.submissions:
                sub.run_and_score(p.solution)

    def to_dict(self):
        """
        Makes a dictionary that has personal identifier as a key, 
        and a list of their submissions as a value        
        """
        out_dict = defaultdict(list)
        for p in self.problems:
            for submission in p.submissions:
                out_dict[submission.identifier].append(submission)

        return out_dict

    @property
    def max_points(self):
        """
        Retreives the sum of points from all associated problems        
        """
        total = 0
        for p in self.problems:
            total += p.points
        return total

    def file_header(self):
        """
        Creates text for a header to be used in multiple output formats        
        """
        head_str = ""
        head_str += f"Assignment: {self.name}\n"
        head_str += f"Max Points: {self.max_points}\n"
        head_str += f"Report generated: {datetime.datetime.now()}\n"
        return head_str

    def output_dataframe(self):
        """
        Creates a pandas dataframe of the data        
        """
        asgmt_dict = self.to_dict()
        csv_rows = []
        for key,submissions in asgmt_dict.items():
            grade = 0
            total_points = 0
            all_canvas_submissions = True
            for s in submissions:
                grade += s.grade
                total_points += s.points_scored
                all_canvas_submissions &= s.is_canvas

            new_row = {}
            if all_canvas_submissions:
                new_row["name"] = key[0]
                new_row["sys_id"] = key[1]
            else:
                new_row["name"] = key

            new_row["grade"] = grade
            new_row["raw_points"] = total_points
            for s in submissions:
                new_row[s.params.name] = s.grade
                new_row[f"{s.params.name}_is_late"] = s.is_late
                new_row[f"{s.params.name}_raw_points"] = s.points_scored
                new_row[f"{s.params.name}_errors"] = s.error_comments

            csv_rows.append(new_row)

        return pd.DataFrame(csv_rows)


    def output_terminal(self):
        """
        Displays information about the output in the terminal        
        """
        asgmt_dict = self.to_dict()

        print(self.file_header())

        for submissions in asgmt_dict.values():

            points_earned = 0
            for s in submissions:
                points_earned += s.grade

            score_str = f"{submissions[0].student_name}:"
            if submissions[0].is_canvas: # Only print if the student is known
                score_str += f" {points_earned:0.2f}/{self.max_points:0.2f}"
                score_str += f" ({100*points_earned/self.max_points:2.0f}%)"
            print(score_str)

            for s in submissions:
                s.print_results()
            print() # Space between students


    def output_txt(self, file="output.txt"):
        """
        Creates .txt file output of test results
        
        Parameters:
            file (str): name/path of the output file
        """
        asgmt_dict = self.to_dict()

        try:
            with open(file, 'w', encoding="utf-8") as out:
                out.write(self.file_header() + "\n")

                for submissions in asgmt_dict.values():
                    points_earned = 0
                    for s in submissions:
                        points_earned += s.grade

                    problem_str = f"{submissions[0].student_name}:"
                    if submissions[0].is_canvas: # Only print if the student is known
                        problem_str += f" {points_earned:0.2f}/{self.max_points:0.2f}"
                        problem_str += f" ({100*points_earned/self.max_points:2.0f}%)\n"

                    out.write(problem_str)
                    for s in submissions:
                        s.print_results(out)
                    out.write("\n\n")
        except PermissionError:
            print("Output text document is open or inaccessible")
            raise


    def output_csv(self, file):
        """
        Creates .csv file output of test results
        
        Parameters:
            file (str): name/path of the output file
        """
        df = self.output_dataframe()

        try:
            with open(file, '+w', encoding="utf-8") as csv:
                csv.write(self.file_header())
                df.to_csv(csv, mode='a', lineterminator='\n')
        except PermissionError:
            print("Output file is already open or otherwise inaccessible. Cannot edit")
            raise


    def pypackage_command(self, target_file):
        """
        Develops a pyinstaller command based on required inputs

        Parameters:
            target_file (str): Python script being converted into a .exe
        """

        def update_path_list(all_paths, new_file):
            """
            Makes the file string, but also adds a path if needed
            """
            new_path = os.path.dirname(new_file)
            if new_path not in all_paths:
                all_paths.append(new_path)
            return all_paths


        path_list = []

        out_str = 'pyinstaller --noconfirm --onefile --console --contents-directory "."'
        out_str += f' --add-data "{self.config_file};."'

        for p in self.problems:
            out_str += f' --hidden-import "{utils.file_strip(p.solution_file)}"'
            path_list = update_path_list(path_list, p.solution_file)

            if p.runner_file:
                if p.runner_hidden:
                    out_str += f' --hidden-import "{utils.file_strip(p.runner_file)}"'
                    path_list = update_path_list(path_list, p.runner_file)
                else:
                    out_str += f' --add-data "{p.runner_file};."'

        if ico_dir := exist_icon():
            out_str += f' --icon "{ico_dir}"'

        if len(path_list) >= 0:
            out_str += f' --paths {":".join(path_list)}'

        out_str += f' "{target_file}"'
        return out_str


def exist_icon():
    """
    Checks if icon file can be found
    """
    return utils.in_repo('pygrader.ico')
