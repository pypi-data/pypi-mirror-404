"""
Unit tests for the VKPy utility module of VKPyKit.

This module tests the VKPy class functionality including:
- Seed management across multiple libraries
- RANDOM_STATE configuration
- Reproducibility validation
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import random

from VKPyKit.VKPy import VKPy


class TestVKPy(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Reset to default seed before each test
        VKPy.RANDOM_STATE = 42

    def test_setseed_updates_random_state(self):
        """Test that setseed updates the VKPy.RANDOM_STATE class variable."""
        custom_seed = 123
        VKPy.setseed(custom_seed)
        
        self.assertEqual(VKPy.RANDOM_STATE, custom_seed)

    def test_setseed_default_value(self):
        """Test that setseed uses default value of 42 when no argument provided."""
        VKPy.RANDOM_STATE = 999  # Change from default
        VKPy.setseed()  # Call without arguments
        
        self.assertEqual(VKPy.RANDOM_STATE, 42)

    def test_setseed_affects_numpy_reproducibility(self):
        """Test that setseed makes NumPy random operations reproducible."""
        # Set seed and generate random numbers
        VKPy.setseed(42)
        numpy_result_1 = np.random.rand(5)
        
        # Reset seed and generate again
        VKPy.setseed(42)
        numpy_result_2 = np.random.rand(5)
        
        # Results should be identical
        np.testing.assert_array_equal(numpy_result_1, numpy_result_2)

    def test_setseed_affects_python_random_reproducibility(self):
        """Test that setseed makes Python's random module reproducible."""
        # Set seed and generate random numbers
        VKPy.setseed(42)
        python_result_1 = [random.random() for _ in range(5)]
        
        # Reset seed and generate again
        VKPy.setseed(42)
        python_result_2 = [random.random() for _ in range(5)]
        
        # Results should be identical
        self.assertEqual(python_result_1, python_result_2)

    def test_setseed_with_different_seeds(self):
        """Test that different seeds produce different random sequences."""
        VKPy.setseed(42)
        result_seed_42 = np.random.rand(5)
        
        VKPy.setseed(123)
        result_seed_123 = np.random.rand(5)
        
        # Results should be different
        with self.assertRaises(AssertionError):
            np.testing.assert_array_equal(result_seed_42, result_seed_123)

    def test_setseed_with_tensorflow_available(self):
        """Test that setseed sets TensorFlow seed when TensorFlow is available."""
        # Mock tensorflow module
        with patch('builtins.__import__') as mock_import:
            mock_tf = MagicMock()
            
            def import_side_effect(name, *args, **kwargs):
                if name == 'tensorflow':
                    return mock_tf
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            custom_seed = 42
            VKPy.setseed(custom_seed)
            
            # Verify TensorFlow seed was set
            mock_tf.random.set_seed.assert_called_once_with(custom_seed)

    def test_setseed_with_pytorch_available(self):
        """Test that setseed sets PyTorch seed when PyTorch is available."""
        # Mock torch module
        with patch('builtins.__import__') as mock_import:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            
            def import_side_effect(name, *args, **kwargs):
                if name == 'torch':
                    return mock_torch
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            custom_seed = 42
            VKPy.setseed(custom_seed)
            
            # Verify PyTorch seed was set
            mock_torch.manual_seed.assert_called_once_with(custom_seed)

    def test_setseed_handles_tensorflow_import_error(self):
        """Test that setseed gracefully handles TensorFlow not being installed."""
        # This should not raise an exception even if tensorflow is not available
        try:
            VKPy.setseed(42)
            # If we get here, the function handled missing tensorflow gracefully
            self.assertTrue(True)
        except ImportError:
            self.fail("setseed should not raise ImportError for missing TensorFlow")

    def test_setseed_handles_pytorch_import_error(self):
        """Test that setseed gracefully handles PyTorch not being installed."""
        # This should not raise an exception even if torch is not available
        try:
            VKPy.setseed(42)
            # If we get here, the function handled missing pytorch gracefully
            self.assertTrue(True)
        except ImportError:
            self.fail("setseed should not raise ImportError for missing PyTorch")

    def test_vkpy_str_representation(self):
        """Test the string representation of VKPy class."""
        vkpy_instance = VKPy()
        vkpy_str = str(vkpy_instance)
        
        # Should contain RANDOM_STATE and NUMBER_OF_DASHES
        self.assertIn("RANDOM_STATE", vkpy_str)
        self.assertIn("DASHES", vkpy_str)
        self.assertIn(str(VKPy.RANDOM_STATE), vkpy_str)
        self.assertIn(str(VKPy.NUMBER_OF_DASHES), vkpy_str)

    def test_vkpy_constants(self):
        """Test that VKPy class has the expected constants."""
        self.assertTrue(hasattr(VKPy, 'RANDOM_STATE'))
        self.assertTrue(hasattr(VKPy, 'NUMBER_OF_DASHES'))
        self.assertEqual(VKPy.NUMBER_OF_DASHES, 100)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
