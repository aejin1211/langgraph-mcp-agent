#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Export values from your private .env before running this script. Never enable xtrace.
: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
: "${NVIDIA_API_KEY:?Set NVIDIA_API_KEY}"
: "${NVIDIA_BASE_URL:?Set NVIDIA_BASE_URL}"
: "${NVIDIA_MODEL:?Set NVIDIA_MODEL}"
: "${TAVILY_API_KEY:?Set TAVILY_API_KEY}"
region="${GCP_REGION:-us-west1}"
service="${CLOUD_RUN_SERVICE:-csci599-a1}"

# Cloud Run source deployment builds the Dockerfile using Cloud Build and Artifact Registry.
gcloud run deploy "$service" \
    --source . \
    --project "$GCP_PROJECT_ID" \
    --region "$region" \
    --allow-unauthenticated \
    --port 8080 \
    --cpu 1 --memory 1Gi \
    --min-instances 0 --max-instances 1 --concurrency 1 \
    --timeout 300 \
    --set-env-vars "NVIDIA_API_KEY=${NVIDIA_API_KEY},NVIDIA_BASE_URL=${NVIDIA_BASE_URL},NVIDIA_MODEL=${NVIDIA_MODEL},TAVILY_API_KEY=${TAVILY_API_KEY}"
