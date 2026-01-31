# louati_mahdi_analytics/cli.py
import sys

def run_welcome():
    """
    This function runs when you type 'louati-mahdi' in the terminal.
    """
    print("\n" + "="*50)
    print("❤️  Welcome To Louati Mahdi Analytics  ❤️")
    print("="*50)
    print("Open Source Library for Fast Analytics & Causal AI")
    print("Created by Louati Mahdi (mahdi123-tech)")
    print("="*50 + "\n")
    
    # Try to generate PDF
    try:
        from ._reporter import generate_welcome_pdf
        generate_welcome_pdf()
    except Exception as e:
        print(f"Note: Could not generate PDF automatically. Error: {e}")

if __name__ == "__main__":
    run_welcome()