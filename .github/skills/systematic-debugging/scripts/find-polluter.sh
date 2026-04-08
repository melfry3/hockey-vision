#!/usr/bin/env bash
# Bisection script to find which test creates unwanted files/state
# Usage: ./find-polluter.sh <file_or_dir_to_check> <test_pattern>
# Example: ./find-polluter.sh '.git' 'src/**/*.test.ts'
#
# PowerShell equivalent (Windows):
#   $testFiles = Get-ChildItem -Recurse -Filter "*.test.ts" | Sort-Object FullName
#   foreach ($tf in $testFiles) {
#     if (Test-Path $pollutionCheck) { Write-Host "Pollution exists before $tf"; continue }
#     npm test $tf.FullName 2>$null
#     if (Test-Path $pollutionCheck) { Write-Host "FOUND: $tf"; break }
#   }

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <file_to_check> <test_pattern>"
  echo "Example: $0 '.git' 'src/**/*.test.ts'"
  exit 1
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"

echo "Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo ""

# Get list of test files
TEST_FILES=$(find . -path "$TEST_PATTERN" | sort)
TOTAL=$(echo "$TEST_FILES" | wc -l | tr -d ' ')

echo "Found $TOTAL test files"
echo ""

COUNT=0
for TEST_FILE in $TEST_FILES; do
  COUNT=$((COUNT + 1))

  if [ -e "$POLLUTION_CHECK" ]; then
    echo "WARNING: Pollution already exists before test $COUNT/$TOTAL"
    echo "   Skipping: $TEST_FILE"
    continue
  fi

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"

  npm test "$TEST_FILE" > /dev/null 2>&1 || true

  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "FOUND POLLUTER!"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  npm test $TEST_FILE"
    echo "  cat $TEST_FILE"
    exit 1
  fi
done

echo ""
echo "No polluter found - all tests clean!"
exit 0
