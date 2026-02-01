from abc import ABC, abstractmethod
import numpy as np
import random
class VKPy:

    def __init__(self):
        pass

    RANDOM_STATE = 42
    NUMBER_OF_DASHES = 100
    

    def __str__(self):
        return (f"VKPy : RANDOM_STATE = {VKPy.RANDOM_STATE} | DASHES ={VKPy.NUMBER_OF_DASHES}")
    
    @staticmethod
    def setseed(seed: int = 42):
        """ Set seeds for common libraries
        Many machine learning algorithms and data processing steps 
        (like train-test splits or neural network weight initialization) 
        rely on random number generators. If the seed is not set, 
        every run will produce slightly different results, 
        making debugging and comparison difficult

        seed: int = 42
        """
        VKPy.RANDOM_STATE = seed

        random.seed(VKPy.RANDOM_STATE)
        np.random.seed(VKPy.RANDOM_STATE)

        # For TensorFlow/Keras (if available)
        try:
            import tensorflow as tf
            tf.random.set_seed(VKPy.RANDOM_STATE)
        except ImportError:
            pass  # TensorFlow not installed

        # For PyTorch (if available)
        try:
            import torch
            torch.manual_seed(VKPy.RANDOM_STATE)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(VKPy.RANDOM_STATE)
                torch.cuda.manual_seed_all(VKPy.RANDOM_STATE)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        except ImportError:
            pass  # PyTorch not installed
        