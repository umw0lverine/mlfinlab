"""
Test RegressionModelFingerprint, ClassificationModelFingerprint implementations
"""

import unittest
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.datasets import load_boston, load_breast_cancer
from mlfinlab.feature_importance import RegressionModelFingerprint, ClassificationModelFingerprint


# pylint: disable=invalid-name
# pylint: disable=unsubscriptable-object

class TestModelFingerprint(unittest.TestCase):
    """
    Test model fingerprint functions
    """

    def setUp(self):
        """
        Set the file path for the sample dollar bars data.
        """

        self.X, self.y = load_boston(return_X_y=True)
        self.X = pd.DataFrame(self.X[:100])
        self.y = pd.Series(self.y[:100])

        self.reg_1 = RandomForestRegressor(n_estimators=10, random_state=42)
        self.reg_2 = LinearRegression(fit_intercept=True, normalize=False)
        self.reg_1.fit(self.X, self.y)
        self.reg_2.fit(self.X, self.y)

        self.reg_1_fingerprint = RegressionModelFingerprint(self.reg_1, self.X, num_values=20)
        self.reg_2_fingerprint = RegressionModelFingerprint(self.reg_2, self.X, num_values=20)

        self.reg_1_fingerprint.fit()
        self.reg_2_fingerprint.fit()

    def test_linear_effect(self):
        """
        Test get_linear_effect for various regression models and num_values.
        """

        # Test the most informative feature effects for reg_1
        informative_features_1 = [0, 5, 6, 12]
        for feature, effect_value in zip(informative_features_1, [0.0577, 0.5102, 0.136, 0.2139]):
            self.assertAlmostEqual(self.reg_1_fingerprint.linear_effect['norm'][feature], effect_value, delta=1e-3)

        # Test the most informative feature effects for reg_2
        informative_features_2 = [0, 2, 4, 5, 6]
        for feature, effect_value in zip(informative_features_2, [0.13, 0.0477, 0.1, 0.4, 0.208]):
            self.assertAlmostEqual(self.reg_2_fingerprint.linear_effect['norm'][feature], effect_value, delta=1e-3)

        # Test fingerprints with bigger num_values
        reg_1_fingerpint_70 = RegressionModelFingerprint(self.reg_1, self.X, num_values=70)
        reg_2_fingerpint_70 = RegressionModelFingerprint(self.reg_2, self.X, num_values=70)

        reg_1_fingerpint_70.fit()
        reg_2_fingerpint_70.fit()

        # Increasing the number of samples doesn't change feature effect massively
        for feature in informative_features_1:
            self.assertAlmostEqual(self.reg_1_fingerprint.linear_effect['norm'][feature],
                                   reg_1_fingerpint_70.linear_effect['norm'][feature], delta=0.05)

        for feature in informative_features_2:
            self.assertAlmostEqual(self.reg_2_fingerprint.linear_effect['norm'][feature],
                                   reg_2_fingerpint_70.linear_effect['norm'][feature], delta=0.05)

    def test_non_linear_effect(self):
        """
        Test get_non_linear_effect for various regression models and num_values.
        """

        # Test the most informative feature effects for reg_1
        informative_features_1 = [0, 5, 6, 12]
        for feature, effect_value in zip(informative_features_1, [0.0758, 0.3848, 0.1, 0.28]):
            self.assertAlmostEqual(self.reg_1_fingerprint.non_linear_effect['norm'][feature], effect_value, delta=1e-3)

        # Non-linear effect to linear model is zero
        for effect_value in self.reg_2_fingerprint.non_linear_effect['raw'].values():
            self.assertAlmostEqual(effect_value, 0, delta=1e-8)

        # Test fingerprints with bigger num_values
        reg_1_fingerpint_70 = RegressionModelFingerprint(self.reg_1, self.X, num_values=70)
        reg_2_fingerpint_70 = RegressionModelFingerprint(self.reg_2, self.X, num_values=70)

        reg_1_fingerpint_70.fit()
        reg_2_fingerpint_70.fit()

        # Increasing the number of samples doesn't change feature effect massively
        for feature in informative_features_1:
            self.assertAlmostEqual(self.reg_1_fingerprint.non_linear_effect['norm'][feature],
                                   reg_1_fingerpint_70.non_linear_effect['norm'][feature], delta=0.05)

        for effect_value in reg_2_fingerpint_70.non_linear_effect['raw'].values():
            self.assertAlmostEqual(effect_value, 0, delta=1e-8)

    def test_pairwise_effect(self):
        """
        Test get_pairwise_effect for various regression models and num_values.
        """

        combinations = [(0, 5), (0, 12), (1, 2), (5, 7), (3, 6), (4, 9)]
        self.reg_1_fingerprint.get_pairwise_effect(combinations)
        self.reg_2_fingerprint.get_pairwise_effect(combinations)
        for pair, effect_value in zip(combinations, [0.203, 0.17327, 0.005, 0.032, 0, 0.00004]):
            self.assertAlmostEqual(self.reg_1_fingerprint.pair_wise_effect['raw'][str(pair)], effect_value, delta=1e-3)

        # Pairwise effect for linear model should be zero
        for pair in combinations:
            self.assertAlmostEqual(self.reg_2_fingerprint.pair_wise_effect['raw'][str(pair)], 0, delta=1e-9)

    def test_classification_fingerpint(self):
        """
        Test model fingerprint values (linear, non-linear, pairwise) for classification model.
        """
        X, y = load_breast_cancer(return_X_y=True)
        X, y = pd.DataFrame(X), pd.Series(y)
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X, y)
        clf_fingerpint = ClassificationModelFingerprint(clf, X, num_values=20)
        clf_fingerpint.fit()
        clf_fingerpint.get_pairwise_effect([(0, 1), (2, 3), (8, 9)])

        for feature, effect in zip([0, 2, 3, 8, 9], [0.0068, 0.0249, 0.014, 0]):
            self.assertAlmostEqual(clf_fingerpint.linear_effect['raw'][feature], effect, delta=1e-3)

        for feature, effect in zip([0, 2, 3, 8, 9], [0.0062, 0.0217, 0.0155, 0.0013]):
            self.assertAlmostEqual(clf_fingerpint.non_linear_effect['raw'][feature], effect, delta=1e-3)

        for comb, effect in zip([(0, 1), (2, 3), (8, 9)], [0.008, 0.0087, 0]):
            self.assertAlmostEqual(clf_fingerpint.pair_wise_effect['raw'][str(comb)], effect, delta=1e-3)

    def test_plot_effects(self):
        """
        Test plot_effects function.
        """

        self.reg_1_fingerprint.pair_wise_effect = None
        fig_1 = self.reg_1_fingerprint.plot_effects()
        self.reg_1_fingerprint.get_pairwise_effect([(1, 2), (3, 5)])
        fig_2 = self.reg_1_fingerprint.plot_effects()
