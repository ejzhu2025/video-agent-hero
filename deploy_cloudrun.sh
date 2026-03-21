#!/bin/bash
# Deploy ads-video-hero to Google Cloud Run
# Usage: ./deploy_cloudrun.sh <GCP_PROJECT_ID>
set -e

PROJECT_ID="${1:-$(gcloud config get-value project)}"
SERVICE_NAME="ads-video-hero"
REGION="us-central1"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "==> Building and pushing Docker image..."
gcloud builds submit --tag "${IMAGE}:latest" .

echo "==> Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}:latest" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars "VAH_DATA_DIR=/tmp/data" \
  --project "${PROJECT_ID}"

echo ""
echo "==> Deployed! Service URL:"
gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)"
