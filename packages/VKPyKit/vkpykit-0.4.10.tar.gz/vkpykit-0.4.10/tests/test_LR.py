"""
Unit tests for the LR (Linear Regression) module of VKPyKit.

Tests cover:
- MAPE score calculation
- Adjusted R² calculation
- Regression model performance metrics
- Edge cases
"""
import unittest
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

# Import the LR module
from VKPyKit.LR import LR

# Create LR instance for testing
lr = LR()


class TestLRMapeScore(unittest.TestCase):
    """Test cases for MAPE score calculation."""
    
    def test_mape_score_basic(self):
        """Test MAPE calculation with basic values."""
        targets = np.array([100, 200, 150, 300])
        predictions = np.array([90, 210, 140, 320])
        
        expected_mape = np.mean([10, 5, 6.67, 6.67])  # Approximate
        actual_mape = lr.mape_score(targets, predictions)
        
        self.assertAlmostEqual(actual_mape, 7.0833, places=2)
    
    def test_mape_score_perfect_prediction(self):
        """Test MAPE when predictions are perfect."""
        targets = np.array([100, 200, 150, 300])
        predictions = np.array([100, 200, 150, 300])
        
        mape = lr.mape_score(targets, predictions)
        
        self.assertEqual(mape, 0.0)
    
    def test_mape_score_with_series(self):
        """Test MAPE calculation with pandas Series."""
        targets = pd.Series([100, 200, 150, 300])
        predictions = pd.Series([90, 210, 140, 320])
        
        mape = lr.mape_score(targets, predictions)
        
        self.assertIsInstance(mape, (float, np.floating))
        self.assertGreater(mape, 0)


class TestLRAdjustedR2Score(unittest.TestCase):
    """Test cases for Adjusted R² calculation."""
    
    def test_adj_r2_basic(self):
        """Test adjusted R² calculation."""
        # Create simple dataset
        X = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10]
        })
        y_true = np.array([3, 7, 11, 15, 19])
        y_pred = np.array([3.1, 6.9, 11.2, 14.8, 19.1])
        
        adj_r2 = lr.adj_r2_score(X, y_true, y_pred)
        
        # Adjusted R² should be slightly less than regular R²
        # and should be close to 1 for good predictions
        self.assertGreater(adj_r2, 0.9)
        self.assertLessEqual(adj_r2, 1.0)
    
    def test_adj_r2_perfect_fit(self):
        """Test adjusted R² with perfect predictions."""
        X = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'x2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        })
        y_true = np.array([3, 7, 11, 15, 19, 23, 27, 31, 35, 39])
        y_pred = y_true.copy()  # Perfect predictions
        
        adj_r2 = lr.adj_r2_score(X, y_true, y_pred)
        
        self.assertAlmostEqual(adj_r2, 1.0, places=5)
    
    def test_adj_r2_penalty_for_features(self):
        """Test that adjusted R² penalizes additional features."""
        n_samples = 100
        
        # Dataset with 2 features
        X_small = pd.DataFrame(np.random.randn(n_samples, 2))
        y = np.random.randn(n_samples)
        y_pred = y + np.random.randn(n_samples) * 0.1
        
        adj_r2_small = lr.adj_r2_score(X_small, y, y_pred)
        
        # Same dataset with 10 features (more features should lower adj R²)
        X_large = pd.DataFrame(np.random.randn(n_samples, 10))
        adj_r2_large = lr.adj_r2_score(X_large, y, y_pred)
        
        # With more features, adjusted R² should be lower (penalty for complexity)
        self.assertLess(adj_r2_large, adj_r2_small)


class TestLRModelPerformanceRegression(unittest.TestCase):
    """Test cases for regression model performance evaluation."""
    
    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        self.X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        self.y = 2 * self.X['feature1'] + 3 * self.X['feature2'] + np.random.randn(100) * 0.5
        
        # Train a simple model
        self.model = LinearRegression()
        self.model.fit(self.X, self.y)
    
    def test_model_performance_returns_dataframe(self):
        """Test that model_performance_regression returns a DataFrame."""
        result = lr.model_performance_regression(self.model, self.X, self.y)
        
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_model_performance_has_correct_columns(self):
        """Test that result has all expected metric columns."""
        result = lr.model_performance_regression(self.model, self.X, self.y)
        
        expected_columns = ['RMSE', 'MAE', 'MAPE', 'R-squared', 'Adj R-squared']
        
        for col in expected_columns:
            self.assertIn(col, result.columns)
    
    def test_model_performance_metric_ranges(self):
        """Test that metrics are in reasonable ranges."""
        result = lr.model_performance_regression(self.model, self.X, self.y)
        
        # R² should be between 0 and 1 for a decent model
        self.assertGreater(result['R-squared'].iloc[0], 0.5)
        self.assertLessEqual(result['R-squared'].iloc[0], 1.0)
        
        # Adjusted R² should be slightly less than R²
        self.assertLessEqual(result['Adj R-squared'].iloc[0], result['R-squared'].iloc[0])
        
        # RMSE and MAE should be positive
        self.assertGreater(result['RMSE'].iloc[0], 0)
        self.assertGreater(result['MAE'].iloc[0], 0)
    
    def test_model_performance_perfect_model(self):
        """Test metrics for a perfect model."""
        # Create perfect predictions
        y_pred = self.y.copy()
        
        # Create a mock model that returns perfect predictions
        class PerfectModel:
            def predict(self, X):
                return y_pred
        
        perfect_model = PerfectModel()
        result = lr.model_performance_regression(perfect_model, self.X, self.y)
        
        # For perfect predictions:
        # R² should be 1.0
        self.assertAlmostEqual(result['R-squared'].iloc[0], 1.0, places=5)
        # RMSE should be very close to 0
        self.assertAlmostEqual(result['RMSE'].iloc[0], 0.0, places=5)
        # MAE should be very close to 0
        self.assertAlmostEqual(result['MAE'].iloc[0], 0.0, places=5)


class TestLRWithFixtures:
    """Test LR module using pytest fixtures."""
    
    def test_with_regression_data(self, regression_df, trained_lr_model):
        """Test model performance with fixture data."""
        X = regression_df.drop('price', axis=1).select_dtypes(include=[np.number])
        y = regression_df['price']
        
        result = lr.model_performance_regression(trained_lr_model, X, y)
        
        assert isinstance(result, pd.DataFrame)
        assert 'RMSE' in result.columns
        assert 'R-squared' in result.columns
        assert result['R-squared'].iloc[0] > 0  # Should have some predictive power
    
    def test_with_simple_regression_data(self, simple_regression_data):
        """Test with simple regression data."""
        X = simple_regression_data[['x1', 'x2']]
        y = simple_regression_data['y']
        
        model = LinearRegression()
        model.fit(X, y)
        
        result = lr.model_performance_regression(model, X, y)
        
        # Simple linear data should have very high R²
        assert result['R-squared'].iloc[0] > 0.95
    
    def test_decision_tree_regressor(self, regression_train_test_split):
        """Test that LR module works with different regression models."""
        data = regression_train_test_split
        
        # Train a Decision Tree Regressor
        dt_model = DecisionTreeRegressor(max_depth=5, random_state=42)
        dt_model.fit(data['X_train'], data['y_train'])
        
        # Evaluate on test set
        result = lr.model_performance_regression(dt_model, data['X_test'], data['y_test'])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert all(col in result.columns for col in ['RMSE', 'MAE', 'MAPE', 'R-squared', 'Adj R-squared'])


class TestLREdgeCases:
    """Test edge cases for LR module."""
    
    def test_single_feature_model(self):
        """Test with single feature."""
        X = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
        y = pd.Series([2, 4, 6, 8, 10])
        
        model = LinearRegression()
        model.fit(X, y)
        
        result = lr.model_performance_regression(model, X, y)
        
        # Perfect linear relationship should give R² ≈ 1
        assert result['R-squared'].iloc[0] > 0.99
    
    def test_high_dimensional_data(self):
        """Test with many features."""
        np.random.seed(42)
        n_samples = 100
        n_features = 50
        
        X = pd.DataFrame(np.random.randn(n_samples, n_features))
        y = pd.Series(np.random.randn(n_samples))
        
        model = LinearRegression()
        model.fit(X, y)
        
        result = lr.model_performance_regression(model, X, y)
        
        # Adjusted R² should be significantly less than R² due to many features
        assert result['Adj R-squared'].iloc[0] < result['R-squared'].iloc[0]


if __name__ == '__main__':
    # Run unittest tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
