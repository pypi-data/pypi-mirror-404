import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import sys

from sklearn import tree, metrics
from sklearn.tree import DecisionTreeClassifier
from IPython.display import display, HTML
from sklearn.metrics import classification_report, confusion_matrix

import tensorflow as tf
import warnings
warnings.filterwarnings("ignore")
# Time related functions.
import time


class MLM():
    
    def __init__(self): 
        super().__init__()
        pass
    

    RANDOM_STATE = 42
    NUMBER_OF_DASHES = 100

    """
    Model Metrics related visualizations
    To plot the confusion_matrix with percentages
    """

    @staticmethod
    def plot_feature_importance(model,
                                features: list,
                                figsize: tuple[float, float] = (10, 6),
                                numberoftopfeatures: int = None,
                                title: str = '',
                                ignoreZeroImportance: bool = False,
                                ) -> None:
        """
        Plot feature importance for a given model and feature names

        model: trained model with feature_importances_ attribute \n
        feature_names: list of feature names    \n
        figsize: size of the figure (default (10,6)) \n
        numberoftopfeatures: number of top features to display (default None, i.e., display all features) \n
        return: None
        """

        df_importance = pd.DataFrame({
            'Feature': features,
            'Importance': model.feature_importances_
        }).sort_values(by='Importance', ascending=False)

        if numberoftopfeatures:
            df_importance.head(numberoftopfeatures, inplace=True)

        if ignoreZeroImportance:
            df_importance = df_importance[df_importance['Importance'] > 0]

        display(df_importance)

        plt.figure(figsize=figsize)
        sns.barplot(x='Importance',
                    y='Feature',
                    data=df_importance,
                    palette='viridis')
        plt.title('Feature and their Importance Scores : ' + title)
        plt.xlabel('Importance Score')
        plt.ylabel('Features')
        plt.show()
        sys.stdout.flush()

        # END OF PLOT FEATURE IMPORTANCE FUNCTION

# defining a function to compute different metrics to check performance of a classification model built using sklearn
    @staticmethod
    def model_performance_classification(
            model,
            predictors: pd.DataFrame,
            expected: pd.Series,
            threshold: float = 0.0,
            score_average: str = 'binary',
            printall: bool = False,
            title: str = 'DecisionTreeClassifier') -> pd.DataFrame:
        """
        Function to compute different metrics to check classification model performance
        model: classifier \n
        predictors: independent variables \n
        target: dependent variable \n
        return: dataframe of different performance metrics
        """

        # predicting using the independent variables
        predictions = model.predict(predictors) > threshold

        accuracy = metrics.accuracy_score(expected, predictions)  # to compute Accuracy
        recall = metrics.recall_score(expected, predictions, average=score_average)  # to compute Recall
        precision = metrics.precision_score(expected, predictions, average=score_average)  # to compute Precision
        f1 = metrics.f1_score(expected, predictions, average=score_average)  # to compute F1-score

        # creating a dataframe of metrics
        df_perf = pd.DataFrame(
            {
                "Accuracy": accuracy,
                "Recall": recall,
                "Precision": precision,
                "F1": f1,
            },
            index=[0],
        )
        if (printall):
            display(
                HTML(
                    f"<h3>Classification Model Performance Metrics : {title}</h3>"
                ))
            display(df_perf)

        return df_perf

        # END OF MODEL PERFORMANCE CLASSIFICATION FUNCTION


    @staticmethod
    def plot_confusion_matrix(
                              model,
                              predictors: pd.DataFrame,
                              expected: pd.Series,
                              title: str = "DecisionTreeClassifier") -> None:
        """
        To plot the confusion_matrix with percentages \n
        model: classifier \n
        predictors: independent variables  \n
        target: dependent variable \n
        return: None
        """
        # Predict the target values using the provided model and predictors
        predicted = model.predict(predictors)

        # Compute the confusion matrix comparing the true target values with the predicted values
        conf_matrix = metrics.confusion_matrix(expected, predicted)

        # Create labels for each cell in the confusion matrix with both count and percentage
        labels = np.asarray([[
            "{0:0.0f}".format(item) +
            "\n{0:.2%}".format(item / conf_matrix.flatten().sum())
        ] for item in conf_matrix.flatten()
                             ]).reshape(2, 2)  # reshaping to a matrix

        # Set the figure size for the plot
        plt.figure(figsize=(6, 4))
        plt.title("Confusion Matrix for " + title)
        # Plot the confusion matrix as a heatmap with the labels
        sns.heatmap(conf_matrix, annot=labels, fmt="")

        # Add a label to the y-axis
        plt.ylabel("True label")

        # Add a label to the x-axis
        plt.xlabel("Predicted label")
        plt.show()
        sys.stdout.flush()
        # END OF PLOT CONFUSION MATRIX FUNCTION

    @staticmethod
    def model_history_plot(history: tf.keras.callbacks.History,
                           plot_metric: str = None,
                           title: str = "Model History") -> None:
        """
        Function to plot loss/accuracy

        history: an object which stores the metrics and losses.
        metric: can be one of Loss or Accuracy
        """
        

        if plot_metric is not None:
            metrics = [plot_metric]
        else:
            metrics = filtered_list = list(filter(lambda item: not item.startswith('val_'), history.history.keys()))
 
        for metric in metrics:
            # Print maximum values for each metric
            train_max = max(history.history[metric])
            val_max = max(history.history['val_'+metric])
            print(f"\n{metric.capitalize()} - Max Values:")
            print(f"  Train: {train_max:.4f}")
            print(f"  Validation: {val_max:.4f}")
            
            fig, ax = plt.subplots() #Creating a subplot with figure and axes.
            plt.plot(history.history[metric]) #Plotting the train accuracy or train loss
            plt.plot(history.history['val_'+metric]) #Plotting the validation accuracy or validation loss

            plt.title(title + ' - ' + metric.capitalize()) #Defining the title of the plot.
            plt.ylabel(metric.capitalize()) #Capitalizing the first letter.
            plt.xlabel('Epoch') #Defining the label for the x-axis.
            fig.legend(['Train', 'Validation'], loc="outside right upper") #Defining the legend, loc controls the position of the legend.

        plt.tight_layout()
        plt.show()
        sys.stdout.flush()
        
        # END OF MODEL HISTORY PLOT FUNCTION

    """
    Compiles, trains, and evaluates a Keras model using specified hyper-parameters and datasets, 
    then reports performance metrics.
    """
    @staticmethod
    def execute_model(model_in: tf.keras.Model, 
                    optimizer: tf.keras.optimizers.Optimizer, 
                    model_name: str, 
                    data: dict, 
                    class_weights: dict, 
                    loss_type: str, 
                    optmization_metrics: list, 
                    threshold: float, 
                    target_names: list, 
                    epochs: int, 
                    batch_size: int, 
                    verbose: int = 1,
                    print_model_summary: bool = True,
                    activation: str = 'relu') -> pd.DataFrame:
        
        # clears the current Keras session, resetting all layers and models previously created, 
        # freeing up memory and resources.

        tf.keras.backend.clear_session()
    
        if print_model_summary:
            display(model_in.summary())

        model_in.compile(loss=loss_type, optimizer=optimizer, metrics = optmization_metrics)

        model_start = time.time()
        model_in_history = model_in.fit(data["X_train"], data["y_train"], validation_data=(data["X_val"],data["y_val"]) , batch_size=batch_size, epochs=epochs,class_weight=class_weights,verbose=verbose)
        model_end=time.time()

        model_T_performance = MLM.model_performance_classification(model=model_in, predictors=data["X_train"], expected=data["y_train"], threshold=threshold, score_average='macro', title=f"{model_name} Training Data")
        model_V_performance = MLM.model_performance_classification(model=model_in, predictors=data["X_val"], expected=data["y_val"],threshold=threshold, score_average='macro',title=f"{model_name} Validation Data")

        MLM.model_history_plot(model_in_history, title = f"{model_name} History")

        #Check the predictions. 
        model_y_train_pred = model_in.predict(data["X_train"])
        model_y_val_pred = model_in.predict(data["X_val"])

        if print_model_summary:

            #Collect Classification Reports - Train
            model_in_cr_train = classification_report(data["y_train"],model_y_train_pred>threshold,output_dict=True, digits=4, target_names=target_names)
            # Convert to DataFrame
            report_df = pd.DataFrame(model_in_cr_train).transpose()
            # Apply a background gradient to highlight performance
            report_df.style.background_gradient(cmap='viridis')
            display("Classification report - Training set", report_df)
            # Visualize using Seaborn
            plt.figure(figsize=(3, 2))
            sns.heatmap(pd.DataFrame(data=model_in_cr_train).T.iloc[:-3, :-1], annot=True, cmap="Blues", fmt=".4f")
            plt.title(f"{model_name} - CR Heatmap - Train")
            plt.show()
            
            # Visualize using Seaborn - Validation
            model_in_cr_val = classification_report(data["y_val"],model_y_val_pred>threshold,output_dict=True, digits=4, target_names=target_names)
            # Convert to DataFrame
            report_df = pd.DataFrame(model_in_cr_val).transpose()
            # Apply a background gradient to highlight performance
            report_df.style.background_gradient(cmap='viridis')
            display("Classification report - Validation set", report_df)
            # Visualize using Seaborn
            plt.figure(figsize=(3, 2))
            sns.heatmap(pd.DataFrame(data=model_in_cr_val).T.iloc[:-3, :-1], annot=True, cmap="Blues", fmt=".4f")
            plt.title(f"{model_name} CR Heatmap - Val")
            plt.show()



        _results = pd.DataFrame(data={
                                'ModelName':model_name,
                                'Layers' : len(model_in.layers),
                                'Epochs':epochs,
                                'BatchSize':batch_size,
                                'Activation':activation,
                                'ClassWeights' : False if (class_weights is None) else True,
                                'Optimizer':optimizer.__class__.__name__,
                                'Loss':loss_type.__class__.__name__,
                                'Metrics':optmization_metrics,
                                'TotalParameters': model_in.count_params(),
                                'Model':model_in,
                                'History':model_in_history,
                                'Time':model_end-model_start,

                                'Train_Accuracy':model_T_performance['Accuracy'].abs(),
                                'Train_Recall':model_T_performance['Recall'].abs(),
                                'Train_Precision':model_T_performance['Precision'].abs(),
                                'Train_F1Score':model_T_performance['F1'].abs(),

                                'Validation_Accuracy':model_V_performance['Accuracy'].abs(),
                                'Validation_Recall':model_V_performance['Recall'].abs(),
                                'Validation_Precision':model_V_performance['Precision'].abs(),
                                'Validation_F1Score':model_V_performance['F1'].abs(),

                                'Validation_Weighted_Recall':model_in_cr_val['weighted avg']['recall'],
                                'Validation_Weighted_Precision':model_in_cr_val['weighted avg']['precision'],
                                'Validation_Weighted_F1Score':model_in_cr_val['weighted avg']['f1-score'],

                                'Validation_Macro_Recall':model_in_cr_val['macro avg']['recall'],
                                'Validation_Macro_Precision':model_in_cr_val['macro avg']['precision'],
                                'Validation_Macro_F1Score':model_in_cr_val['macro avg']['f1-score']
                            })
            
        if print_model_summary:
            display(f"{model_name} Execution Results",_results)

        return _results