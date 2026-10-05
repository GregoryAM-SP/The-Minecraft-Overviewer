#!/bin/sh
# Container entry for the Ubuntu legs of the compatibility matrix.
#
# Mounts (see run_matrix.py):
#   /repo         the Overviewer checkout (read-only)
#   /worlds       staged test worlds + manifest.json (read-only)
#   /mc-versions  Minecraft client jars, <ver>/<ver>.jar (read-only)
#   /output       writable; renders + result.json land here
# Environment:
#   COMPAT_EXCLUDE  optional repo-relative path (e.g. /tmp) to leave out of the
#                   copy; set when the host's work_dir is inside the repo
#   OV_VERSION,     git tag and commit of the host checkout. There is no .git
#   OV_HASH         (or git) in here, so setup.py would otherwise report version
#                   'unknown', which setuptools rejects
set -e

# Copy the read-only repo to a writable location, leaving out anything built
# on the host so the C extension is rebuilt against this container's numpy.
mkdir -p /work
rsync -a \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude 'build' \
    --exclude 'overviewer_core/c_overviewer*.so' \
    --exclude 'overviewer_core/c_overviewer*.pyd' \
    ${COMPAT_EXCLUDE:+--exclude "$COMPAT_EXCLUDE"} \
    /repo/ /work/

cd /work
# util.findGitTag()/findGitHash() fall back to this generated file without git.
if [ -n "$OV_VERSION" ] || [ ! -f overviewer_core/overviewer_version.py ]; then
    cat > overviewer_core/overviewer_version.py <<EOF
VERSION='${OV_VERSION:-0+unknown}'
HASH='${OV_HASH:-unknown}'
BUILD_DATE='$(date)'
BUILD_PLATFORM='$(uname -m)'
BUILD_OS='$(uname -sr)'
EOF
fi
exec python3 test/compat/render_test.py \
    --repo /work \
    --worlds /worlds \
    --versions /mc-versions \
    --output /output \
    "$@"
