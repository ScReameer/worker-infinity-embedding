#!/bin/bash
set -e

echo "Starting Infinity Embedding Server for RunPod Serverless..."

# Start Infinity server in the background
echo "Starting Infinity server with model: ${MODEL_NAME}"
infinity_emb v2 \
    --model-id "${MODEL_NAME}" \
    --port "${INFINITY_PORT}" \
    --host "${INFINITY_HOST}" \
    --engine torch \
    --served-model-name "${MODEL_NAME}" &

INFINITY_PID=$!
echo "Infinity server started with PID: $INFINITY_PID"

# Wait for Infinity to be ready
echo "Waiting for Infinity server to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "http://${INFINITY_HOST}:${INFINITY_PORT}/health" > /dev/null 2>&1; then
        echo "Infinity server is ready!"
        break
    fi
    
    # If health endpoint doesn't exist, try root
    if curl -s "http://${INFINITY_HOST}:${INFINITY_PORT}/" > /dev/null 2>&1; then
        echo "Infinity server is ready (via root check)!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for Infinity... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Infinity server failed to start within timeout"
    kill $INFINITY_PID 2>/dev/null || true
    exit 1
fi

# Start RunPod handler
echo "Starting RunPod handler..."
exec python -u /app/handler.py
