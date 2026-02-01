"""
Unit tests for finlearner.utils module.
"""
import pytest
import pandas as pd
import numpy as np
from io import StringIO
from unittest.mock import patch
from finlearner.utils import check_val


class TestCheckVal:
    """Tests for the check_val class."""
    
    def test_init(self):
        """Test check_val initialization."""
        checker = check_val()
        assert checker is not None
    
    def test_check_accuracy_range_valid_input(self, sample_predictions_csv, capsys):
        """Test accuracy check with valid error percentage."""
        checker = check_val()
        checker.check_accuracy_range(sample_predictions_csv, 5)
        
        captured = capsys.readouterr()
        assert "accuracy" in captured.out.lower()
    
    def test_check_accuracy_range_out_of_bounds_low(self, sample_predictions_csv, capsys):
        """Test that negative error range is rejected."""
        checker = check_val()
        checker.check_accuracy_range(sample_predictions_csv, -5)
        
        captured = capsys.readouterr()
        assert "range between 0 and 100" in captured.out
    
    def test_check_accuracy_range_out_of_bounds_high(self, sample_predictions_csv, capsys):
        """Test that error range > 100 is rejected."""
        checker = check_val()
        checker.check_accuracy_range(sample_predictions_csv, 150)
        
        captured = capsys.readouterr()
        assert "range between 0 and 100" in captured.out
    
    def test_check_accuracy_range_zero_percent(self, sample_predictions_csv, capsys):
        """Test 0% error tolerance (exact matches only)."""
        checker = check_val()
        checker.check_accuracy_range(sample_predictions_csv, 0)
        
        captured = capsys.readouterr()
        # With synthetic data, likely 0 exact matches
        assert "accuracy" in captured.out.lower()
    
    def test_check_accuracy_range_hundred_percent(self, sample_predictions_csv, capsys):
        """Test 100% error tolerance (all should match)."""
        checker = check_val()
        checker.check_accuracy_range(sample_predictions_csv, 100)
        
        captured = capsys.readouterr()
        # All predictions should be within 100% error
        assert "accuracy" in captured.out.lower()
    
    def test_check_accuracy_range_calculates_correctly(self, tmp_path, capsys):
        """Test accuracy calculation with known values."""
        # Create data where we know exactly which predictions are within range
        csv_path = tmp_path / "known_predictions.csv"
        data = pd.DataFrame({
            'Close': [100.0, 100.0, 100.0, 100.0],
            'Predicted': [100.0, 105.0, 110.0, 120.0]  # 0%, 5%, 10%, 20% error
        })
        data.to_csv(csv_path, index=False)
        
        checker = check_val()
        
        # With 5% tolerance: first 2 should match (50% accuracy)
        checker.check_accuracy_range(str(csv_path), 5)
        captured = capsys.readouterr()
        assert "0.5" in captured.out  # 50% accuracy
    
    def test_check_accuracy_range_boundary_value(self, tmp_path, capsys):
        """Test boundary value at 100% range."""
        csv_path = tmp_path / "boundary_test.csv"
        data = pd.DataFrame({
            'Close': [100.0],
            'Predicted': [105.0]  # exactly 5% error
        })
        data.to_csv(csv_path, index=False)
        
        checker = check_val()
        
        # At exactly 5% tolerance, should match (<= comparison)
        checker.check_accuracy_range(str(csv_path), 5)
        captured = capsys.readouterr()
        assert "1.0" in captured.out  # 100% accuracy
