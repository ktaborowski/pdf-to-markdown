#!/usr/bin/env python3

"""Run unit tests for PDF to Markdown converter."""

import unittest
import sys


if __name__ == '__main__':
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir)
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests fail
    sys.exit(not result.wasSuccessful()) 