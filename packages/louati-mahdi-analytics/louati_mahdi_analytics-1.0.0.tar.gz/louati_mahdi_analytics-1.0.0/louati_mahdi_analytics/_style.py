# louati_mahdi_analytics/_style.py

GITHUB_URL = "https://github.com/mahdi123-tech"
EMAIL = "louatimahdi390@gmail.com"

FOOTER_HTML = f"""
<div style="
    width: 100%; 
    text-align: center; 
    border-top: 2px solid #ff4081; 
    margin-top: 20px; 
    padding-top: 10px; 
    font-family: Arial, sans-serif; 
    color: #555;
    font-size: 12px;
">
    <p>Powered By <strong>Louati Mahdi</strong> ❤️</p>
    <a href="{GITHUB_URL}" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="Github" style="width:20px; height:20px; margin: 0 5px;">
    </a>
    <a href="{GITHUB_URL}" target="_blank" style="text-decoration:none; color:#333;">Visit Github</a>
</div>
"""

PDF_FOOTER_TEMPLATE = """
<div style="text-align: center; font-size: 10px; color: grey; margin-top: 2cm;">
    <p>Powered By Louati Mahdi</p>
    {qr_placeholder}
</div>
"""

PLOTLY_TEMPLATE = {
    "layout": {
        "plot_bgcolor": "#1e1e1e",
        "paper_bgcolor": "#1e1e1e",
        "font": {"color": "white"},
        "margin": {"t": 40, "b": 100}, # Extra space at bottom for footer
        "showlegend": True,
    }
}