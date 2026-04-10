#!/bin/bash
# Pre-submission validation script for CyberSOC OpenEnv

set -e

echo "🔍 Running CyberSOC Pre-Submission Validation..."

# 1. OpenEnv spec validation
echo "✓ Checking openenv.yaml..."
if command -v openenv &> /dev/null; then
    openenv validate || { echo "❌ openenv validate failed"; exit 1; }
else
    echo "⚠️  openenv CLI not found, skipping validation"
fi

# 2. Python syntax check
echo "✓ Checking Python syntax..."
python -m py_compile cybersoc/*.py cybersoc/**/*.py || { echo "❌ Python syntax errors found"; exit 1; }

# 3. Run tests
echo "✓ Running tests..."
pytest tests/ -v || { echo "❌ Tests failed"; exit 1; }

# 4. Docker build test
echo "✓ Testing Docker build..."
docker build -t cybersoc-test:latest . || { echo "❌ Docker build failed"; exit 1; }

# 5. Container startup test
echo "✓ Testing container startup..."
CONTAINER_ID=$(docker run -d -p 7861:7860 cybersoc-test:latest)
sleep 5

curl -f -X POST http://localhost:7861/health || {
    echo "❌ Container health check failed"
    docker logs $CONTAINER_ID
    docker kill $CONTAINER_ID
    exit 1
}

docker kill $CONTAINER_ID

# 6. Inference script format check
echo "✓ Checking inference.py stdout format..."
python -c "
import inspect
with open('inference.py', 'r') as f:
    source = f.read()
    assert '[START]' in source, 'Missing [START] log'
    assert '[STEP]' in source, 'Missing [STEP] log'
    assert '[END]' in source, 'Missing [END] log'
print('✓ Log format validation passed')
"

echo ""
echo "🎉 All validation checks passed! Submission ready."
