import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_cube_generation import TestCubeGeneration

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()

    # Add tests
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCubeGeneration))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Exit with appropriate exit code
    sys.exit(0 if result.wasSuccessful() else 1)
