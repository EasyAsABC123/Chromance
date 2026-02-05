#!/bin/bash
set -e

echo "Running tests (WSL)..."
wsl -d ubuntu make run_tests