# louati_mahdi_analytics/causal.py
import pandas as pd
import numpy as np

class CausalEngine:
    def __init__(self, df):
        self.df = df

    def analyze_ate(self, treatment_col, outcome_col):
        """
        Average Treatment Effect (Naive difference in means)
        """
        try:
            treated = self.df[self.df[treatment_col] == 1][outcome_col].mean()
            control = self.df[self.df[treatment_col] == 0][outcome_col].mean()
            ate = treated - control
            return f"ATE: {ate:.4f} (Treated Mean: {treated:.4f}, Control Mean: {control:.4f})"
        except:
            return "Error: Ensure treatment column is binary (0/1)."

    def plot_causal_graph(self):
        """
        Generates a dummy causal DAG visualization
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            return "Plotly required for plotting."

        fig = go.Figure(go.Scatter(
            x=[1, 2, 3], y=[2, 3, 1],
            mode='markers+text',
            text=['Treatment', 'Confounder', 'Outcome'],
            textposition="top center",
            marker=dict(size=40, color=['#ff4081', '#00bcd4', '#ffeb3b'])
        ))

        fig.add_annotation(x=1.5, y=2.5, ax=2, ay=2.8, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2)
        fig.add_annotation(x=2.5, y=2, ax=3, ay=1.5, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2)
        
        fig.update_layout(title="Simplified Causal Graph (Treatment -> Outcome)", plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white')
        return fig