#!/usr/bin/env python
"""Run all tests and generate a report."""
import subprocess
import sys
import os
import time
from pathlib import Path
import json
from datetime import datetime


def run_tests():
    """Run all tests and return the results."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Get all test files
    test_dir = script_dir / "tests"
    test_files = list(test_dir.glob("test_*.py"))
    
    results = []
    
    # Run each test file
    for test_file in test_files:
        print(f"Running {test_file.name}...")
        start_time = time.time()
        
        # Run the test
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-xvs", str(test_file)],
            capture_output=True,
            text=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse the output
        output = process.stdout
        error = process.stderr
        success = process.returncode == 0
        
        # Count passed and failed tests
        passed = output.count("PASSED")
        failed = output.count("FAILED")
        skipped = output.count("SKIPPED")
        
        # Add to results
        results.append({
            "file": test_file.name,
            "success": success,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "output": output,
            "error": error
        })
    
    return results


def generate_report(results):
    """Generate a report from the test results."""
    # Calculate summary
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_skipped = sum(r["skipped"] for r in results)
    total_duration = sum(r["duration"] for r in results)
    
    # Create report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "duration": total_duration,
            "success": total_failed == 0
        },
        "results": results
    }
    
    return report


def save_report(report, output_file):
    """Save the report to a file."""
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)


def print_report_summary(report):
    """Print a summary of the report."""
    summary = report["summary"]
    
    print("\n" + "=" * 80)
    print(f"TEST REPORT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"Tests Passed: {summary['passed']}")
    print(f"Tests Failed: {summary['failed']}")
    print(f"Tests Skipped: {summary['skipped']}")
    print(f"Total Duration: {summary['duration']:.2f} seconds")
    print(f"Overall Status: {'SUCCESS' if summary['success'] else 'FAILURE'}")
    print("=" * 80)
    
    # Print details of failed tests
    if summary["failed"] > 0:
        print("\nFAILED TESTS:")
        for result in report["results"]:
            if result["failed"] > 0:
                print(f"\n{result['file']}:")
                # Extract failure messages
                lines = result["output"].split("\n")
                for i, line in enumerate(lines):
                    if "FAILED" in line:
                        # Print the failure message and the next few lines
                        print("  " + line)
                        for j in range(1, 4):
                            if i + j < len(lines):
                                print("  " + lines[i + j])
    
    print("\n" + "=" * 80)


def main():
    """Run tests and generate a report."""
    # Run tests
    results = run_tests()
    
    # Generate report
    report = generate_report(results)
    
    # Save report
    output_file = Path(__file__).parent / "test_report.json"
    save_report(report, output_file)
    
    # Print summary
    print_report_summary(report)
    
    # Return exit code
    return 0 if report["summary"]["success"] else 1


if __name__ == "__main__":
    sys.exit(main())