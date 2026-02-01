#!/bin/bash
# Django Ninja Development Setup Script
# Usage: ./setup-django-ninja.sh [--no-sync]

set -e

echo "🚀 Setting up Django Ninja development environment..."
echo ""

# Parse arguments
SYNC=true
for arg in "$@"; do
    case $arg in
        --no-sync)
            SYNC=false
            shift
            ;;
    esac
done

# Sync dependencies
if [ "$SYNC" = true ]; then
    echo "📦 Syncing dependencies..."
    uv sync --group dev --group django-ninja
    echo "✅ Dependencies synced"
    echo ""
fi

# Check if uvicorn is installed
echo "🔍 Checking uvicorn installation..."
if uv run which uvicorn > /dev/null 2>&1; then
    UVICORN_PATH=$(uv run which uvicorn)
    echo "✅ Uvicorn found at: $UVICORN_PATH"
else
    echo "❌ Uvicorn not found in project environment"
    exit 1
fi
echo ""

# Start Django Ninja server
echo "🌟 Starting Django Ninja Voyager server..."
echo "   App: tests.django_ninja.embedding:application"
echo "   URL: http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run uvicorn tests.django_ninja.embedding:application --reload --host 127.0.0.1 --port 8000
