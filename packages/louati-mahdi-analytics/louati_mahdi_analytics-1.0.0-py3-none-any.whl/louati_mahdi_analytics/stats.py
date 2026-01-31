# louati_mahdi_analytics/stats.py
from scipy import stats
import pandas as pd

class StatEngine:
    def __init__(self, df):
        self.df = df

    def describe(self):
        return self.df.describe()

    def test(self, col1, col2, test_type='ttest'):
        """
        test_type: 'ttest', 'chi2', 'anova', 'corr'
        """
        d1 = self.df[col1].dropna()
        d2 = self.df[col2].dropna()
        
        res = {}
        if test_type == 'ttest':
            t_stat, p_val = stats.ttest_ind(d1, d2)
            res = {'Test': 'T-Test', 'Statistic': t_stat, 'P-Value': p_val}
        elif test_type == 'corr':
            corr, p_val = stats.pearsonr(d1, d2)
            res = {'Test': 'Pearson Corr', 'Statistic': corr, 'P-Value': p_val}
        elif test_type == 'chi2':
            # Requires categorical data
            contingency = pd.crosstab(d1, d2)
            chi2, p_val, _, _ = stats.chi2_contingency(contingency)
            res = {'Test': 'Chi-Square', 'Statistic': chi2, 'P-Value': p_val}
            
        return pd.DataFrame([res])