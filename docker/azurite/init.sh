#!/bin/bash
set -e

IFS=',' read -ra CONTAINERS <<< "$AZURITE_CONTAINER_NAMES"

for container in "${CONTAINERS[@]}"; do
  echo "Creating container '$container'..."
  az storage container create \
    --name "$container" \
    --connection-string "$AZURITE_CONNECTION_STRING" \
    --output none 2>/dev/null
done

echo "Done!"
