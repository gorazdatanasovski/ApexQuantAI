import os
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class DimensionalProjectionEngine:
    """
    Renders high-dimensional mathematical data and stochastic trajectories into visual space.
    """
    def __init__(self, output_dir="projections"):
        self.output_path = Path(os.getcwd()) / output_dir
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Enforce sterile, quantitative aesthetic
        sns.set_theme(style="whitegrid", context="paper")
        plt.rcParams.update({
            "font.family": "serif",
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "lines.linewidth": 1.5
        })

    def export_stochastic_path(self, data_vector: list, title: str, filename: str):
        print(f"[+] VISUALIZATION MATRIX: Projecting {title} into 2D space...")
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(data_vector, color="black")
            ax.set_title(title)
            ax.set_ylabel("Amplitude")
            ax.set_xlabel("Discrete Time Steps")
            
            save_target = self.output_path / f"{filename}.png"
            plt.savefig(save_target, dpi=300, bbox_inches="tight")
            plt.close(fig)
            return f"[+] PROJECTION SUCCESS: Matrix saved to {save_target}"
        except Exception as e:
            return f"[-] DIMENSIONAL COLLAPSE: {str(e)}"