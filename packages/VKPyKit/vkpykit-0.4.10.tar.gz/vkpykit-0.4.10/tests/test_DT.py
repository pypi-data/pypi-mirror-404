import unittest
from unittest.mock import patch, MagicMock, call, ANY
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.datasets import make_classification
from sklearn.metrics import f1_score, recall_score

# Import the DT class
from VKPyKit.DT import DT


class TestDTModelPerformanceClassification(unittest.TestCase):
    """Test cases for model_performance_classification method"""

    def setUp(self):
        """Set up sample data and model for testing"""
        self.dt = DT()
        
        # Create a simple binary classification dataset
        np.random.seed(42)
        X, y = make_classification(n_samples=100, n_features=4, 
                                   n_informative=3, n_redundant=1,
                                   random_state=42)
        self.X = pd.DataFrame(X, columns=['f1', 'f2', 'f3', 'f4'])
        self.y = pd.Series(y)
        
        # Train a simple model
        self.model = DecisionTreeClassifier(random_state=42, max_depth=3)
        self.model.fit(self.X, self.y)

    def test_model_performance_basic(self):
        """Test basic performance metric calculation"""
        result = DT.model_performance_classification(
            model=self.model,
            predictors=self.X,
            expected=self.y,
            printall=False
        )
        
        # Check that result is a DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        
        # Check that all required columns are present
        expected_columns = ['Accuracy', 'Recall', 'Precision', 'F1']
        for col in expected_columns:
            self.assertIn(col, result.columns)
        
        # Check that metrics are between 0 and 1
        for col in expected_columns:
            self.assertGreaterEqual(result[col].iloc[0], 0.0)
            self.assertLessEqual(result[col].iloc[0], 1.0)

    @patch('VKPyKit.DT.display')
    def test_model_performance_with_printall(self, mock_display):
        """Test model performance with printall=True"""
        result = DT.model_performance_classification(
            model=self.model,
            predictors=self.X,
            expected=self.y,
            printall=True,
            title='Test Model'
        )
        
        # Check that display was called (for HTML output)
        self.assertEqual(mock_display.call_count, 2)
        
        # Check that result is still a valid DataFrame
        self.assertIsInstance(result, pd.DataFrame)

    def test_model_performance_custom_title(self):
        """Test with custom title parameter"""
        custom_title = 'Custom Decision Tree'
        result = DT.model_performance_classification(
            model=self.model,
            predictors=self.X,
            expected=self.y,
            printall=False,
            title=custom_title
        )
        
        # Should still return valid results
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(result['Accuracy'].iloc[0], 0)


class TestDTPlotConfusionMatrix(unittest.TestCase):
    """Test cases for plot_confusion_matrix method"""

    def setUp(self):
        """Set up sample data and model for testing"""
        np.random.seed(42)
        X, y = make_classification(n_samples=100, n_features=4,
                                   n_informative=3, n_redundant=1,
                                   random_state=42)
        self.X = pd.DataFrame(X, columns=['f1', 'f2', 'f3', 'f4'])
        self.y = pd.Series(y)
        
        self.model = DecisionTreeClassifier(random_state=42, max_depth=3)
        self.model.fit(self.X, self.y)

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.sns')
    def test_plot_confusion_matrix_basic(self, mock_sns, mock_plt):
        """Test basic confusion matrix plotting"""
        DT.plot_confusion_matrix(
            model=self.model,
            predictors=self.X,
            expected=self.y,
            title='Test Confusion Matrix'
        )
        
        # Check that plt.figure was called
        mock_plt.figure.assert_called_once_with(figsize=(6, 4))
        
        # Check that plt.title was called
        mock_plt.title.assert_called_once()
        
        # Check that seaborn heatmap was called
        mock_sns.heatmap.assert_called_once()
        
        # Check that plt.show was called
        mock_plt.show.assert_called_once()

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.sns')
    def test_plot_confusion_matrix_custom_title(self, mock_sns, mock_plt):
        """Test confusion matrix with custom title"""
        custom_title = 'My Custom Model'
        DT.plot_confusion_matrix(
            model=self.model,
            predictors=self.X,
            expected=self.y,
            title=custom_title
        )
        
        # Check that title contains our custom text
        call_args = mock_plt.title.call_args
        self.assertIn(custom_title, call_args[0][0])

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.sns')
    @patch('VKPyKit.DT.metrics.confusion_matrix')
    def test_plot_confusion_matrix_creates_correct_labels(self, mock_cm, mock_sns, mock_plt):
        """Test that confusion matrix creates correct percentage labels"""
        # Mock the confusion matrix to return a known value
        mock_cm.return_value = np.array([[40, 10], [5, 45]])
        
        DT.plot_confusion_matrix(
            model=self.model,
            predictors=self.X,
            expected=self.y,
            title='Test'
        )
        
        # Check that heatmap was called
        mock_sns.heatmap.assert_called_once()
        
        # The labels should contain both counts and percentages
        call_args = mock_sns.heatmap.call_args
        labels = call_args[1]['annot']
        
        # Check that labels have the right shape
        self.assertEqual(labels.shape, (2, 2))


class TestDTTuneDecisionTree(unittest.TestCase):
    """Test cases for tune_decision_tree method"""

    def setUp(self):
        """Set up sample data for testing"""
        np.random.seed(42)
        X, y = make_classification(n_samples=200, n_features=5,
                                   n_informative=4, n_redundant=1,
                                   random_state=42)
        
        # Split into train and test
        split_idx = 150
        self.X_train = pd.DataFrame(X[:split_idx], columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.y_train = pd.Series(y[:split_idx])
        self.X_test = pd.DataFrame(X[split_idx:], columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.y_test = pd.Series(y[split_idx:])

    def test_tune_decision_tree_basic(self):
        """Test basic hyperparameter tuning"""
        # Use small parameter ranges for faster testing
        best_model = DT.tune_decision_tree(
            X_train=self.X_train,
            y_train=self.y_train,
            X_test=self.X_test,
            y_test=self.y_test,
            max_depth_v=(2, 5, 1),           # Only test depths 2, 3, 4
            max_leaf_nodes_v=(5, 11, 5),     # Only test 5, 10
            min_samples_split_v=(10, 21, 10), # Only test 10, 20
            printall=False
        )
        
        # Check that a model was returned
        self.assertIsInstance(best_model, DecisionTreeClassifier)
        
        # Check that the model has been fitted
        self.assertTrue(hasattr(best_model, 'tree_'))

    @patch('builtins.print')
    @patch('VKPyKit.DT.display')
    def test_tune_decision_tree_with_printall(self, mock_display, mock_print):
        """Test tuning with printall=True"""
        best_model = DT.tune_decision_tree(
            X_train=self.X_train,
            y_train=self.y_train,
            X_test=self.X_test,
            y_test=self.y_test,
            max_depth_v=(2, 4, 1),
            max_leaf_nodes_v=(5, 11, 5),
            min_samples_split_v=(10, 21, 10),
            printall=True
        )
        
        # Check that display was called (for showing results)
        self.assertGreater(mock_display.call_count, 0)
        
        # Check that a valid model was returned
        self.assertIsInstance(best_model, DecisionTreeClassifier)

    def test_tune_decision_tree_returns_best_model(self):
        """Test that the function returns a functional best model"""
        best_model = DT.tune_decision_tree(
            X_train=self.X_train,
            y_train=self.y_train,
            X_test=self.X_test,
            y_test=self.y_test,
            max_depth_v=(2, 5, 1),
            max_leaf_nodes_v=(5, 11, 5),
            min_samples_split_v=(10, 21, 10),
            printall=False
        )
        
        # Test that the model can make predictions
        predictions = best_model.predict(self.X_test)
        
        # Check that predictions have the right shape
        self.assertEqual(len(predictions), len(self.y_test))
        
        # Check that predictions are binary (0 or 1)
        self.assertTrue(all(pred in [0, 1] for pred in predictions))


class TestDTPlotFeatureImportance(unittest.TestCase):
    """Test cases for plot_feature_importance method"""

    def setUp(self):
        """Set up a trained model for testing"""
        np.random.seed(42)
        X, y = make_classification(n_samples=100, n_features=5,
                                   n_informative=4, n_redundant=1,
                                   random_state=42)
        self.X = pd.DataFrame(X, columns=['feature1', 'feature2', 'feature3', 'feature4', 'feature5'])
        self.y = pd.Series(y)
        
        self.model = DecisionTreeClassifier(random_state=42, max_depth=5)
        self.model.fit(self.X, self.y)
        self.feature_names = ['feature1', 'feature2', 'feature3', 'feature4', 'feature5']

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.sns')
    @patch('VKPyKit.DT.display')
    def test_plot_feature_importance_basic(self, mock_display, mock_sns, mock_plt):
        """Test basic feature importance plotting"""
        DT.plot_feature_importance(
            model=self.model,
            features=self.feature_names,
            figsize=(10, 6)
        )
        
        # Check that display was called (for showing dataframe)
        mock_display.assert_called_once()
        
        # Check that plt.figure was called with correct figsize
        mock_plt.figure.assert_called_once_with(figsize=(10, 6))
        
        # Check that seaborn barplot was called
        mock_sns.barplot.assert_called_once()
        
        # Check that plt.show was called
        mock_plt.show.assert_called_once()

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.sns')
    @patch('VKPyKit.DT.display')
    def test_plot_feature_importance_top_n(self, mock_display, mock_sns, mock_plt):
        """Test plotting only top N features"""
        DT.plot_feature_importance(
            model=self.model,
            features=self.feature_names,
            numberoftopfeatures=3
        )
        
        # Check that plotting functions were called
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.sns')
    @patch('VKPyKit.DT.display')
    def test_plot_feature_importance_ignore_zero(self, mock_display, mock_sns, mock_plt):
        """Test ignoring features with zero importance"""
        DT.plot_feature_importance(
            model=self.model,
            features=self.feature_names,
            ignoreZeroImportance=True
        )
        
        # Check that plotting functions were called
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()


class TestDTVisualizeDecisionTree(unittest.TestCase):
    """Test cases for visualize_decision_tree method"""

    def setUp(self):
        """Set up a trained model for testing"""
        np.random.seed(42)
        X, y = make_classification(n_samples=100, n_features=4,
                                   n_informative=3, n_redundant=1,
                                   n_classes=2, random_state=42)
        self.X = pd.DataFrame(X, columns=['f1', 'f2', 'f3', 'f4'])
        self.y = pd.Series(y)
        
        self.model = DecisionTreeClassifier(random_state=42, max_depth=3)
        self.model.fit(self.X, self.y)
        self.feature_names = ['f1', 'f2', 'f3', 'f4']
        self.class_names = ['Class0', 'Class1']

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.tree.plot_tree')
    @patch('VKPyKit.DT.display')
    def test_visualize_decision_tree_basic(self, mock_display, mock_plot_tree, mock_plt):
        """Test basic decision tree visualization"""
        # Mock the plot_tree return value to simulate tree elements
        mock_element = MagicMock()
        mock_element.arrow_patch = MagicMock()
        mock_plot_tree.return_value = [mock_element]
        
        DT.visualize_decision_tree(
            model=self.model,
            features=self.feature_names,
            classes=self.class_names
        )
        
        # Check that plt.figure was called
        mock_plt.figure.assert_called_once_with(figsize=(20, 10))
        
        # Check that tree.plot_tree was called
        mock_plot_tree.assert_called_once()
        
        # Check that plt.show was called
        mock_plt.show.assert_called_once()

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.tree.plot_tree')
    @patch('VKPyKit.DT.tree.export_text')
    @patch('VKPyKit.DT.display')
    @patch('builtins.print')
    def test_visualize_decision_tree_with_text(self, mock_print, mock_display, 
                                               mock_export_text, mock_plot_tree, mock_plt):
        """Test visualization with text representation"""
        mock_element = MagicMock()
        mock_element.arrow_patch = MagicMock()
        mock_plot_tree.return_value = [mock_element]
        mock_export_text.return_value = "Tree text representation"
        
        DT.visualize_decision_tree(
            model=self.model,
            features=self.feature_names,
            classes=self.class_names,
            showtext=True
        )
        
        # Check that export_text was called
        mock_export_text.assert_called_once()
        
        # Check that print was called to show the text
        mock_print.assert_called()

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.tree.plot_tree')
    @patch('VKPyKit.DT.display')
    @patch('VKPyKit.DT.DT.plot_feature_importance')
    @patch('builtins.print')
    def test_visualize_decision_tree_with_importance(self, mock_print, 
                                                     mock_plot_importance, mock_display,
                                                     mock_plot_tree, mock_plt):
        """Test visualization with feature importance"""
        mock_element = MagicMock()
        mock_element.arrow_patch = MagicMock()
        mock_plot_tree.return_value = [mock_element]
        
        DT.visualize_decision_tree(
            model=self.model,
            features=self.feature_names,
            classes=self.class_names,
            showimportance=True
        )
        
        # Check that plot_feature_importance was called
        mock_plot_importance.assert_called_once()


class TestDTPrepruning(unittest.TestCase):
    """Test cases for prepruning_nodes_samples_split method"""

    def setUp(self):
        """Set up sample data for testing"""
        np.random.seed(42)
        X, y = make_classification(n_samples=150, n_features=5,
                                   n_informative=4, n_redundant=1,
                                   random_state=42)
        
        split_idx = 100
        self.X_train = pd.DataFrame(X[:split_idx], columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.y_train = pd.Series(y[:split_idx])
        self.X_test = pd.DataFrame(X[split_idx:], columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.y_test = pd.Series(y[split_idx:])

    @patch('VKPyKit.DT.display')
    @patch('builtins.print')
    def test_prepruning_basic(self, mock_print, mock_display):
        """Test basic pre-pruning functionality"""
        DT.prepruning_nodes_samples_split(
            X_train=self.X_train,
            y_train=self.y_train,
            X_test=self.X_test,
            y_test=self.y_test,
            min_samples_split_v=(10, 31, 10),  # Small range for testing
            printall=True
        )
        
        # Check that display was called (for showing results)
        self.assertGreater(mock_display.call_count, 0)


class TestDTPostpruning(unittest.TestCase):
    """Test cases for postpruning_cost_complexity method"""

    def setUp(self):
        """Set up sample data for testing"""
        np.random.seed(42)
        X, y = make_classification(n_samples=150, n_features=5,
                                   n_informative=4, n_redundant=1,
                                   random_state=42)
        
        split_idx = 100
        self.X_train = pd.DataFrame(X[:split_idx], columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.y_train = pd.Series(y[:split_idx])
        self.X_test = pd.DataFrame(X[split_idx:], columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        self.y_test = pd.Series(y[split_idx:])

    @patch('VKPyKit.DT.plt')
    @patch('VKPyKit.DT.display')
    @patch('builtins.print')
    def test_postpruning_basic(self, mock_print, mock_display, mock_plt):
        """Test basic post-pruning with cost complexity"""
        DT.postpruning_cost_complexity(
            X_train=self.X_train,
            y_train=self.y_train,
            X_test=self.X_test,
            y_test=self.y_test,
            printall=True
        )
        
        # Check that display was called for showing results
        self.assertGreater(mock_display.call_count, 0)
        
        # Check that plotting was done
        self.assertGreater(mock_plt.subplot.call_count, 0)


class TestDTConstants(unittest.TestCase):
    """Test cases for DT class constants and initialization"""

    def test_dt_initialization(self):
        """Test DT class initialization"""
        dt_instance = DT()
        self.assertIsInstance(dt_instance, DT)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
