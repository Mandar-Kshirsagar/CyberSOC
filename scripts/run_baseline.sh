#!/bin/bash
# Run baseline inference on all CyberSOC tasks

set -e

# Check required environment variables
if [ -z "$HF_TOKEN" ]; then
    echo "Error: HF_TOKEN environment variable not set"
    exit 1
fi

# Set defaults
export API_BASE_URL="${API_BASE_URL:-https://router.huggingface.co/v1}"
export MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-72B-Instruct}"

echo "Running CyberSOC Baseline Inference"
echo "===================================="
echo "Model: $MODEL_NAME"
echo "API: $API_BASE_URL"
echo ""

# Run each task
for task in phishing_triage malware_investigation; do
    echo "Running task: $task"
    echo "-----------------------------------"
    export CYBERSOC_TASK=$task
    python inference.py
    echo ""
done

echo "Baseline inference complete!"
