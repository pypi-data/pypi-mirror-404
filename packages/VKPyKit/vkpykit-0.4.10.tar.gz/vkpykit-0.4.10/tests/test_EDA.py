import unittest
from unittest.mock import patch, MagicMock, call, ANY
import pandas as pd
import numpy as np

# Assuming vkpykit is in the python path.
# If not, you might need to adjust sys.path.
from VKPyKit.EDA import *
EDA = EDA()
class TestEDAPairplotAll(unittest.TestCase):

    def setUp(self):
        """Set up a sample DataFrame and EDA instance for testing."""
        self.eda = EDA()
        self.df = pd.DataFrame({
            'numeric_1': np.random.rand(20),
            'numeric_2': np.random.rand(20),
            'low_cardinality_numeric': [1, 2] * 10,  # Only 2 unique values
            'categorical_hue': ['group_A'] * 10 + ['group_B'] * 10,
            'target': [0, 1] * 10,
            'categorical_other': ['cat1'] * 5 + ['cat2'] * 5 + ['cat3'] * 5 + ['cat4'] * 5,
        })

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_pairplot_all_default_behavior(self, mock_sns, mock_plt):
        """
        Test pairplot_all with default arguments.
        It should automatically select numeric features with enough unique values.
        """
        self.eda.pairplot_all(self.df)

        # Expected features have > 4 unique values (default)
        expected_features = ['numeric_1', 'numeric_2']
        
        # Check if pairplot was called once
        mock_sns.pairplot.assert_called_once()
        
        # Check the arguments it was called with
        args, kwargs = mock_sns.pairplot.call_args
        self.assertEqual(args[0].equals(self.df), True)
        self.assertEqual(kwargs['vars'], expected_features)
        self.assertEqual(kwargs['diag_kind'], 'kde')
        
        # Check if plot is shown
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_pairplot_all_with_features(self, mock_sns, mock_plt):
        """
        Test pairplot_all when a specific list of features is provided.
        """
        custom_features = ['numeric_1', 'low_cardinality_numeric']
        self.eda.pairplot_all(self.df, features=custom_features)

        # Check if pairplot was called with the custom features
        mock_sns.pairplot.assert_called_once()
        _, kwargs = mock_sns.pairplot.call_args
        self.assertEqual(kwargs['vars'], custom_features)
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_pairplot_all_with_hues(self, mock_sns, mock_plt):
        """
        Test pairplot_all when a list of hues is provided.
        It should call pairplot for each hue.
        """
        hues_list = ['categorical_hue', 'categorical_other']
        self.eda.pairplot_all(self.df, hues=hues_list)

        # Expected features to be plotted against
        expected_features = ['numeric_1', 'numeric_2']

        # Check that pairplot is called for each hue
        self.assertEqual(mock_sns.pairplot.call_count, len(hues_list))

        # Check the calls were made with the correct hue
        expected_calls = [
            call(self.df, vars=expected_features, hue='categorical_hue', diag_kind='kde'),
            call(self.df, vars=expected_features, hue='categorical_other', diag_kind='kde')
        ]
        mock_sns.pairplot.assert_has_calls(expected_calls, any_order=True)
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_pairplot_all_with_min_unique_values(self, mock_sns, mock_plt):
        """
       Test that `min_unique_values_for_pairplot` correctly filters features.
        """
        # With min_unique_values_for_pairplot=1, 'low_cardinality_numeric' should be included
        self.eda.pairplot_all(self.df, min_unique_values_for_pairplot=1)

        expected_features = ['numeric_1', 'numeric_2', 'low_cardinality_numeric']
        
        mock_sns.pairplot.assert_called_once()
        _, kwargs = mock_sns.pairplot.call_args
        self.assertEqual(sorted(kwargs['vars']), sorted(expected_features))
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_pairplot_all_empty_dataframe(self, mock_sns, mock_plt):
        """
        Test that the function handles an empty DataFrame without crashing.
        """
        empty_df = pd.DataFrame()
        self.eda.pairplot_all(empty_df)

        # pairplot should not be called if there are no valid features
        mock_sns.pairplot.assert_not_called()
        mock_plt.show.assert_called_once() # It will still try to show a (likely empty) plot

class TestEDA(unittest.TestCase):

    def setUp(self):
        """Set up a sample DataFrame and EDA instance for testing."""
        self.eda = EDA()
        self.df = pd.DataFrame({
            'predictor': ['A', 'A', 'B', 'B', 'C'],
            'target': [0, 1, 0, 1, 0],
            'numeric': [10, 20, 15, 25, 5],
            'category': ['X', 'Y', 'X', 'Y', 'X']
        })

    @patch('builtins.print')
    @patch('vkpykit.EDA.plt')
    @patch('pandas.crosstab')
    def test_barplot_stacked(self, mock_crosstab, mock_plt, mock_print):
        """Test barplot_stacked function."""
        # Mock the crosstab and its plot method
        mock_df = MagicMock()
        mock_crosstab.return_value = mock_df

        self.eda.barplot_stacked(self.df, 'predictor', 'target')

        # Check that crosstab was called twice (once for counts, once for normalize)
        self.assertEqual(mock_crosstab.call_count, 2)
        mock_crosstab.assert_any_call(self.df['predictor'], self.df['target'], margins=True)
        mock_crosstab.assert_any_call(self.df['predictor'], self.df['target'], normalize="index")

        # Check that the plot method was called correctly
        mock_df.plot.assert_called_with(kind="bar", stacked=True, figsize=(ANY))
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_barplot_labeled(self, mock_sns, mock_plt):
        """Test barplot_labeled with counts."""
        mock_ax = MagicMock()
        mock_sns.countplot.return_value = mock_ax
        # Mock patches for annotation
        p1 = MagicMock()
        p1.get_height.return_value = 100
        p1.get_x.return_value = 0
        p1.get_width.return_value = 0.8
        mock_ax.patches = [p1]

        self.eda.barplot_labeled(self.df, 'category', percentages=False)

        mock_sns.countplot.assert_called_once()
        mock_ax.annotate.assert_called_once_with(100, (0.4, 100), ha='center', va='center', size=12, xytext=(0, 5), textcoords='offset points')
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_barplot_labeled_with_percentages(self, mock_sns, mock_plt):
        """Test barplot_labeled with percentages."""
        mock_ax = MagicMock()
        mock_sns.countplot.return_value = mock_ax
        p1 = MagicMock()
        p1.get_height.return_value = 3 # 3 out of 5 rows
        p1.get_x.return_value = 0
        p1.get_width.return_value = 0.8
        mock_ax.patches = [p1]

        self.eda.barplot_labeled(self.df, 'category', percentages=True)

        mock_sns.countplot.assert_called_once()
        # 100 * 3 / 5 = 60.0%
        mock_ax.annotate.assert_called_once_with('60.0%', (0.4, 3), ha='center', va='center', size=12, xytext=(0, 5), textcoords='offset points')
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt.subplots')
    @patch('vkpykit.EDA.sns')
    def test_histogram_boxplot(self, mock_sns, mock_subplots):
        """Test histogram_boxplot function."""
        mock_fig, (mock_ax_box, mock_ax_hist) = MagicMock(), (MagicMock(), MagicMock())
        mock_subplots.return_value = (mock_fig, (mock_ax_box, mock_ax_hist))

        self.eda.histogram_boxplot(self.df, 'numeric', kde=True, bins=15)

        mock_subplots.assert_called_once()
        mock_sns.boxplot.assert_called_once_with(data=self.df, x='numeric', ax=mock_ax_box, showmeans=True, color='violet')
        mock_sns.histplot.assert_called_once_with(data=self.df, x='numeric', kde=True, ax=mock_ax_hist, bins=15, palette='winter')
        self.assertEqual(mock_ax_hist.axvline.call_count, 2)

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_histogram_boxplot_all(self, mock_sns, mock_plt):
        """Test histogram_boxplot_all function."""
        self.eda.histogram_boxplot_all(self.df)

        # It should plot for 'target' and 'numeric'
        self.assertEqual(mock_sns.histplot.call_count, 2)
        self.assertEqual(mock_sns.boxplot.call_count, 2)
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_heatmap_all(self, mock_sns, mock_plt):
        """Test heatmap_all function."""
        self.eda.heatmap_all(self.df)

        mock_plt.figure.assert_called_with(figsize=(12, 7))
        # Check that heatmap is called on the correlation matrix of numeric columns
        numeric_cols = self.df.select_dtypes(include=['number'])
        self.assertTrue(mock_sns.heatmap.call_args[0][0].equals(numeric_cols.corr()))
        mock_sns.heatmap.assert_called_once_with(ANY, annot=True, vmin=-1, vmax=1, fmt=".2f", cmap="Spectral")

    @patch('vkpykit.EDA.plt')
    def test_boxplot_outliers(self, mock_plt):
        """Test boxplot_outliers function."""
        self.eda.boxplot_outliers(self.df)

        # Called for 'target' and 'numeric'
        self.assertEqual(mock_plt.boxplot.call_count, 2)
        mock_plt.show.assert_called_once()

    @patch('vkpykit.EDA.plt')
    @patch('vkpykit.EDA.sns')
    def test_distribution_plot_for_target(self, mock_sns, mock_plt):
        """Test distribution_plot_for_target function."""
        self.eda.distribution_plot_for_target(self.df, predictor='numeric', target='target')

        # Two histplots and two boxplots should be created
        self.assertEqual(mock_sns.histplot.call_count, 2)
        self.assertEqual(mock_sns.boxplot.call_count, 2)

        # Check calls for histplot
        mock_sns.histplot.assert_any_call(data=ANY, x='numeric', kde=True, ax=ANY, color='teal', stat='density')
        mock_sns.histplot.assert_any_call(data=ANY, x='numeric', kde=True, ax=ANY, color='orange', stat='density')

        # Check calls for boxplot
        mock_sns.boxplot.assert_any_call(data=self.df, x='target', y='numeric', ax=ANY, palette='gist_rainbow')
        mock_sns.boxplot.assert_any_call(data=self.df, x='target', y='numeric', ax=ANY, showfliers=False, palette='gist_rainbow')

        mock_plt.show.assert_called_once()


class TestEDAPivotTableAll(unittest.TestCase):

    def setUp(self):
        """Set up a sample DataFrame for testing pivot_table_all."""
        self.eda = EDA()
        self.df = pd.DataFrame({
            'category': ['A', 'A', 'B', 'B', 'C', 'C'] * 3,
            'target': [0, 1, 0, 1, 0, 1] * 3,
            'value1': np.random.rand(18) * 100,
            'value2': np.random.rand(18) * 50,
            'non_numeric': ['x', 'y'] * 9
        })

    @patch('VKPyKit.EDA.plt')
    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_pivot_table_all_default_behavior(self, mock_html, mock_display, mock_plt):
        """Test pivot_table_all with default parameters."""
        result = self.eda.pivot_table_all(data=self.df, target='target', printall=True)

        # Should return a dictionary
        self.assertIsInstance(result, dict)
        
        # Should have entries for numeric columns (value1, value2) but not target itself
        self.assertIn('value1', result)
        self.assertIn('value2', result)
        self.assertNotIn('target', result)
        self.assertNotIn('non_numeric', result)
        
        # Each entry should be a DataFrame
        for key in result:
            self.assertIsInstance(result[key], pd.DataFrame)
        
        # Display and HTML should be called for output
        self.assertTrue(mock_display.called)
        self.assertTrue(mock_html.called)

    @patch('VKPyKit.EDA.plt')
    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_pivot_table_all_with_predictors(self, mock_html, mock_display, mock_plt):
        """Test pivot_table_all with specified predictors."""
        predictors = ['value1']
        result = self.eda.pivot_table_all(
            data=self.df, 
            target='target', 
            predictors=predictors, 
            printall=False
        )

        # Should only have value1
        self.assertEqual(len(result), 1)
        self.assertIn('value1', result)
        self.assertNotIn('value2', result)

    @patch('VKPyKit.EDA.plt')
    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_pivot_table_all_custom_stats(self, mock_html, mock_display, mock_plt):
        """Test pivot_table_all with custom statistics."""
        custom_stats = ['mean', 'median']
        result = self.eda.pivot_table_all(
            data=self.df, 
            target='target', 
            stats=custom_stats,
            printall=False
        )

        # Check that pivot tables have the correct statistics
        for key in result:
            # Columns should be the custom stats
            self.assertTrue(all(stat in result[key].columns for stat in custom_stats))

    @patch('VKPyKit.EDA.plt')
    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_pivot_table_all_with_chart_type(self, mock_html, mock_display, mock_plt):
        """Test pivot_table_all with chart generation."""
        mock_plot = MagicMock()
        
        # Call with chart_type
        result = self.eda.pivot_table_all(
            data=self.df, 
            target='target', 
            chart_type='bar',
            printall=True
        )

        # plt.show should be called (for charts and boxplots)
        self.assertTrue(mock_plt.show.called)
        # Should have called display for showing charts
        self.assertTrue(mock_display.called)

    @patch('VKPyKit.EDA.plt')
    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_pivot_table_all_printall_false(self, mock_html, mock_display, mock_plt):
        """Test pivot_table_all with printall=False."""
        result = self.eda.pivot_table_all(
            data=self.df, 
            target='target', 
            printall=False
        )

        # Should still return dictionary
        self.assertIsInstance(result, dict)
        
        # Display should not be called when printall=False
        mock_display.assert_not_called()
        mock_html.assert_not_called()

    @patch('VKPyKit.EDA.plt')
    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_pivot_table_all_return_structure(self, mock_html, mock_display, mock_plt):
        """Test that pivot_table_all returns correct dictionary structure."""
        result = self.eda.pivot_table_all(
            data=self.df, 
            target='target',
            printall=False
        )

        # Verify structure
        for predictor, pivot_df in result.items():
            # Each value should be a DataFrame
            self.assertIsInstance(pivot_df, pd.DataFrame)
            # Index should be target values
            self.assertIsInstance(pivot_df.index, pd.Index)


class TestEDAOverview(unittest.TestCase):

    def setUp(self):
        """Set up sample DataFrames for testing overview."""
        self.eda = EDA()
        self.df = pd.DataFrame({
            'numeric1': [1, 2, 3, 4, 5],
            'numeric2': [10, 20, 30, 40, 50],
            'category': ['A', 'B', 'C', 'D', 'E'],
            'text': ['hello', 'world', 'test', 'data', 'frame']
        })

    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_overview_default_behavior(self, mock_html, mock_display):
        """Test overview with default printall=True."""
        result = self.eda.overview(data=self.df, printall=True)

        # Should return a DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        
        # Should have expected columns
        expected_cols = ['number of rows', 'number of columns', 
                        'number of missing values', 'number of duplicates']
        for col in expected_cols:
            self.assertIn(col, result.columns)
        
        # Check values
        self.assertEqual(result['number of rows'].iloc[0], 5)
        self.assertEqual(result['number of columns'].iloc[0], 4)
        
        # Display and HTML should be called multiple times for different sections
        self.assertTrue(mock_display.called)
        self.assertTrue(mock_html.called)

    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_overview_return_values(self, mock_html, mock_display):
        """Test that overview returns DataFrame with correct information."""
        result = self.eda.overview(data=self.df, printall=False)

        # Verify the returned DataFrame structure
        self.assertEqual(len(result), 1)  # Should have one row
        self.assertEqual(result['number of rows'].iloc[0], self.df.shape[0])
        self.assertEqual(result['number of columns'].iloc[0], self.df.shape[1])
        self.assertEqual(result['number of missing values'].iloc[0], 0)
        self.assertEqual(result['number of duplicates'].iloc[0], 0)

    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_overview_with_missing_values(self, mock_html, mock_display):
        """Test overview on dataset with missing values."""
        df_with_missing = self.df.copy()
        df_with_missing.loc[0, 'numeric1'] = np.nan
        df_with_missing.loc[1, 'category'] = np.nan
        
        result = self.eda.overview(data=df_with_missing, printall=False)

        # Should detect 2 missing values
        self.assertEqual(result['number of missing values'].iloc[0], 2)

    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_overview_with_duplicates(self, mock_html, mock_display):
        """Test overview on dataset with duplicate rows."""
        df_with_duplicates = pd.DataFrame({
            'col1': [1, 2, 3, 1, 2],
            'col2': ['A', 'B', 'C', 'A', 'B']
        })
        
        result = self.eda.overview(data=df_with_duplicates, printall=False)

        # Should detect 2 duplicate rows
        self.assertEqual(result['number of duplicates'].iloc[0], 2)

    @patch('VKPyKit.EDA.display')
    @patch('VKPyKit.EDA.HTML')
    def test_overview_printall_false(self, mock_html, mock_display):
        """Test overview with printall=False doesn't call display."""
        result = self.eda.overview(data=self.df, printall=False)

        # Should return DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        
        # Display should not be called when printall=False
        mock_display.assert_not_called()
        mock_html.assert_not_called()



if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
