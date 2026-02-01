<div align="center">

# 🐍 VKPyKit

**A comprehensive Python toolkit for Machine Learning and Data Science workflows**

[![PyPI Version](https://img.shields.io/pypi/v/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)
[![Python Versions](https://img.shields.io/pypi/pyversions/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)
[![License](https://img.shields.io/pypi/l/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)
[![Status](https://img.shields.io/pypi/status/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)

[![Downloads (Monthly)](https://img.shields.io/pypi/dm/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)
[![Downloads (Weekly)](https://img.shields.io/pypi/dw/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)
[![Downloads (Daily)](https://img.shields.io/pypi/dd/VKPyKit.svg)](https://pypi.python.org/pypi/VKPyKit)

[![GitHub Release](https://img.shields.io/github/release/assignarc/VKPyKit.svg)](https://github.com/assignarc/VKPyKit/releases)
[![GitHub Tag](https://img.shields.io/github/tag/assignarc/VKPyKit.svg)](https://github.com/assignarc/VKPyKit/tags)

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

VKPyKit is a production-ready Python package designed to streamline common Machine Learning and Data Science tasks. Built on top of industry-standard libraries like scikit-learn, pandas, matplotlib, seaborn, TensorFlow, and Keras, it provides convenient wrapper functions and utilities for:

- **VKPy Utilities**: Core utility functions for reproducible ML experiments including seed management
- **Exploratory Data Analysis (EDA)**: Comprehensive visualization and statistical analysis tools
- **Decision Trees (DT)**: Model training, evaluation, and hyperparameter tuning
- **Linear Regression (LR)**: Linear model building and performance assessment
- **Machine Learning Models (MLM)**: General classification model performance evaluation and visualization

Instead of repeatedly writing the same boilerplate code across projects, VKPyKit packages these commonly-used functions into a reusable, well-tested library.

## ✨ Features

### 🛠️ VKPy Utilities

- **Seed Management**: Set random seeds across all major ML libraries (NumPy, TensorFlow, Keras, PyTorch)
- **Reproducibility**: Ensure consistent results across multiple runs of your experiments
- **Multi-Library Support**: Single function call to set seeds for all commonly used ML frameworks
- **CUDA Support**: Automatic configuration for GPU-based PyTorch experiments

### 📊 Exploratory Data Analysis (EDA)

- **Stacked Bar Plots**: Visualize categorical distributions with respect to target variables
- **Labeled Bar Plots**: Bar charts with percentage or count annotations
- **Distribution Analysis**: Combined histogram and boxplot visualizations
- **Outlier Detection**: Automated boxplot generation for outlier identification
- **Correlation Heatmaps**: Visualize feature correlations
- **Pair Plots**: Comprehensive pairwise relationship visualization
- **Target Distribution**: Analyze feature distributions across target classes
- **Pivot Tables**: Generate comprehensive pivot tables with multiple statistics
- **Data Overview**: Quick statistical summary and data quality assessment

### 🌲 Decision Trees (DT)

- **Model Performance Metrics**: Comprehensive classification performance reporting
- **Confusion Matrices**: Visual confusion matrix generation with customization
- **Hyperparameter Tuning**: Automated grid search for optimal decision tree parameters
- **Cross-Validation**: Built-in validation strategies
- **Feature Importance**: Analyze and visualize feature contributions

### 📈 Linear Regression (LR)

- **Model Building**: Streamlined linear regression model creation
- **Performance Evaluation**: R², RMSE, MAE, and other regression metrics
- **Residual Analysis**: Automated residual plotting and diagnostics
- **Model Comparison**: Compare multiple regression models

### 🤖 Machine Learning Models (MLM)

- **Model Performance Metrics**: Comprehensive classification performance reporting for any sklearn classifier
- **Confusion Matrices**: Visual confusion matrix generation with percentages
- **Model Evaluation**: Accuracy, Precision, Recall, and F1-Score metrics
- **Universal Compatibility**: Works with any scikit-learn classification model

## 🚀 Installation

### Using pip (Recommended)

```bash
pip install VKPyKit
```

### From Source

```bash
git clone https://github.com/assignarc/VKPyKit.git
cd VKPyKit
pip install -e .
```

### Requirements

- Python >= 3.9
- Dependencies: `numpy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl`, `plotly`, `tensorflow`, `keras`

All dependencies will be automatically installed with the package.

## 🎯 Quick Start

```python
from VKPyKit.VKPy import *
from VKPyKit.EDA import *
from VKPyKit.DT import *
from VKPyKit.LR import *
from VKPyKit.MLM import *

# Set seeds for reproducibility across all ML libraries
VKPy.setseed(42)

# Quick EDA visualization
EDA.histogram_boxplot_all(
    data=df,
    figsize=(15, 10),
    bins=10,
    kde=True
)

# Train and evaluate a Decision Tree
DT.model_performance_classification(
    model=my_dt_classifier,
    X=X_test,
    y=y_test,
    printall=True,
    title='Customer Churn Model'
)

# Evaluate any classification model
MLM.model_performance_classification(
    model=my_classifier,
    predictors=X_test,
    expected=y_test,
    printall=True,
    title='My Classification Model'
)

# Build a Linear Regression model
LR.linear_regression_model(
    data=df,
    predictors=['feature1', 'feature2', 'feature3'],
    target='target_variable',
    printall=True,
    title='Sales Prediction Model'
)
```

## 📚 Documentation

### VKPy Utilities

#### Seed Management for Reproducibility

Ensure consistent results across multiple runs of your ML experiments by setting random seeds for all major libraries:

```python
from VKPyKit.VKPy import *

# Set seed for reproducibility across NumPy, TensorFlow, Keras, and PyTorch
VKPy.setseed(42)

# Now all random operations will be reproducible
# This affects:
# - NumPy random operations
# - TensorFlow/Keras model initialization and training
# - PyTorch model initialization and training (including CUDA operations)
# - Python's built-in random module
```

**Benefits:**

- ✅ Reproducible experiments across different runs
- ✅ Consistent model initialization weights
- ✅ Reliable train-test splits
- ✅ Easier debugging and model comparison
- ✅ GPU operations (CUDA) are also deterministic

### Exploratory Data Analysis (EDA)

#### Histogram with Boxplot

Visualize the distribution of all numerical features in your dataset:

```python
from VKPyKit.EDA import *
import pandas as pd

# Load your data
df = pd.read_csv('your_data.csv')

# Generate histogram and boxplot for all numerical columns
EDA.histogram_boxplot_all(
    data=df,
    figsize=(15, 10),
    bins=10,
    kde=True
)
```

#### Stacked Bar Plots

Visualize categorical variable distributions against a target:

```python
# Single stacked bar plot
EDA.barplot_stacked(
    data=df,
    predictor='category_column',
    target='target_column'
)

# Multiple stacked bar plots
EDA.barplot_stacked_all(
    data=df,
    predictors=['cat_col1', 'cat_col2', 'cat_col3'],
    target='target_column'
)
```

#### Distribution Analysis for Target Variable

```python
# Analyze how a feature distributes across target classes
EDA.distribution_plot_for_target(
    data=df,
    predictor='numerical_feature',
    target='target_column',
    figsize=(12, 10)
)

# Analyze multiple features
EDA.distribution_plot_for_target_all(
    data=df,
    predictors=['feature1', 'feature2', 'feature3'],
    target='target_column',
    figsize=(12, 10)
)
```

#### Correlation Analysis

```python
# Generate correlation heatmap
EDA.heatmap_all(
    data=df,
    features=['feature1', 'feature2', 'feature3']  # Optional: specify features
)

# Generate pairplot for feature relationships
EDA.pairplot_all(
    data=df,
    features=['feature1', 'feature2', 'feature3'],
    hues=['target_column'],
    min_unique_values_for_pairplot=4,
    diagonal_plot_kind='auto'
)
```

#### Outlier Detection

```python
# Visualize outliers across all numerical features
EDA.boxplot_outliers(data=df)
```

#### Pivot Tables and Statistical Analysis

```python
# Generate comprehensive pivot tables with multiple statistics
EDA.pivot_table_all(
    data=df,
    predictors=['category1', 'category2'],
    target='numerical_target',
    stats=['mean', 'median', 'count', 'std'],
    figsize=(12, 10),
    chart_type='bar',  # 'bar', 'line', or None
    printall=True
)
```

#### Quick Data Overview

```python
# Get a comprehensive statistical summary and data quality check
EDA.overview(
    data=df,
    printall=True
)
# Displays: shape, data types, missing values, duplicates, and basic statistics
```

### Decision Trees (DT)

#### Model Performance Evaluation

```python
from VKPyKit.DT import *
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

# Prepare your data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train a model
model = DecisionTreeClassifier(random_state=42)
model.fit(X_train, y_train)

# Evaluate performance
DT.model_performance_classification(
    model=model,
    X=X_test,
    y=y_test,
    printall=True,
    title='Decision Tree Classifier Performance'
)
```

#### Confusion Matrix Visualization

```python
# Plot confusion matrix
DT.plot_confusion_matrix(
    model=model,
    X=X_test,
    y=y_test,
    title='Confusion Matrix - Decision Tree'
)
```

#### Hyperparameter Tuning

```python
# Automated hyperparameter tuning with grid search
best_params, results_df = DT.tune_decision_tree(
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
    max_depth_v=(2, 11, 2),           # (start, end, step)
    max_leaf_nodes_v=(10, 51, 10),
    min_samples_split_v=(10, 51, 10),
    printall=True,
    sortresultby=['F1Difference'],
    sortbyAscending=False
)

print(f"Best parameters: {best_params}")
```

### Linear Regression (LR)

#### Build and Evaluate a Linear Regression Model

```python
from VKPyKit.LR import *

# Train and evaluate linear regression
LR.linear_regression_model(
    data=df,
    predictors=['feature1', 'feature2', 'feature3'],
    target='target_variable',
    printall=True,
    title='House Price Prediction Model'
)
```

### Machine Learning Models (MLM)

#### Evaluate Any Classification Model

The MLM module works with any scikit-learn classifier (Random Forest, SVM, Logistic Regression, etc.):

```python
from VKPyKit.MLM import *
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Prepare your data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train any classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate performance with comprehensive metrics
MLM.model_performance_classification(
    model=model,
    predictors=X_test,
    expected=y_test,
    printall=True,
    title='Random Forest Classifier'
)
```

#### Confusion Matrix for Any Classifier

```python
# Plot confusion matrix with percentages
MLM.plot_confusion_matrix(
    model=model,
    predictors=X_test,
    expected=y_test,
    title='Random Forest - Confusion Matrix'
)
```

## 🛠️ API Reference

### VKPy Class

| Method          | Description                                                   |
| --------------- | ------------------------------------------------------------- |
| `setseed(seed)` | Set random seeds across NumPy, TensorFlow, Keras, and PyTorch |

### EDA Class

| Method                               | Description                                               |
| ------------------------------------ | --------------------------------------------------------- |
| `histogram_boxplot_all()`            | Combined histogram and boxplot for all numerical features |
| `barplot_stacked()`                  | Stacked bar chart for categorical variables               |
| `barplot_stacked_all()`              | Multiple stacked bar charts                               |
| `barplot_labeled()`                  | Bar plot with count/percentage labels                     |
| `distribution_plot_for_target()`     | Distribution analysis across target classes               |
| `distribution_plot_for_target_all()` | Multiple distribution analyses                            |
| `boxplot_outliers()`                 | Outlier detection using boxplots                          |
| `boxplot_dependent_category()`       | Boxplot for dependent variables against categories        |
| `heatmap_all()`                      | Correlation heatmap                                       |
| `pairplot_all()`                     | Pairwise feature relationship plots                       |
| `pivot_table_all()`                  | Generate pivot tables with multiple statistics            |
| `overview()`                         | Quick statistical summary and data quality check          |

### DT Class

| Method                               | Description                       |
| ------------------------------------ | --------------------------------- |
| `model_performance_classification()` | Comprehensive performance metrics |
| `plot_confusion_matrix()`            | Visualize confusion matrix        |
| `tune_decision_tree()`               | Automated hyperparameter tuning   |

### LR Class

| Method                      | Description                                 |
| --------------------------- | ------------------------------------------- |
| `linear_regression_model()` | Build and evaluate linear regression models |

### MLM Class

| Method                               | Description                                          |
| ------------------------------------ | ---------------------------------------------------- |
| `model_performance_classification()` | Comprehensive performance metrics for any classifier |
| `plot_confusion_matrix()`            | Visualize confusion matrix with percentages          |

## 🧪 Testing

VKPyKit includes a comprehensive test suite to ensure code quality and reliability. The test suite covers all major modules:

- **EDA Module Tests** (`tests/test_EDA.py`): Tests for all exploratory data analysis functions
- **DT Module Tests** (`tests/test_DT.py`): Tests for decision tree utilities
- **LR Module Tests** (`tests/test_LR.py`): Tests for linear regression functions
- **MLM Module Tests** (`tests/test_MLM.py`): Tests for machine learning model evaluation

### Running Tests

```bash
# Install test dependencies
pip install VKPyKit[test]

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=VKPyKit
```

The test suite uses synthetic data generated via `conftest.py` to ensure reproducible and reliable testing.

## 🤝 Contributing

Contributions are welcome! If you have additional utility functions or improvements, please contribute to the project.

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Reporting Issues

Found a bug or have a feature request? Please open an issue on [GitHub Issues](https://github.com/assignarc/VKPyKit/issues).

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Vishal Khapre**

- GitHub: [@assignarc](https://github.com/assignarc)
- PyPI: [VKPyKit](https://pypi.org/project/VKPyKit/)

## 🌟 Acknowledgments

Built with:

- [NumPy](https://numpy.org/)
- [Pandas](https://pandas.pydata.org/)
- [Scikit-learn](https://scikit-learn.org/)
- [Matplotlib](https://matplotlib.org/)
- [Seaborn](https://seaborn.pydata.org/)
- [Plotly](https://plotly.com/)

---

<div align="center">

**[⬆ Back to Top](#-vkpykit)**

Made with ❤️ by [Vishal Khapre](https://github.com/assignarc)

If you find VKPyKit useful, please consider giving it a ⭐ on [GitHub](https://github.com/assignarc/VKPyKit)!

</div>
