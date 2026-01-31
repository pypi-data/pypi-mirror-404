"""
json_interface.py
weavebj1 - 2025

Reads json files that contain testing parameters

Part of python-grader library
"""

import importlib
import numpy as np
from mupygrader import test_file


class TestInfo:
    """
    TestInfo object represents a test with conditions

    Attributes:
        name (str): The name of the test
        error_comment (str): A statement given when the answer is incorrect
        weight (num): Relative weight of this test relative to others within a problem
        points (num): Calculated value of test based on problem's total points and weight
        invert (bool): By default, checks that test passed. If inverted, makes sure that it doesn't 
    """

    def __init__(self, name, error_comment, weight, invert):
        """
        Constructor for test object

        Parameters:
            [See attributes above. Points is a derived attribute]
        """
        self.name = name
        self.error_comment = error_comment
        self.weight = weight
        self.points = []
        self.invert = invert


class ValueTest(TestInfo):
    """
    Constructor for ValueTest object

    Attributes:
        abs_tol (num): Linear slop in results that is allowable (+/- diff)
        rel_tol (num): Multiplicative slop in results that is allowable (percent diff)
        [See TestInfo for parent attributes]
    """

    def __init__(self, variable, abs_tol=0, rel_tol=0, error_comment="",
                 test_weight=1, invert=False):
        """
        Constructor for ValueTest object

        Parameters:
            [See Attributes for ValueTest]
        """
        if len(error_comment) == 0:
            error_comment = f"Variable '{variable}' had incorrect value"

        super().__init__(variable, error_comment, test_weight, invert)
        self.variable = variable
        self.abs_tol = max(abs_tol, 1e-9) # Default for math.isclose() for floating point errors
        self.rel_tol = rel_tol


    def equal_tol(self, submission_val, key_val):
        """
        Compares two values based on tolerances in a value test
        If both tolerances are given, math.isclose is generous 
            (either can be true, both are not required to pass)

        Parameters:
            submission_val (any?): Value from the submission
            key_val (any?): Value from the answer key
        """

        if np.shape(key_val) != np.shape(submission_val):
            raise ValueError("Submission and Key had different numbers of data points")

        check_format = "unknown"
        if isinstance(key_val, np.ndarray):
            if np.issubdtype(key_val.dtype, np.number):
                check_format = "numeric"
            elif np.issubdtype(key_val.dtype, np.character):
                check_format = "string"
        else:
            if isinstance(key_val, (int, float, bool)):
                check_format = "numeric"
            elif isinstance(key_val, (str, list)):
                check_format = "string"


        match check_format:
            case "numeric":
                result = np.allclose(submission_val, key_val, rtol=self.rel_tol, atol=self.abs_tol, equal_nan=True)
            case "string":
                result = np.all(submission_val == key_val)
            case "unknown":
                raise ValueError("Tests for this type of data have not been set up")

        return result


class FunctionTest(TestInfo):
    """
    Constructor for FunctionTest object

    Attributes:
        function (str): Name of function from module
        module (str): Name of module that function is derived from
        [See TestInfo for parent attributes]
    """
    def __init__(self, function, module, error_comment="", test_weight=1, invert=False):
        """
        Constructor for FunctionTest object

        Parameters:
            [See attributes for FunctionTest]
        """

        if len(error_comment) == 0 and not invert:
            error_comment = f"Function '{function}' from '{module}' was not used"
        elif len(error_comment) == 0 and invert:
            error_comment = f"Function '{function}' from '{module}' was used, but should not be"

        super().__init__(function, error_comment, test_weight, invert)

        self.module = module
        self.function = function
        self.original = []
        self.mock = []
        try:
            self.module = importlib.import_module(self.module, function)
            self.original = getattr(self.module, function)
        except ModuleNotFoundError:
            print((f'Could not import from "{self.module}". Check that it is installed and '
                   'that its full name is spelled out correctly'))
            raise
        except AttributeError:
            print((f'"{function}" from "{self.module}" could not import. Check the '
                   'name of the function and make sure that all items are installed'))
            raise


class Problem:
    """
    Problem Object defines problem information from json files

    Attributes:
        assignment (assignment.Assignment): Parent assignment
        name (str): Name of problem for bookkeeping
        file_whitelist (str): Filename search filter for this problem
        solution_file (str): Name of file used as solution
        solution (test_file.TestFile): obj for solution file
        runner_file (str): Name of file used to run FunctionTest
        runner_hidden (bool): Keeps track of the runner file being available in .exe
        runner (test_file.TestFile): obj for runner file
        type (str): Either "script" or "function"
        points (num): Value of problem in points
        value_tests ([test_file.ValueTest]): List of value tests to assess 
        function_tests ([test_file.FunctionTest]): List of function tests to assess
        submissions ([test_file.Submission]): List of student submissions associated with problem
    """

    def __init__(self, asgmt, name, file_whitelist, solution_file, function_name='', runner_file='',
                 runner_hidden=False, pytype="script", prob_points=0, returned_vars=None,
                 used_functions=None):
        """
        Constructor for Problem object

        Parameters:
            asgmt (assignment.Assignment): Parent assignment
            name (str): Name of problem for bookkeeping
            file_whitelist (str): Filename search filter for this problem
            solution_file (str): Name of file used as solution
            function_name (str): Name of function to run from file
            runner_file (str): Name of file used to run FunctionTest
            runner_hidden (bool): Keeps track of the runner file being available in .exe
            pytype (str): Either "script" or "function"
            prob_points (num): Value of problem in points
            returned_vars ([dict]): List of value tests to assess (from json) 
            used_function ([dict]): List of function tests to assess (from json)
        """
        self.assignment = asgmt
        self.name = name
        self.file_whitelist = file_whitelist
        self.solution_file = solution_file
        self.function_name = function_name
        self.solution = []
        self.runner_file = runner_file
        self.runner_hidden = runner_hidden
        self.runner = []
        self.type = pytype
        self.points = prob_points

        self.value_tests = []
        if returned_vars:
            for t in returned_vars:
                self.value_tests.append(ValueTest(**t))

        self.function_tests = []
        if used_functions:
            for t in used_functions:
                self.function_tests.append(FunctionTest(**t))

        total_weights = sum(self.function_weights + self.value_weights)
        for t in self.all_tests:
            t.points = prob_points * t.weight / total_weights

        self.submissions = []


    def init_solution(self):
        """
        Creates the solution TestFile object based on a found solution file
        """
        self.solution = test_file.TestFile(self.solution_file, self)


    def init_runner(self):
        """
        Creates the runner TestFile object based on a found runner file
        """
        self.runner = test_file.TestFile(self.runner_file, self)


    def add_submission(self, file):
        """
        Creates a submission TestFile object and adds it to the list
        """
        self.submissions.append(test_file.Submission(file, self))

    @property
    def all_tests(self):
        """
        Returns all of the value and function tests in the problem
        """
        return [*self.value_tests, *self.function_tests]

    @property
    def value_weights(self):
        """
        Returns the weights of all value tests
        """
        weights = []
        for w in self.value_tests:
            weights.append(w.weight)
        return weights

    @property
    def function_weights(self):
        """
        Returns the weights of all function tests
        """
        weights = []
        for w in self.function_tests:
            weights.append(w.weight)
        return weights
