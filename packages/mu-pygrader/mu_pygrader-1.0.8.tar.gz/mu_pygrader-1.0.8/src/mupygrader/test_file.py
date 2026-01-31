"""
test_file.py
weavebj1 - 2025

File objects that run python files and store attributes

Part of python-grader library

TODO Add "import" type of file which can run multiple functions
"""

import os
import importlib
import re
from unittest.mock import Mock
import numpy as np
from mupygrader.utils import guarantee_path, file_strip


class TestFile:
    """
    TestFile object represents a file that is evaluated under testing conditions

    Attributes:
        filename (str): The name of the file under test
        filepath (str): The directory location of the file
        params (json_interface.problem): Problem definition derived from json file
        code (TestScript or TestFunction): [has an] object that represents the 
                                             specific code in the file 
    """

    def __init__(self, filepath, problem):
        """
        Constructor for TestFile object

        Parameters:
            filepath (str): Fully defined path of the file being used
            problem (json_interface.problem): Problem that this file is associated with 
        """
        split_path = filepath.split(os.path.sep)
        self.filename = split_path[-1]
        self.filepath = filepath
        self.params = problem

        try:
            if problem.type.lower() not in ["function", "script"]:
                raise ValueError
        except ValueError:
            print('Parameter "pytype" must be "function" or "script"')
            raise
        if problem.type.lower() == "function":
            self.code = TestFunction(self)
        elif problem.type.lower() == "script":
            self.code = TestScript(self)

    def init_function_trackers(self):
        """
        Begins the tracking of any functions that are tracked by function tests
        """
        fun_tests = self.params.function_tests

        for fun in fun_tests:

            fun.mock = Mock()
            fun.mock.side_effect = fun.original

            setattr(fun.module, fun.function, fun.mock)

    def close_function_trackers(self):
        """
        Ends the tracking of any functions that are tracked by function tests
        """
        fun_tests = self.params.function_tests
        for fun in fun_tests:
            setattr(fun.module, fun.function, fun.original)

    def run_with_mock(self):
        """
        Runs the code of a file with tracking enabled
        """
        blank_array_size = np.size(self.params.function_tests)
        start_counts   = np.zeros(blank_array_size)
        end_counts     = np.zeros(blank_array_size)
        should_be_used = np.zeros(blank_array_size)

        # Get starting use-counts for functions
        idx = 0
        for fun in self.params.function_tests:
            start_counts[idx] = fun.mock.call_count
            should_be_used[idx] = not fun.invert
            idx += 1

        try:
            self.code.run()

        except Exception as e:
            self.code.result = e
            return np.zeros(blank_array_size).tolist()

        finally:

            # Get final use counts for functions (up until any errors)
            idx = 0
            for fun in self.params.function_tests:
                end_counts[idx] = fun.mock.call_count
                idx += 1

        was_used = np.dot(1, end_counts > start_counts)
        function_scorecard = 1*(should_be_used == was_used)

        return function_scorecard.tolist()


class TestScript:
    """
    Represents the code for a file under test that is a script file

    Attributes:
        parent (TestFile): The name of the file under test
        result (tuple): Collected namespace from running the script
    """

    def __init__(self, file):
        """
        Constructor for TestScript

        Parameters:
            file (TestFile): Parent object for script file obj
        """
        self.parent = file
        self.result = []


    def run(self):
        """
        Runs TestScript file and saves result

        In a separate namespace:
            - if the module has already been imported, remove the key from the module
              list, forcing it to be reloaded when imported
            - import and store the result of the import to a variable, which includes
              any variables that existed in the script
        """
        sol_local_space = {"importlib":importlib}
        try:
            filename = file_strip(self.parent.filepath)
            guarantee_path(self.parent.filepath)
            exec('import sys', {}, sol_local_space) # pylint: disable=exec-used
            exec(f'if "{filename}" in sys.modules: del sys.modules["{filename}"]', # pylint: disable=exec-used
                 {},sol_local_space)
            exec(f'output = importlib.import_module("{filename}")',{},sol_local_space)  # pylint: disable=exec-used
            self.result = sol_local_space["output"]
        except Exception as e:
            print(f"Could not run script of file {filename}")
            self.result = e


    def compare_values(self, key):
        """
        Compares results of this object to another TestScript

        Parameters:
            key (TestScript): code object for solution code
        """
        scorecard = np.zeros(len(self.parent.params.value_tests)).tolist()
        i=0
        for var_test in self.parent.params.value_tests:
            var_name = str(var_test.variable)

            # Conditional to see if the value exists in general
            try:
                scorecard[i] = var_test.equal_tol(getattr(self.result, var_name),
                                                  getattr(key.result, var_name))
            except Exception as e:
                scorecard[i] = e

            i+=1

        return scorecard



class TestFunction:
    """
    Represents the code for a file under test that is a function

    Attributes:
        parent (TestFile): The file under test
        result (tuple): Collected output returned by the function
    """

    def __init__(self, file):
        """
        Constructor for TestFunction

        Parameters:
            file (TestFile): Parent object for function obj
        """
        self.parent = file
        self.result = []


    def run(self):
        """
        Runs TestFunction file and saves result
        """
        fun_name = self.parent.params.function_name
        module_name = file_strip(self.parent.filename)
        guarantee_path(self.parent.filename)
        try:
            test_file = importlib.import_module(module_name)
            importlib.reload(test_file)
        except Exception as e:
            self.result = e
            return


        if fun_name not in dir(test_file):
            raise ValueError(f'Function {fun_name} not found in {test_file.__name__}')
        fun_to_run = getattr(test_file, self.parent.params.function_name)

        if self.parent.params.runner:
            filename = file_strip(self.parent.params.runner.filename)
            guarantee_path(self.parent.params.runner.filename)
            runner_file = importlib.import_module(filename)
            runner_to_run = getattr(runner_file, 'main')
            self.result = runner_to_run(fun_to_run) # Pass the function obj, not the result
        else:
            self.result = fun_to_run()

    def compare_values(self, key):
        """
        Compares results of this object to another TestFunction

        Parameters:
            key (TestFunction): code object for solution code
        """
        # Check the number of outputs
        if len(key.result) < len(self.result):
            print("Submission has too many variables returned")
        elif len(key.result) > len(self.result):
            print("Submission has too few variables returned")

        if len(key.result) != len(self.result):
            print(f"Expected {len(key.result)} values. Returned {len(self.result)}")

        scorecard = np.zeros(len(key.result)).tolist()
        i = 0
        for var_test in self.parent.params.value_tests:
            try:
                scorecard[i] = var_test.equal_tol(self.result[i], key.result[i])
            except Exception as e:
                scorecard[i] = e

            i+=1

        return scorecard



class Submission(TestFile):
    """
    Represents a file that is submitted by a student and will be compared
    against a solution

    Attributes:
        super(): TestFile class parameters
        student_name (str): Name of student
        student_id (str): Id number that canvas assigns to student
        is_late (bool): Based on canvas submission format. Affects grading
        is_canvas (bool): Flag based on detecting canvas format in docstring

        function_scorecard ([num]): Array showing performance on function tests
        value_scorecard ([num]): Array showing performance on value tests 
        scorecard ([num]): Composite of function and value scorecards

        points_scored (num): Sum of points gained, ignoring late penalties
        grade (num): Grade based on points and late penalties
        error_comments (str): List of feedback statements based on errors
    """

    def __init__(self, filepath, problem):
        """
        Constructor for Submission

        Parameters:
            filepath (str): File path to the file being submitted
            problem (json_interface.problem): Problem obj that submission is 
                                              associated with
        """
        super().__init__(filepath, problem)

        self._is_canvas = re.search(r"\S*_[^LATE_$]?(\d*)_\d+", self.filename)
        self.student_name = self.filename.split("_")[0]
        self.student_id = []
        self.is_late = False

        if self._is_canvas:
            self.student_id =  self._is_canvas.group(1)
            self.is_late = self.filename.split("_")[1].__contains__("LATE")
            self.is_canvas = True
        else:
            self.is_canvas = False

        self.function_scorecard = []
        self.value_scorecard = []
        self.scorecard = []
        self.points_scored = 0
        self.grade = 0
        self.error_comments = ""

    def update_score(self):
        """
        Updates score and grade based on results from running code
        """
        self.points_scored = 0
        i = 0
        for t in self.params.all_tests:
            if not isinstance(self.scorecard[i], Exception) and (self.scorecard[i] > 0):
                self.points_scored += t.points
            i+=1


        multiplier = 1
        if self.is_late:
            multiplier *= self.params.assignment.late_mult

        self.grade = self.points_scored * multiplier

    def make_error_msg(self):
        """
        Creates error messages based on tests failed
        """
        messages = []
        if isinstance(self.code.result, Exception):
            error_type = type(self.code.result).__name__
            messages.append(f"{error_type}: {self.code.result}")

        i = 0
        for t in self.params.all_tests:
            if isinstance(self.scorecard[i], Exception):
                messages.append(f"[-{t.points}] ERROR {self.scorecard[i]}")
            elif self.scorecard[i] == 0:
                messages.append(f"[-{t.points}] {t.error_comment}")
            elif np.isnan(self.scorecard[i]):
                messages.append(f"[-{t.points}] A test ({t.name}) could not be evaluated")
            i+=1

        self.error_comments = "\n".join(messages) + "\n"

    def run_and_score(self, solution):
        """
        Evaluates submission based on a given solution file

        Parameters:
            solution (TestFile): Solution being compared against
        """
        self.init_function_trackers()
        self.function_scorecard = self.run_with_mock()
        self.close_function_trackers()

        if not isinstance(self.code.result, Exception):
            try:
                self.value_scorecard = self.code.compare_values(solution.code)
            except Exception:
                self.value_scorecard = [0]*len(self.params.value_tests)
                ValueError("Could not compare values for this file")
        else:
            self.value_scorecard = [0]*len(self.params.value_tests)
        
        self.scorecard = (self.value_scorecard + self.function_scorecard)
        self.update_score()
        self.make_error_msg()


    def print_results(self, fileobj=''):
        """
        Prints the results to python terminal or to a file if given

        Parameters:
            fileobj (str): File that results are written to (optional)
        """
        strs = []
        strs.append((f"Grader gave {self.grade:05.2f}/"
                    f"{self.params.points:05.2f} for {self.filename}"))
        if self.is_late:
            strs.append(f"[-{self.points_scored-self.grade}] File was submitted late")
        strs.append(self.error_comments)

        outstr = "\n".join(strs)

        if fileobj:
            fileobj.write(outstr + "\n")
        else:
            print(outstr)


    @property
    def identifier(self):
        """
        Returns a unique identifier for output dictionaries
        """
        if self.is_canvas:
            return (self.student_name, self.student_id)
        else:
            return self.student_name


def get_pyfiles(folder):
    """
    Helper function to get files but ignore __pycache__ directories
    that are created due to importing of modules
    """
    
    pyfiles = []
    test_files = os.listdir(folder)
    
    if '__pycache__' in test_files:
        test_files.remove('__pycache__') # Directory added due to import statements
    
    for f in test_files:
        if f.endswith(".py"):
            pyfiles.append(f)
    
    return pyfiles
