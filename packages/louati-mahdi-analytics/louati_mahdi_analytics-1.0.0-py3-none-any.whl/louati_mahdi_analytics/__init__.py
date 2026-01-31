# louati_mahdi_analytics/__init__.py
from .base import LMA
from ._reporter import generate_welcome_pdf

# Welcome Message & PDF Generation
print("\n" + "="*50)
print("❤️  Welcome To Louati Mahdi Analytics  ❤️")print("="*50)
print("Open Source Library for Fast Analytics & Causal AI")
print("Created by Louati Mahdi (mahdi123-tech)")
print("="*50 + "\n")

# Trigger PDF generation in background
try:
    generate_welcome_pdf()
except Exception as e:
    pass # Fail silently if PDF gen fails