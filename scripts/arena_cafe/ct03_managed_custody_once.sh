#!/usr/bin/env bash
# CT-03 same-operator custody; ONLY a separately scoped custodian Actions job.
# Cloudflare R2 is private by default; credentials MUST NOT be available to D/M/B.
# No provider. Exactly one world OMC attempt; no implicit retries.
set -euo pipefail

: "${GITHUB_EVENT_NAME:?CT03_MANUAL_ONLY}"
: "${GITHUB_RUN_ID:?CT03_RUN_ID_REQUIRED}"
: "${GITHUB_SHA:?CT03_SHA_REQUIRED}"
: "${RUNNER_TEMP:?CT03_EPHEMERAL_RUNNER_REQUIRED}"
: "${CT03_R2_ACCOUNT_ID:?CT03_R2_ACCOUNT_REQUIRED}"
: "${CT03_R2_ACCESS_KEY_ID:?CT03_R2_ACCESS_KEY_REQUIRED}"
: "${CT03_R2_SECRET_ACCESS_KEY:?CT03_R2_SECRET_KEY_REQUIRED}"

test "$GITHUB_EVENT_NAME" = workflow_dispatch
test "${GITHUB_RUN_ATTEMPT:-}" = 1
test "${CT03_CUSTODIAN_MODE:-}" = CT03_ONE_APPROVED_WORLD
test "$GITHUB_REF" = refs/heads/experiment/arena-ct00-ct02-20261107
test "$GITHUB_SHA" = "${CT03_FROZEN_SHA:-}"
test "${CT03_R2_BUCKET:-}" = igc-ct03-private-custody
command -v aws >/dev/null
command -v docker >/dev/null

export AWS_ACCESS_KEY_ID="$CT03_R2_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$CT03_R2_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION=auto
export AWS_EC2_METADATA_DISABLED=true
R2_ENDPOINT="https://${CT03_R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
PRIVATE_BASE="$RUNNER_TEMP/ct03-private-custodian"
PUBLIC_BASE="$GITHUB_WORKSPACE/artifacts/ct03-public-release"
PRODUCER_CHECKOUT="$GITHUB_WORKSPACE"
R2_PREFIX="s3://${CT03_R2_BUCKET}/ct03/run-${GITHUB_RUN_ID}"
umask 077
test ! -e "$PRIVATE_BASE"
test ! -e "$PUBLIC_BASE"
mkdir -m 700 "$PRIVATE_BASE"

# Even a failure after choosing the world must leave private attempt evidence.
# This is an at-most-once job, NOT a retryable command.
on_exit() {
  rc=$?
  trap - EXIT
  if test -d "$PRIVATE_BASE"; then
    aws --endpoint-url "$R2_ENDPOINT" s3 sync "$PRIVATE_BASE/" "$R2_PREFIX/" \
      --only-show-errors >&2 || echo "CT03_PRIVATE_BACKUP_FAILED_MANUAL_STOP" >&2
  fi
  exit "$rc"
}
trap on_exit EXIT

python -m scripts.arena_cafe.ct03_private_choose \
  --out "$PRIVATE_BASE/world-config.json"
IGC_CT03_CUSTODIAN_AUTH=CT03_POST_LOCK_CUSTODIAN_ONLY \
  python -m scripts.arena_cafe.ct03_world_custody \
  --sealed-config "$PRIVATE_BASE/world-config.json" \
  --private-out "$PRIVATE_BASE/world-run" \
  --producer-root "$PRODUCER_CHECKOUT" \
  --public-commitment "$PRIVATE_BASE/world-commitment.json"

# Persist the private source and a pre-attempt journal BEFORE invoking OMC.
# If the solver fails, the attempted world still counts; do not rerun.
printf 'CT03_WORLD_OMC_ATTEMPTED_ONCE run=%s sha=%s\n' "$GITHUB_RUN_ID" "$GITHUB_SHA" \
  > "$PRIVATE_BASE/world-run/world-attempt.log"
aws --endpoint-url "$R2_ENDPOINT" s3 sync "$PRIVATE_BASE/" "$R2_PREFIX/" --only-show-errors
echo "CT03_PRIVATE_WORLD_ATTEMPT_RESERVED"

mkdir -p "$RUNNER_TEMP/ct03-libs" "$RUNNER_TEMP/ct03-omhome"
git clone --quiet --depth 1 --branch v4.0.0 \
  https://github.com/modelica/ModelicaStandardLibrary.git "$RUNNER_TEMP/ct03-libs/msl"
git clone --quiet --depth 1 --branch v2.1.2 \
  https://github.com/modelica-3rdparty/SystemDynamics.git "$RUNNER_TEMP/ct03-libs/systemdynamics"
docker pull openmodelica/openmodelica@sha256:8993c8273224aeacbc018f351c00d60879c5aec386c77a58019318c44c938c9b
# The private directory is NOT mounted into any producer job.
# The pinned image executes the existing one simulate() script, with no network.
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$GITHUB_WORKSPACE:/repo:ro" \
  -v "$PRIVATE_BASE/world-run:/private" -w /private \
  -v "$RUNNER_TEMP/ct03-omhome:/omhome" -e HOME=/omhome \
  -v "$RUNNER_TEMP/ct03-libs:/thirdparty:ro" \
  -e OPENMODELICALIBRARY=/thirdparty/msl:/thirdparty/systemdynamics \
  openmodelica/openmodelica:v1.26.5-minimal omc simulate.mos \
  > "$PRIVATE_BASE/world-run/world-omc.log" 2>&1

# Keep the full CSV (including t6/t8) private; never upload as Actions artifact.
python -m scripts.arena_cafe.ct03_minimal_custody \
  --producer-root "$PRODUCER_CHECKOUT" \
  --private-dir "$PRIVATE_BASE/world-run" \
  --commitment "$PRIVATE_BASE/world-commitment.json" \
  --public-out "$PUBLIC_BASE"

# Require durable private R2 backup BEFORE the 3-file public handoff is accepted.
aws --endpoint-url "$R2_ENDPOINT" s3 sync "$PRIVATE_BASE/" "$R2_PREFIX/" --only-show-errors
python - <<'PY'
from pathlib import Path
from scripts.arena_cafe.ct03_public_intake import FILES
p = Path("artifacts/ct03-public-release")
seen = {x.name for x in p.iterdir() if x.is_file()}
assert seen == FILES and not any(x.is_symlink() for x in p.iterdir())
print("CT03_MANAGED_CUSTODY_FOUR_PUBLIC_CUTS_ONLY")
PY
