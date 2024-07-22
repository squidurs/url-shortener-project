import unittest
'''
Run this file to run all tests in the test directory.
Test file names must start with test_
Test files must use unittest by
-creating a class that inherits from unittest.TestCase
-and that class starts with Test

Use the command: python tests.py
to run this file
'''

loader = unittest.TestLoader()
suite = loader.discover('tests', pattern='test_*.py')

unittest.TextTestRunner().run(suite)
