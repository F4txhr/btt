#!/bin/bash

# Audio Player Pro Build Script
# This script helps build the project with different configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists java; then
        print_error "Java is not installed. Please install Java 11 or later."
        exit 1
    fi
    
    if ! command_exists ./gradlew; then
        print_error "Gradle wrapper not found. Please run this script from the project root."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to clean project
clean_project() {
    print_status "Cleaning project..."
    ./gradlew clean
    print_success "Project cleaned"
}

# Function to build debug APK
build_debug() {
    print_status "Building debug APK..."
    ./gradlew assembleDebug
    print_success "Debug APK built successfully"
}

# Function to build release APK
build_release() {
    print_status "Building release APK..."
    ./gradlew assembleRelease
    print_success "Release APK built successfully"
}

# Function to build all variants
build_all() {
    print_status "Building all variants..."
    ./gradlew assemble
    print_success "All variants built successfully"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    ./gradlew test
    print_success "Tests completed"
}

# Function to run instrumented tests
run_instrumented_tests() {
    print_status "Running instrumented tests..."
    ./gradlew connectedAndroidTest
    print_success "Instrumented tests completed"
}

# Function to install debug APK on connected device
install_debug() {
    print_status "Installing debug APK on device..."
    ./gradlew installDebug
    print_success "Debug APK installed successfully"
}

# Function to show help
show_help() {
    echo "Audio Player Pro Build Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  clean           Clean the project"
    echo "  debug           Build debug APK"
    echo "  release         Build release APK"
    echo "  all             Build all variants"
    echo "  test            Run unit tests"
    echo "  instrumented    Run instrumented tests"
    echo "  install         Install debug APK on device"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 debug        # Build debug APK"
    echo "  $0 clean debug  # Clean and build debug APK"
    echo "  $0 test         # Run tests"
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Process arguments
    for arg in "$@"; do
        case $arg in
            clean)
                clean_project
                ;;
            debug)
                build_debug
                ;;
            release)
                build_release
                ;;
            all)
                build_all
                ;;
            test)
                run_tests
                ;;
            instrumented)
                run_instrumented_tests
                ;;
            install)
                install_debug
                ;;
            help|--help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $arg"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_success "Build script completed successfully"
}

# Run main function with all arguments
main "$@"