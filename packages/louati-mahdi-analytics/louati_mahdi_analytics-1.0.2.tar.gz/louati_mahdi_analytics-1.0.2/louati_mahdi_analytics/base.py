# louati_mahdi_analytics/base.py
import pandas as pd
from tabulate import tabulate
from IPython.display import display, HTML
from ._style import FOOTER_HTML
from .sql_parser import SQLParser
from .stats import StatEngine
from .visuals import VisualEngine
from .causal import CausalEngine

class LMA:
    """
    Louati Mahdi Analytics - The Main Engine
    """
    def __init__(self, data=None):
        self.df = data
        self.parser = SQLParser(self.df) if self.df is not None else None
        self.stats = StatEngine(self.df) if self.df is not None else None
        self.viz = VisualEngine(self.df) if self.df is not None else None
        self.causal = CausalEngine(self.df) if self.df is not None else None

    def load(self, data):
        if isinstance(data, pd.DataFrame):
            self.df = data
            # Re-init engines
            self.parser = SQLParser(self.df)
            self.stats = StatEngine(self.df)
            self.viz = VisualEngine(self.df)
            self.causal = CausalEngine(self.df)
            return "✅ Data Loaded Successfully!"
        else:
            return "❌ Error: Input must be a Pandas DataFrame."

    def query(self, sql_str):
        if not self.parser: return "❌ No data loaded."
        try:
            result = self.parser.execute(sql_str)
            # Display in Jupyter/Notebook with Footer
            try:
                html_table = tabulate(result, headers='keys', tablefmt='html')
                display(HTML(html_table + FOOTER_HTML))
            except:
                # Fallback for terminal
                print(tabulate(result, headers='keys'))
                print("\nPowered By Louati Mahdi ❤️ (github.com/mahdi123-tech)")
            return result
        except Exception as e:
            return f"❌ Query Error: {e}"

    def plot(self, sql_str):
        if not self.viz: return "❌ No data loaded."
        fig = self.viz.render(sql_str)
        if isinstance(fig, str): # Error message
            print(fig)
        else:
            fig.show()

    def analyze(self):
        return self.stats.describe()

    def test(self, col1, col2, kind='ttest'):
        return self.stats.test(col1, col2, kind)
    
    def causal(self):
        return self.causal