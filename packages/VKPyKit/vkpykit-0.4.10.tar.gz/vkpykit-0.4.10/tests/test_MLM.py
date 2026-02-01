"""
Unit tests for the MLM (Machine Learning Models) module of VKPyKit.

Tests cover:
- Model performance classification metrics
- Confusion matrix plotting
- Compatibility with various sklearn classifiers
- Edge cases
"""
import unittest
from unittest.mock import patch, MagicMock, ANY
import pytest
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

# Import the MLM module
from VKPyKit.MLM import MLM

# Create MLM instance for testing
mlm = MLM()


class TestMLMModelPerformanceClassification(unittest.TestCase):
    """Test cases for classification model performance evaluation."""
    
    def setUp(self):
        """Set up test data and models."""
        np.random.seed(42)
        
        # Create simple binary classification data
        self.X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        # Create simple separable classes
        self.y = pd.Series((self.X['feature1'] + self.X['feature2'] > 0).astype(int))
        
        # Train a simple model
        self.model = DecisionTreeClassifier(max_depth=3, random_state=42)
        self.model.fit(self.X, self.y)
    
    def test_returns_dataframe(self):
        """Test that model_performance_classification returns a DataFrame."""
        result = mlm.model_performance_classification(
            self.model, self.X, self.y, printall=False
        )
        
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_has_correct_columns(self):
        """Test that result has all expected metric columns."""
        result = mlm.model_performance_classification(
            self.model, self.X, self.y, printall=False
        )
        
        expected_columns = ['Accuracy', 'Recall', 'Precision', 'F1']
        
        for col in expected_columns:
            self.assertIn(col, result.columns)
    
    def test_metrics_in_valid_range(self):
        """Test that all metrics are between 0 and 1."""
        result = mlm.model_performance_classification(
            self.model, self.X, self.y, printall=False
        )
        
        for col in ['Accuracy', 'Recall', 'Precision', 'F1']:
            value = result[col].iloc[0]
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_perfect_classifier(self):
        """Test metrics for a perfect classifier."""
        # Create perfectly separable data
        X_perfect = pd.DataFrame({
            'x1': [0, 0, 1, 1],
            'x2': [0, 1, 0, 1]
        })
        y_perfect = pd.Series([0, 0, 1, 1])
        
        # Train a model that can perfectly separate
        perfect_model = DecisionTreeClassifier(max_depth=2, random_state=42)
        perfect_model.fit(X_perfect, y_perfect)
        
        result = mlm.model_performance_classification(
            perfect_model, X_perfect, y_perfect, printall=False
        )
        
        # All metrics should be 1.0 for perfect classification
        self.assertAlmostEqual(result['Accuracy'].iloc[0], 1.0, places=5)
        self.assertAlmostEqual(result['Recall'].iloc[0], 1.0, places=5)
        self.assertAlmostEqual(result['Precision'].iloc[0], 1.0, places=5)
        self.assertAlmostEqual(result['F1'].iloc[0], 1.0, places=5)
    
    @patch('VKPyKit.MLM.display')
    def test_printall_displays_output(self, mock_display):
        """Test that printall=True triggers display."""
        result = mlm.model_performance_classification(
            self.model, self.X, self.y, printall=True, title='Test Model'
        )
        
        # Check that display was called
        self.assertGreater(mock_display.call_count, 0)
    
    def test_custom_title(self):
        """Test that custom title is accepted."""
        # Should not raise an error
        result = mlm.model_performance_classification(
            self.model, self.X, self.y, printall=False, title='Custom Classifier'
        )
        
        self.assertIsInstance(result, pd.DataFrame)


class TestMLMPlotConfusionMatrix(unittest.TestCase):
    """Test cases for confusion matrix plotting."""
    
    def setUp(self):
        """Set up test data and model."""
        np.random.seed(42)
        
        self.X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        self.y = pd.Series((self.X['feature1'] + self.X['feature2'] > 0).astype(int))
        
        self.model = DecisionTreeClassifier(max_depth=3, random_state=42)
        self.model.fit(self.X, self.y)
    
    @patch('VKPyKit.MLM.plt')
    @patch('VKPyKit.MLM.sns')
    def test_plot_is_called(self, mock_sns, mock_plt):
        """Test that plotting functions are called."""
        mlm.plot_confusion_matrix(self.model, self.X, self.y)
        
        # Check that seaborn heatmap was called
        mock_sns.heatmap.assert_called_once()
        
        # Check that plt.show was called
        mock_plt.show.assert_called_once()
    
    @patch('VKPyKit.MLM.plt')
    @patch('VKPyKit.MLM.sns')
    def test_confusion_matrix_shape(self, mock_sns, mock_plt):
        """Test that confusion matrix has correct shape."""
        mlm.plot_confusion_matrix(self.model, self.X, self.y)
        
        # Get the confusion matrix passed to heatmap
        args, kwargs = mock_sns.heatmap.call_args
        conf_matrix = args[0]
        
        # Should be 2x2 for binary classification
        self.assertEqual(conf_matrix.shape, (2, 2))
    
    @patch('VKPyKit.MLM.plt')
    @patch('VKPyKit.MLM.sns')
    def test_custom_title(self, mock_sns, mock_plt):
        """Test custom title in confusion matrix."""
        custom_title = "My Custom Model"
        mlm.plot_confusion_matrix(self.model, self.X, self.y, title=custom_title)
        
        # Check that title was set
        mock_plt.title.assert_called_once()
        title_call = mock_plt.title.call_args[0][0]
        self.assertIn(custom_title, title_call)
    
    @patch('VKPyKit.MLM.plt')
    @patch('VKPyKit.MLM.sns')
    @patch('VKPyKit.MLM.sys.stdout')
    def test_stdout_flush(self, mock_stdout, mock_sns, mock_plt):
        """Test that stdout is flushed."""
        mlm.plot_confusion_matrix(self.model, self.X, self.y)
        
        # Verify stdout.flush was called
        mock_stdout.flush.assert_called()


class TestMLMWithMultipleClassifiers:
    """Test MLM module with various sklearn classifiers using pytest."""
    
    @pytest.fixture(autouse=True)
    def setup(self, classification_train_test_split):
        """Set up test data from fixture."""
        self.data = classification_train_test_split
    
    def test_with_random_forest(self, trained_rf_model):
        """Test MLM with Random Forest classifier."""
        result = mlm.model_performance_classification(
            trained_rf_model,
            self.data['X_test'],
            self.data['y_test'],
            printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert result['Accuracy'].iloc[0] > 0.5  # Should be better than random
    
    def test_with_decision_tree(self, trained_dt_model):
        """Test MLM with Decision Tree classifier."""
        result = mlm.model_performance_classification(
            trained_dt_model,
            self.data['X_test'],
            self.data['y_test'],
            printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert all(col in result.columns for col in ['Accuracy', 'Recall', 'Precision', 'F1'])
    
    def test_with_logistic_regression(self):
        """Test MLM with Logistic Regression."""
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(self.data['X_train'], self.data['y_train'])
        
        result = mlm.model_performance_classification(
            model,
            self.data['X_test'],
            self.data['y_test'],
            printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert result['Accuracy'].iloc[0] > 0
    
    def test_with_svm(self):
        """Test MLM with Support Vector Machine."""
        # Use a small subset for SVM (it's slower)
        X_small = self.data['X_train'].iloc[:100]
        y_small = self.data['y_train'].iloc[:100]
        
        model = SVC(kernel='linear', random_state=42)
        model.fit(X_small, y_small)
        
        result = mlm.model_performance_classification(
            model,
            self.data['X_test'].iloc[:50],
            self.data['y_test'].iloc[:50],
            printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
    
    def test_with_gradient_boosting(self):
        """Test MLM with Gradient Boosting classifier."""
        model = GradientBoostingClassifier(n_estimators=50, random_state=42)
        model.fit(self.data['X_train'], self.data['y_train'])
        
        result = mlm.model_performance_classification(
            model,
            self.data['X_test'],
            self.data['y_test'],
            printall=False,
            title='Gradient Boosting Model'
        )
        
        assert isinstance(result, pd.DataFrame)
        assert result['F1'].iloc[0] > 0


class TestMLMEdgeCases:
    """Test edge cases for MLM module."""
    
    def test_perfect_classifier_fixture(self, perfect_classifier_data):
        """Test with perfect classifier from fixture."""
        data = perfect_classifier_data
        
        result = mlm.model_performance_classification(
            data['model'],
            pd.DataFrame(data['X_test']),
            pd.Series(data['y_test']),
            printall=False
        )
        
        # Should have very high accuracy for separable data
        assert result['Accuracy'].iloc[0] > 0.9
    
    def test_imbalanced_data(self):
        """Test with imbalanced dataset."""
        # Create imbalanced data (90% class 0, 10% class 1)
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 2))
        y = pd.Series([0] * 90 + [1] * 10)
        
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit(X, y)
        
        result = mlm.model_performance_classification(
            model, X, y, printall=False
        )
        
        # Should still return valid metrics
        assert all(0 <= result[col].iloc[0] <= 1 for col in result.columns)
    
    @patch('VKPyKit.MLM.plt')
    @patch('VKPyKit.MLM.sns')
    def test_confusion_matrix_with_perfect_classifier(self, mock_sns, mock_plt, perfect_classifier_data):
        """Test confusion matrix with perfect classifier."""
        data = perfect_classifier_data
        
        mlm.plot_confusion_matrix(
            data['model'],
            pd.DataFrame(data['X_test']),
            pd.Series(data['y_test'])
        )
        
        # Should create plot without errors
        mock_sns.heatmap.assert_called_once()
        mock_plt.show.assert_called_once()
    
    def test_with_simple_classification_data(self, simple_classification_data):
        """Test with minimal classification dataset."""
        X = simple_classification_data[['feature_1', 'feature_2']]
        y = simple_classification_data['target']
        
        model = DecisionTreeClassifier(max_depth=2, random_state=42)
        model.fit(X, y)
        
        result = mlm.model_performance_classification(
            model, X, y, printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1


class TestMLMDataTypes:
    """Test MLM module with different data types."""
    
    def test_with_numpy_arrays(self):
        """Test that MLM works with numpy arrays converted to DataFrames."""
        np.random.seed(42)
        
        X_array = np.random.randn(100, 2)
        y_array = (X_array[:, 0] + X_array[:, 1] > 0).astype(int)
        
        # Convert to pandas
        X = pd.DataFrame(X_array)
        y = pd.Series(y_array)
        
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit(X, y)
        
        result = mlm.model_performance_classification(
            model, X, y, printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert all(col in result.columns for col in ['Accuracy', 'Recall', 'Precision', 'F1'])
    
    def test_with_integer_features(self):
        """Test with integer-valued features."""
        X = pd.DataFrame({
            'int_feature1': [1, 2, 3, 4, 5, 6, 7, 8],
            'int_feature2': [8, 7, 6, 5, 4, 3, 2, 1]
        })
        y = pd.Series([0, 0, 0, 0, 1, 1, 1, 1])
        
        model = DecisionTreeClassifier(max_depth=2, random_state=42)
        model.fit(X, y)
        
        result = mlm.model_performance_classification(
            model, X, y, printall=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert result['Accuracy'].iloc[0] > 0


if __name__ == '__main__':
    # Run unittest tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
