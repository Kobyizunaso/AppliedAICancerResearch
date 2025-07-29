#!/usr/bin/env python3
"""
Cancer Research Data Analytics Platform
Runner Script with Dependency Installation Instructions
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python 3.7+ is available"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Try different installation methods
    try:
        # Method 1: Try pip with --user
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully with pip --user")
        return True
    except subprocess.CalledProcessError:
        pass
    
    try:
        # Method 2: Try with --break-system-packages (if allowed)
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully with --break-system-packages")
        return True
    except subprocess.CalledProcessError:
        pass
    
    try:
        # Method 3: Try virtual environment
        if not os.path.exists("venv"):
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        
        if os.name == 'nt':  # Windows
            pip_path = "venv/Scripts/pip"
            python_path = "venv/Scripts/python"
        else:  # Unix-like
            pip_path = "venv/bin/pip"
            python_path = "venv/bin/python"
        
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully in virtual environment")
        print(f"🔧 To run the app, use: {python_path} app.py")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return False

def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = [
        'flask', 'pandas', 'numpy', 'sklearn', 'plotly', 
        'seaborn', 'matplotlib', 'lifelines', 'scipy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def run_application():
    """Start the Flask application"""
    print("\n🚀 Starting Cancer Research Data Analytics Platform...")
    print("📍 The application will be available at: http://localhost:5000")
    print("📍 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        print("\n💡 This likely means dependencies are not properly installed.")
        return False
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False

def main():
    """Main function to set up and run the application"""
    print("🔬 Cancer Research Data Analytics Platform")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if dependencies are available
    print("\n📋 Checking dependencies...")
    if check_dependencies():
        print("\n✅ All dependencies are available!")
        run_application()
    else:
        print("\n❌ Some dependencies are missing.")
        print("\n💡 Installation Options:")
        print("1. Create and activate a virtual environment:")
        print("   python3 -m venv cancer_research_env")
        print("   source cancer_research_env/bin/activate  # On Windows: cancer_research_env\\Scripts\\activate")
        print("   pip install -r requirements.txt")
        print("   python app.py")
        print("\n2. Install system-wide (if permitted):")
        print("   pip install -r requirements.txt")
        print("   python app.py")
        print("\n3. Use pipx (if available):")
        print("   pipx install -r requirements.txt")
        print("\n4. Install using package manager (Ubuntu/Debian):")
        print("   sudo apt update")
        print("   sudo apt install python3-flask python3-pandas python3-numpy python3-sklearn")
        print("   sudo apt install python3-plotly python3-seaborn python3-matplotlib")
        
        # Try automatic installation
        print("\n🔧 Attempting automatic installation...")
        if install_dependencies():
            print("\n✅ Installation successful! You can now run the application.")
            run_application()
        else:
            print("\n❌ Automatic installation failed. Please install dependencies manually.")
            sys.exit(1)

if __name__ == "__main__":
    main()