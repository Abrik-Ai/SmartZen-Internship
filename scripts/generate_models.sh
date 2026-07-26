#!/bin/bash
set -e

CONTRACT_PATH="../smartzen-infra/docs/api-contract/openapi.yaml"

if [ ! -f "$CONTRACT_PATH" ]; then
  echo "Error: contract file not found at $CONTRACT_PATH"
  echo "Make sure smartzen-infra is cloned as a sibling folder to smartzen-ai."
  exit 1
fi

datamodel-codegen \
  --input "$CONTRACT_PATH" \
  --input-file-type openapi \
  --output app/models/generated.py \
  --output-model-type pydantic_v2.BaseModel

echo "Models regenerated successfully."

