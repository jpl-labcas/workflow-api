#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-west-1}"
SRC_DIR="src"
OUT_DIR="test_outputs"
MATURITY="iac"

mkdir -p "$OUT_DIR"

for lambda_dir in "$SRC_DIR"/*; do
  [ -d "$lambda_dir" ] || continue

  lambda_name="$(basename "$lambda_dir")"
  events_dir="$lambda_dir/test_events"

  if [ ! -d "$events_dir" ]; then
    echo "Skipping $lambda_name (no test_events/)"
    continue
  fi

  for event_file in "$events_dir"/*.json; do
    [ -f "$event_file" ] || continue

    event_name="$(basename "$event_file" .json)"
    out_file="$OUT_DIR/${lambda_name}_${event_name}.json"

    echo "Invoking $lambda_name with $event_name"

    aws lambda invoke \
      --region "$AWS_REGION" \
      --profile "saml-pub" \
      --function-name "labcas-workflows-$MATURITY-$lambda_name" \
      --payload "file://$event_file" \
      "$out_file" \
      --cli-binary-format raw-in-base64-out \
      >/dev/null

    echo "  → output: $out_file"
  done
done

echo "All Lambda test invocations completed."