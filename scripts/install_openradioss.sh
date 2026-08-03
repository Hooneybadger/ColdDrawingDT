#!/usr/bin/env bash
# Download the published OpenRadioss Linux SMP binaries.
# This is a reference install, not a mill-certified solver package.
set -euo pipefail

TAG="${OPENRADIOSS_RELEASE_TAG:-latest-20260728}"
DEST="${OPENRADIOSS_ROOT:-${HOME}/OpenRadioss}"
URL="https://github.com/OpenRadioss/OpenRadioss/releases/download/${TAG}/OpenRadioss_linux64.zip"
TMP="${TMPDIR:-/tmp}/OpenRadioss_linux64.zip"

mkdir -p "$(dirname "$DEST")"
if [[ ! -x "${DEST}/exec/starter_linux64_gf" ]]; then
  echo "downloading ${URL}"
  curl -L --fail -o "$TMP" "$URL"
  rm -rf "$DEST"
  mkdir -p "$DEST"
  unzip -q "$TMP" -d "$DEST"
  # Zip may contain a top-level OpenRadioss/ directory.
  if [[ ! -x "${DEST}/exec/starter_linux64_gf" && -x "${DEST}/OpenRadioss/exec/starter_linux64_gf" ]]; then
    shopt -s dotglob
    mv "${DEST}/OpenRadioss/"* "$DEST/"
    rmdir "${DEST}/OpenRadioss"
  fi
fi

cat <<EOF
OpenRadioss root: $DEST
export OPENRADIOSS_PATH=$DEST
export OPENRADIOSS_STARTER_BIN=$DEST/exec/starter_linux64_gf
export OPENRADIOSS_ENGINE_BIN=$DEST/exec/engine_linux64_gf
export RAD_CFG_PATH=$DEST/hm_cfg_files
export RAD_H3D_PATH=$DEST/extlib/h3d/lib/linux64
export OMP_STACKSIZE=400m
export LD_LIBRARY_PATH=$DEST/extlib/hm_reader/linux64:\${LD_LIBRARY_PATH:-}
EOF
