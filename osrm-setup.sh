#!/usr/bin/env bash
# osrm-setup.sh
# ============================================================
# One-time OSRM graph preprocessing for Tamil Nadu, India.
# Run this ONCE before starting docker-compose for the first time.
# Output: ./osrm_data/ directory with preprocessed routing graph.
#
# Runtime estimate: 10–20 minutes on a modern laptop (4GB RAM required).
# Disk usage: ~2–3 GB for Tamil Nadu region.
#
# Usage:
#   chmod +x osrm-setup.sh
#   ./osrm-setup.sh
# ============================================================

set -euo pipefail

OSRM_IMAGE="ghcr.io/project-osrm/osrm-backend:v5.27.1"
DATA_DIR="$(pwd)/osrm_data"
# Tamil Nadu + Kerala + Karnataka combined extract (includes Karur / Karudayampalayam)
PBF_URL="https://download.geofabrik.de/asia/india/southern-zone-latest.osm.pbf"
PBF_FILE="$DATA_DIR/southern-zone-latest.osm.pbf"
BASE_NAME="karnataka-kerala-tamil-nadu"

echo "==> Creating OSRM data directory: $DATA_DIR"
mkdir -p "$DATA_DIR"

# ── Step 1: Download Tamil Nadu OSM extract ──────────────────────────────────
if [ ! -f "$PBF_FILE" ]; then
    echo "==> Downloading Tamil Nadu OSM PBF (this may take several minutes)..."
    curl -L --progress-bar -o "$PBF_FILE" "$PBF_URL"
    echo "==> Download complete: $(du -sh "$PBF_FILE" | cut -f1)"
else
    echo "==> PBF file already exists, skipping download: $PBF_FILE"
fi

# ── Step 2: Extract OSRM graph (profile: car/bus driving) ────────────────────
echo "==> Running OSRM extraction (car profile for road bus routing)..."
docker run --rm \
    -v "$DATA_DIR:/data" \
    "$OSRM_IMAGE" \
    osrm-extract \
    -p /opt/car.lua \
    "/data/southern-zone-latest.osm.pbf"

# ── Step 3: Partition graph for MLD algorithm ─────────────────────────────────
echo "==> Running OSRM partition (MLD algorithm)..."
docker run --rm \
    -v "$DATA_DIR:/data" \
    "$OSRM_IMAGE" \
    osrm-partition /data/southern-zone-latest.osrm

# ── Step 4: Customize MLD routing weights ─────────────────────────────────────
echo "==> Running OSRM customize (MLD weights)..."
docker run --rm \
    -v "$DATA_DIR:/data" \
    "$OSRM_IMAGE" \
    osrm-customize /data/southern-zone-latest.osrm

# Rename to human-readable name matching docker-compose.yml command
mv "$DATA_DIR/southern-zone-latest.osrm" "$DATA_DIR/$BASE_NAME.osrm" 2>/dev/null || true
# OSRM generates many side files — rename the base references too
for f in "$DATA_DIR"/southern-zone-latest.osrm.*; do
    mv "$f" "${f/southern-zone-latest.osrm/$BASE_NAME.osrm}" 2>/dev/null || true
done

echo ""
echo "==> OSRM preprocessing complete."
echo "    Graph files are in: $DATA_DIR/"
echo "    Now run: docker-compose up -d"
echo ""
echo "    Verify OSRM is working with:"
echo "    curl 'http://localhost:5000/route/v1/driving/77.9546,10.9549;77.9600,10.9600?overview=false'"
