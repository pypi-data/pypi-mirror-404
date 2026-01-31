"""
Visualization module for DConfusion.

This module contains all plotting and visualization methods for confusion matrices.
"""

from typing import Optional
from matplotlib import figure


class VisualizationMixin:
    """Mixin class providing visualization methods for confusion matrices."""

    def plot(self, normalize: bool = False, cmap: str = 'Blues',
             figsize: tuple = (8, 6), annot: bool = True, fmt: str = 'd',
             title: Optional[str] = None, save_path: Optional[str] = None,
             show_metrics: bool = False, **kwargs) -> figure.Figure:
        """
        Create a matplotlib heatmap visualization of the confusion matrix.

        Args:
            normalize: If True, show percentages instead of counts
            cmap: Matplotlib colormap name (e.g., 'Blues', 'viridis', 'plasma')
            figsize: Figure size as (width, height) tuple
            annot: Whether to annotate cells with values
            fmt: String formatting code for annotations ('d' for integers, '.2f' for floats)
            title: Custom title for the plot
            save_path: Path to save the figure (e.g., 'confusion_matrix.png')
            show_metrics: Whether to display key metrics alongside the matrix
            **kwargs: Additional arguments passed to matplotlib's imshow

        Returns:
            matplotlib Figure object

        Raises:
            ImportError: If matplotlib is not installed
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib as mpl
        except ImportError:
            raise ImportError(
                "matplotlib is required for plotting. Install with: pip install matplotlib"
            )

        # Prepare data
        if normalize:
            if self.total == 0:
                raise ValueError("Cannot normalize empty confusion matrix")
            plot_matrix = self.matrix.astype(float) / self.total * 100
            fmt = '.2f' if fmt == 'd' else fmt
            value_label = "Percentage (%)"
            if cmap == 'Blues' and 'cmap' not in kwargs:
                cmap = 'Blues'  # Keep Blues but we'll adjust vmax

        else:
            plot_matrix = self.matrix
            value_label = "Count"

        # Create figure
        if show_metrics and self.n_classes == 2:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(figsize[0]*1.5, figsize[1]))
        else:
            fig, ax1 = plt.subplots(figsize=figsize)
            ax2 = None

        # Adjust color scaling for better readability
        plot_kwargs = kwargs.copy()
        if normalize:
            # For normalized plots, set a reasonable vmax to avoid overly bright colors
            if 'vmax' not in plot_kwargs and 'vmin' not in plot_kwargs:
                plot_kwargs['vmax'] = min(100, plot_matrix.max() * 1.1)
                plot_kwargs['vmin'] = 0

        # Create heatmap
        im = ax1.imshow(plot_matrix, interpolation='nearest', cmap=cmap, **plot_kwargs)

        # Add colorbar
        cbar = ax1.figure.colorbar(im, ax=ax1)
        cbar.ax.set_ylabel(value_label, rotation=-90, va="bottom")

        # Set ticks and labels
        ax1.set_xticks(range(self.n_classes))
        ax1.set_yticks(range(self.n_classes))
        ax1.set_xticklabels(self.labels)
        ax1.set_yticklabels(self.labels)

        # Rotate tick labels for better readability
        plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Add text annotations
        if annot:
            thresh = plot_matrix.max() / 2.
            for i in range(self.n_classes):
                for j in range(self.n_classes):
                    color = "white" if plot_matrix[i, j] > thresh else "black"
                    text = format(plot_matrix[i, j], fmt)
                    ax1.text(j, i, text, ha="center", va="center", color=color, fontweight='bold')

        # Labels and title
        ax1.set_ylabel('True Label')
        ax1.set_xlabel('Predicted Label')

        if title is None:
            if normalize:
                title = 'Confusion Matrix (Normalized)'
            else:
                title = 'Confusion Matrix'
        ax1.set_title(title)

        # Add metrics panel for binary classification
        if show_metrics and self.n_classes == 2:
            try:
                metrics = self.get_all_metrics()
                ax2.axis('off')

                metrics_text = "Key Metrics:\n\n"
                key_metrics = ['accuracy', 'precision', 'recall', 'specificity', 'f1_score']

                for metric in key_metrics:
                    if metric in metrics and not isinstance(metrics[metric], str):
                        value = metrics[metric]
                        metrics_text += f"{metric.replace('_', ' ').title()}: {value:.3f}\n"

                ax2.text(0.1, 0.9, metrics_text, transform=ax2.transAxes,
                        fontsize=12, verticalalignment='top', fontfamily='monospace',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))

            except Exception as e:
                # If metrics calculation fails, just hide the metrics panel
                ax2.axis('off')

        plt.tight_layout()

        # Save if requested
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_normalized(self, cmap='viridis', **kwargs):
        """
        Convenience method to plot normalized confusion matrix.

        Args:
            cmap: Matplotlib colormap name (e.g., 'Blues', 'viridis', 'plasma')
            **kwargs: Arguments passed to plot() method

        Returns:
            matplotlib Figure object
        """
        defaults = {
            'cmap': cmap,
            'normalize': True
        }
        defaults.update(kwargs)
        return self.plot(**defaults)

    def plot_with_metrics(self, **kwargs):
        """
        Convenience method to plot confusion matrix with metrics panel (binary only).

        Args:
            **kwargs: Arguments passed to plot() method

        Returns:
            matplotlib Figure object
        """
        return self.plot(show_metrics=True, **kwargs)
