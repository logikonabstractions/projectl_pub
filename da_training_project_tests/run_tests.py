import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_game_integration import (
    TestGameInitialization,
    TestGameRun,
    TestStrategyConfigLoading,
    TestRandomStrategy,
    TestBasicStrategy,
    TestActionEffects,
    TestGameState,
    TestCommandLineConfigLoading,
    TestUpgradePieceBug,
)

if __name__ == '__main__':
    suite = unittest.TestSuite()

    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGameInitialization))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGameRun))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStrategyConfigLoading))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRandomStrategy))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestBasicStrategy))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestActionEffects))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGameState))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCommandLineConfigLoading))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUpgradePieceBug))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)
