"""
Input/Output module for DConfusion.

This module contains methods for importing and exporting confusion matrices
in various formats (CSV, dict, from predictions, etc.).
"""

from typing import List, Any, Optional, Dict, Union
import numpy as np


class IOMixin:
    """Mixin class providing I/O methods for confusion matrices."""

    @classmethod
    def from_predictions(cls, y_true: List[Any], y_pred: List[Any],
                         labels: Optional[List[Any]] = None) -> 'DConfusion':
        """
        Create DConfusion object from actual and predicted labels.

        Args:
            y_true: List of actual labels
            y_pred: List of predicted labels
            labels: List of all possible labels (for multi-class)

        Returns:
            DConfusion: New DConfusion object
        """
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have the same length")

        # Determine unique labels
        if labels is None:
            unique_labels = sorted(list(set(y_true + y_pred)))
        else:
            unique_labels = list(labels)

        n_classes = len(unique_labels)

        # Create label to index mapping
        label_to_idx = {label: i for i, label in enumerate(unique_labels)}

        # Initialize confusion matrix
        matrix = np.zeros((n_classes, n_classes), dtype=int)

        # Fill confusion matrix
        for true_label, pred_label in zip(y_true, y_pred):
            true_idx = label_to_idx[true_label]
            pred_idx = label_to_idx[pred_label]
            matrix[true_idx, pred_idx] += 1

        return cls(confusion_matrix=matrix, labels=unique_labels)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export confusion matrix to dictionary format.

        Returns:
            Dict: Serializable dictionary representation
        """
        return {
            'matrix': self.matrix.tolist(),
            'labels': self.labels,
            'n_classes': self.n_classes,
            'total': self.total,
            'is_binary': self.is_binary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DConfusion':
        """
        Create DConfusion object from dictionary.

        Args:
            data: Dictionary created by to_dict()

        Returns:
            DConfusion: New DConfusion object
        """
        return cls(confusion_matrix=data['matrix'], labels=data['labels'])

    def to_csv(self, filepath: str, include_labels: bool = True) -> None:
        """
        Export confusion matrix to CSV file.

        Args:
            filepath: Path to save CSV file
            include_labels: Whether to include row/column labels
        """
        import csv

        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            if include_labels:
                # Header row
                header = [''] + [str(label) for label in self.labels]
                writer.writerow(header)

                # Data rows with labels
                for i, label in enumerate(self.labels):
                    row = [str(label)] + [str(val) for val in self.matrix[i]]
                    writer.writerow(row)
            else:
                # Just the matrix data
                for row in self.matrix:
                    writer.writerow([str(val) for val in row])

    @classmethod
    def from_csv(cls, filepath: str, has_labels: bool = True) -> 'DConfusion':
        """
        Create DConfusion object from CSV file.

        Args:
            filepath: Path to CSV file
            has_labels: Whether CSV includes row/column labels

        Returns:
            DConfusion: New DConfusion object
        """
        import csv

        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            if has_labels:
                labels = rows[0][1:]  # Skip first cell
                # Try to convert labels to int if possible
                try:
                    labels = [int(label) for label in labels]
                except (ValueError, TypeError):
                    pass  # Keep as strings if conversion fails
                matrix_data = []
                for row in rows[1:]:
                    matrix_data.append([int(val) for val in row[1:]])
                return cls(confusion_matrix=matrix_data, labels=labels)
            else:
                matrix_data = [[int(val) for val in row] for row in rows]
                return cls(confusion_matrix=matrix_data)
