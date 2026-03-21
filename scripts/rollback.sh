#!/bin/bash
# Rollback ads-video-hero to a previous Cloud Run revision.
# Usage: ./scripts/rollback.sh [revision-name]
# Example: ./scripts/rollback.sh ads-video-hero-00042-abc
#
# With no argument: lists recent revisions so you can pick one.

SERVICE="ads-video-hero"
REGION="us-central1"

if [ -z "$1" ]; then
  echo ""
  echo "Recent revisions for $SERVICE:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  gcloud run revisions list \
    --service="$SERVICE" \
    --region="$REGION" \
    --format="table(name,createTime,status.conditions[0].status)" \
    --limit=10
  echo ""
  echo "Usage: $0 <revision-name>"
  echo "Example: $0 ads-video-hero-00042-abc"
  exit 0
fi

REVISION="$1"
echo ""
echo "⚠️  Rolling back $SERVICE → $REVISION"
echo "   This will send 100% of traffic to revision: $REVISION"
read -p "   Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 1
fi

gcloud run services update-traffic "$SERVICE" \
  --region="$REGION" \
  --to-revisions="${REVISION}=100"

echo ""
echo "✓ Traffic routed to $REVISION"
echo ""
echo "Verify:"
echo "  python scripts/smoke_test.py https://adreel.studio"
