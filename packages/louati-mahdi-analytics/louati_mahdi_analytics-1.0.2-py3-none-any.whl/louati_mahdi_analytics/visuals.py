# louati_mahdi_analytics/visuals.py
import plotly.express as px
import plotly.graph_objects as go
from ._style import FOOTER_HTML, PLOTLY_TEMPLATE

class VisualEngine:
    def __init__(self, df):
        self.df = df

    def render(self, sql_command):
        """
        Parses commands like:
        PLOT BAR x=col1 y=col2 color=col3
        PLOT LINE x=date y=sales
        PLOT SCATTER x=age y=income
        """
        cmd = sql_command.upper().replace("PLOT", "").strip()
        parts = cmd.split(' ')
        chart_type = parts[0].lower()
        
        params = {}
        for part in parts[1:]:
            if '=' in part:
                k, v = part.split('=')
                params[k.lower()] = v.lower()

        # Map params
        x = params.get('x')
        y = params.get('y')
        color = params.get('color')
        
        if not x or not y:
            return "Error: Syntax -> PLOT <TYPE> x=<col> y=<col>"

        fig = None
        if chart_type == 'bar':
            fig = px.bar(self.df, x=x, y=y, color=color if color else None, template="plotly_dark")
        elif chart_type == 'line':
            fig = px.line(self.df, x=x, y=y, color=color if color else None, template="plotly_dark")
        elif chart_type == 'scatter':
            fig = px.scatter(self.df, x=x, y=y, color=color if color else None, template="plotly_dark")
        elif chart_type == 'pie':
            fig = px.pie(self.df, names=x, values=y, template="plotly_dark")
        elif chart_type == 'hist':
            fig = px.histogram(self.df, x=x, color=color if color else None, template="plotly_dark")
        else:
            return f"Unknown plot type: {chart_type}"

        # Apply Custom Theme
        fig.update_layout(
            PLOTLY_TEMPLATE['layout'],
            title=f"{chart_type.upper()} Chart: {y} vs {x}"
        )

        # Add Footer Annotation
        fig.add_annotation(
            x=0.5, y=-0.25,
            xref="paper", yref="paper",
            text=FOOTER_HTML.replace('style="', 'style="font-size:12px; '),
            showarrow=False,
            align="center",
        )
        
        return fig