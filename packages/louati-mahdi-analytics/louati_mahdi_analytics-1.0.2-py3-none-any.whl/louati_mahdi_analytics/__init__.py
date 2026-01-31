# louati_mahdi_analytics/__init__.py
from .base import LMA
from ._reporter import generate_welcome_pdf

# THIS RUNS INSTANTLY IN COLAB WHEN YOU IMPORT
print("\n" + "="*50)
print("❤️  Welcome To Louati Mahdi Analytics  ❤️")
print("="*50)
print("Open Source Library for Fast Analytics & Causal AI")
print("Created by Louati Mahdi (mahdi123-tech)")
print("="*50 + "\n")

try:
    generate_welcome_pdf()
except Exception as e:
    print(f"PDF Generated: {e}") # Print error if fails, don't crash