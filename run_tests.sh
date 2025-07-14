#!/bin/bash

# Test Runner Script for ELI5 Server
# Provides convenient commands for running different types of tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_colored() {
    echo -e "${1}${2}${NC}"
}

# Function to print section headers
print_header() {
    echo
    print_colored $BLUE "=================================="
    print_colored $BLUE "$1"
    print_colored $BLUE "=================================="
    echo
}

# Function to check if dependencies are installed
check_dependencies() {
    print_header "Checking Dependencies"
    
    if ! command -v python3 &> /dev/null; then
        print_colored $RED "❌ Python3 is not installed"
        exit 1
    fi
    
    if ! python3 -c "import pytest" &> /dev/null; then
        print_colored $RED "❌ pytest is not installed"
        print_colored $YELLOW "Install with: pip install -r requirements.txt"
        exit 1
    fi
    
    print_colored $GREEN "✅ All dependencies are available"
}

# Function to run all tests
run_all_tests() {
    print_header "Running All Tests"
    python3 -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
}

# Function to run unit tests only
run_unit_tests() {
    print_header "Running Unit Tests"
    python3 -m pytest tests/test_auth.py tests/test_database.py tests/test_services.py tests/test_schemas.py -v
}

# Function to run integration tests only
run_integration_tests() {
    print_header "Running Integration Tests"
    python3 -m pytest tests/test_main.py tests/test_integration.py -v
}

# Function to run tests with coverage
run_coverage() {
    print_header "Running Tests with Coverage"
    python3 -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80
    
    if [ -d "htmlcov" ]; then
        print_colored $GREEN "📊 Coverage report generated in htmlcov/index.html"
    fi
}

# Function to run specific test file
run_specific_test() {
    if [ -z "$1" ]; then
        print_colored $RED "❌ Please specify a test file"
        print_colored $YELLOW "Usage: $0 test <test_file>"
        print_colored $YELLOW "Example: $0 test auth"
        exit 1
    fi
    
    TEST_FILE="tests/test_${1}.py"
    
    if [ ! -f "$TEST_FILE" ]; then
        print_colored $RED "❌ Test file $TEST_FILE not found"
        exit 1
    fi
    
    print_header "Running Tests from $TEST_FILE"
    python3 -m pytest "$TEST_FILE" -v
}

# Function to run tests in watch mode
run_watch_mode() {
    print_header "Running Tests in Watch Mode"
    print_colored $YELLOW "Note: Install pytest-xdist for watch mode"
    print_colored $YELLOW "pip install pytest-xdist"
    
    # Basic file watching with inotify (Linux) or fswatch (macOS)
    if command -v inotifywait &> /dev/null; then
        print_colored $GREEN "🔄 Watching for file changes..."
        while inotifywait -r -e modify,create,delete --include='.*\.py$' .; do
            print_header "Files Changed - Running Tests"
            python3 -m pytest tests/ -x --tb=short
        done
    else
        print_colored $YELLOW "⚠️  Install inotify-tools for file watching"
        print_colored $YELLOW "Running tests once..."
        python3 -m pytest tests/ -v
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_header "Running Performance Tests"
    print_colored $YELLOW "⏱️  Running performance-related tests..."
    python3 -m pytest tests/test_integration.py::TestPerformanceIntegration -v
}

# Function to run linting
run_linting() {
    print_header "Running Code Quality Checks"
    
    # Check if flake8 is installed
    if python3 -c "import flake8" &> /dev/null; then
        print_colored $BLUE "🧹 Running flake8..."
        python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    else
        print_colored $YELLOW "⚠️  flake8 not installed, skipping linting"
    fi
    
    # Check if black is installed
    if python3 -c "import black" &> /dev/null; then
        print_colored $BLUE "🎨 Checking code formatting with black..."
        python3 -m black --check .
    else
        print_colored $YELLOW "⚠️  black not installed, skipping format check"
    fi
}

# Function to generate test report
generate_test_report() {
    print_header "Generating Comprehensive Test Report"
    
    REPORT_DIR="test_reports"
    mkdir -p "$REPORT_DIR"
    
    # Run tests with detailed output
    python3 -m pytest tests/ \
        --cov=. \
        --cov-report=html:"$REPORT_DIR/coverage" \
        --cov-report=xml:"$REPORT_DIR/coverage.xml" \
        --junit-xml="$REPORT_DIR/junit.xml" \
        --html="$REPORT_DIR/report.html" \
        --self-contained-html \
        -v
    
    print_colored $GREEN "📋 Test reports generated in $REPORT_DIR/"
    print_colored $GREEN "   - HTML Report: $REPORT_DIR/report.html"
    print_colored $GREEN "   - Coverage: $REPORT_DIR/coverage/index.html"
    print_colored $GREEN "   - JUnit XML: $REPORT_DIR/junit.xml"
}

# Function to clean test artifacts
clean_test_artifacts() {
    print_header "Cleaning Test Artifacts"
    
    rm -rf htmlcov/
    rm -rf test_reports/
    rm -rf .coverage
    rm -rf .pytest_cache/
    rm -rf **/__pycache__/
    rm -f test_eli5.db
    
    print_colored $GREEN "🧹 Test artifacts cleaned"
}

# Function to setup test environment
setup_test_environment() {
    print_header "Setting Up Test Environment"
    
    # Install test dependencies
    print_colored $BLUE "📦 Installing test dependencies..."
    pip install -r requirements.txt
    
    # Create test database if needed
    print_colored $BLUE "🗄️  Setting up test database..."
    python3 -c "
from database import create_tables
create_tables()
print('✅ Test database initialized')
"
    
    print_colored $GREEN "🚀 Test environment setup complete"
}

# Function to show usage
show_usage() {
    print_header "ELI5 Server Test Runner"
    
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  all                 Run all tests with coverage"
    echo "  unit               Run unit tests only"
    echo "  integration        Run integration tests only"
    echo "  coverage           Run tests with coverage report"
    echo "  test <name>        Run specific test file (e.g., 'auth', 'database')"
    echo "  watch              Run tests in watch mode"
    echo "  performance        Run performance tests"
    echo "  lint               Run code quality checks"
    echo "  report             Generate comprehensive test report"
    echo "  clean              Clean test artifacts"
    echo "  setup              Setup test environment"
    echo "  help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 all                    # Run all tests"
    echo "  $0 test auth             # Run authentication tests"
    echo "  $0 coverage              # Run with coverage"
    echo "  $0 unit                  # Run unit tests only"
    echo
}

# Main script logic
main() {
    case "${1:-help}" in
        "all")
            check_dependencies
            run_all_tests
            ;;
        "unit")
            check_dependencies
            run_unit_tests
            ;;
        "integration")
            check_dependencies
            run_integration_tests
            ;;
        "coverage")
            check_dependencies
            run_coverage
            ;;
        "test")
            check_dependencies
            run_specific_test "$2"
            ;;
        "watch")
            check_dependencies
            run_watch_mode
            ;;
        "performance")
            check_dependencies
            run_performance_tests
            ;;
        "lint")
            run_linting
            ;;
        "report")
            check_dependencies
            generate_test_report
            ;;
        "clean")
            clean_test_artifacts
            ;;
        "setup")
            setup_test_environment
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function with all arguments
main "$@"
