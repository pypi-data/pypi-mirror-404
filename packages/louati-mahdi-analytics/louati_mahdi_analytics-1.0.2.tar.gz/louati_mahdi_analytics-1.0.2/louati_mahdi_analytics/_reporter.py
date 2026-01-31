# louati_mahdi_analytics/_reporter.py
import os
import qrcode
from fpdf import FPDF
from datetime import datetime
from ._style import EMAIL

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Louati Mahdi Analytics - Documentation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        self.ln(5)
        # QR Code logic
        self.image(self.qr_path, self.w - 35, self.h - 25, 25)
        self.cell(0, 10, 'Contact Me', 0, 1, 'R')

def generate_welcome_pdf():
    try:
        home_dir = os.path.expanduser("~")
        pdf_path = os.path.join(home_dir, "Louati_Mahdi_Welcome.pdf")
        qr_path = os.path.join(home_dir, "temp_qr.png")

        # Generate QR
        img = qrcode.make(f"mailto:{EMAIL}")
        img.save(qr_path)

        pdf = PDF()
        pdf.qr_path = qr_path
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=25)
        
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(50, 50, 50)

        title = "Welcome to Louati Mahdi Analytics Engine"
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", size=11)
        
        description = f"""
        Hello! I am Louati Mahdi, a passionate Data Engineer. 
        
        I created this open-source library because I believe that powerful analytics should be 
        free, fast, and accessible to everyone. There should be no upfront costs or hidden fees 
        to understand your data.
        
        My hobbies include building python libraries, solving complex data problems, and 
        helping the community make better decisions with data.
        
        This library can:
        1. Query data using custom SQL prompts.
        2. Perform Hypothesis testing (T-tests, Chi2, ANOVA).
        3. Run Causal Inference analysis.
        4. Visualize data with beautiful Plotly charts.
        
        Enjoy your journey!
        """
        pdf.multi_cell(0, 7, description)
        
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')

        pdf.output(pdf_path)
        
        # Cleanup
        if os.path.exists(qr_path):
            os.remove(qr_path)
            
        print(f"✅ Welcome PDF saved to: {pdf_path}")
    except Exception as e:
        print(f"⚠️ Could not generate PDF: {e}")