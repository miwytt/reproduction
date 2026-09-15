#!/usr/bin/env bash
# Populate the original PHOENIX-2014T v3 distribution into the shared Modal Volume.
#
# The Volume already holds rwth-phoenix-2014-t/{annotations,features,videos}, where the
# videos are a lossy HEVC re-encoding (measured at ~1,223 bytes per 210x260 frame, about
# 134x compression). The published SLTUNET pipeline reads the original lossless PNG frames
# under features/fullFrame-210x260px, so this adds that distribution ALONGSIDE the existing
# content. It never deletes or overwrites what is already there: other papers in this
# repository may depend on the existing entries.
#
# It also brings in evaluation/sign-recognition/PHOENIX-2014-T-groundtruth-{dev,test}.stm,
# which SMKD's WER scoring requires and which ships nowhere else.
#
# Idempotent: re-running with the target present revalidates and exits without downloading.
#
# Runs inside a Modal container with the datasets Volume mounted READ-WRITE. Write access
# to that Volume is limited to this controlled population step.

set -euo pipefail

SLUG="rwth-phoenix-2014-t"
ROOT="/datasets/${SLUG}"
RAW="${ROOT}/raw"
TARGET="${RAW}/PHOENIX-2014-T-release-v3"
URL="https://www-i6.informatik.rwth-aachen.de/ftp/pub/rwth-phoenix/2016/phoenix-2014-T.v3.tar.gz"
EXPECTED_BYTES=41699758035

FRAMES="${TARGET}/PHOENIX-2014-T/features/fullFrame-210x260px"
STM="${TARGET}/PHOENIX-2014-T/evaluation/sign-recognition/PHOENIX-2014-T-groundtruth-dev.stm"

echo "=== PHOENIX-2014T v3 population ==="
date -u +"start %Y-%m-%dT%H:%M:%SZ"

verify() {
  local ok=0
  for split in train dev test; do
    if [ -d "${FRAMES}/${split}" ]; then
      n=$(find "${FRAMES}/${split}" -mindepth 1 -maxdepth 1 -type d | wc -l)
      echo "  frames/${split}: ${n} sequence directories"
      [ "${n}" -gt 0 ] || ok=1
    else
      echo "  frames/${split}: MISSING"; ok=1
    fi
  done
  if [ -f "${STM}" ]; then
    echo "  groundtruth dev.stm: present ($(wc -l < "${STM}") lines)"
  else
    echo "  groundtruth dev.stm: MISSING"; ok=1
  fi
  return "${ok}"
}

if [ -d "${TARGET}" ] && verify; then
  echo "Already populated and verified; nothing to do."
  date -u +"end %Y-%m-%dT%H:%M:%SZ"
  exit 0
fi

echo "Populating ${TARGET} from ${URL}"
echo "Expected download: ${EXPECTED_BYTES} bytes (~41.7 GB)"
mkdir -p "${RAW}"

# Stream straight into tar so the compressed archive is never stored: the Volume only ever
# holds the extracted tree. --retry covers transient stalls on the RWTH host.
curl -sSL --retry 5 --retry-delay 20 --retry-all-errors --speed-time 120 --speed-limit 1024 \
  "${URL}" | tar xz -C "${RAW}"

echo "Extraction finished; verifying"
if ! verify; then
  echo "VERIFICATION FAILED: expected paths missing after extraction" >&2
  exit 1
fi

# Provenance beside the data so a later reader knows where it came from.
cat > "${RAW}/PROVENANCE.txt" <<EOF
source_url: ${URL}
expected_bytes: ${EXPECTED_BYTES}
populated_at_utc: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
populated_by: REPRO-SIGN reproduction of Zhang et al. 2023 (SLTUNET), paper_id
  3bbc8841012fdb5971d1c86dff528edd8590f1b8
reason: the pre-existing ${SLUG}/videos tree is a lossy HEVC re-encoding, while the
  published pipeline reads the original lossless PNG frames under
  features/fullFrame-210x260px. This tree is the original RWTH distribution and was added
  alongside, not in place of, the existing content.
also_provides: evaluation/sign-recognition/PHOENIX-2014-T-groundtruth-{dev,test}.stm,
  required by SMKD WER scoring and not distributed elsewhere.
EOF
echo "wrote ${RAW}/PROVENANCE.txt"
date -u +"end %Y-%m-%dT%H:%M:%SZ"
