"""
Content Studio Launcher
Run: python launcher.py
Opens: http://localhost:5000
Single login — credentials determine which business.
"""

from main_app import app

if __name__ == "__main__":
    print("\n  Content Studio — Unified")
    print("  -------------------------------------")
    print("  http://localhost:5000")
    print("  Businesses: sharp_group | ventura")
    print("  -------------------------------------\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
