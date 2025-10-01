"""Test runner and utilities."""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_tests():
    """Run all tests with pytest."""
    print("🧪 Running Qeem Backend Tests")
    print("=" * 50)

    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    # Run pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing"
    ]

    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False


def run_database_verification():
    """Run database verification tests only."""
    print("🔍 Running Database Verification")
    print("=" * 50)

    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_database.py",
        "-v"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Database verification passed!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Database verification failed!")
        return False


def run_model_tests():
    """Run model tests only."""
    print("📊 Running Model Tests")
    print("=" * 50)

    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_models.py",
        "-v"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Model tests passed!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Model tests failed!")
        return False


def run_api_tests():
    """Run API tests only."""
    print("🌐 Running API Tests")
    print("=" * 50)

    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_api.py",
        "-v"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ API tests passed!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ API tests failed!")
        return False


if __name__ == "__main__":
    """Run tests based on command line arguments."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()

        if test_type == "db":
            success = run_database_verification()
        elif test_type == "models":
            success = run_model_tests()
        elif test_type == "api":
            success = run_api_tests()
        elif test_type == "all":
            success = run_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available types: db, models, api, all")
            success = False
    else:
        success = run_tests()

    sys.exit(0 if success else 1)
