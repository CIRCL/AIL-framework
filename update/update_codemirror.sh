#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
AIL_HOME="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
CODEMIRROR_DIR="${AIL_HOME}/var/www/static/codemirror/codemirror-yara"
BUILD_FILE="${CODEMIRROR_DIR}/dist/codemirror-yara.es.js"
AIL_BUNDLE="${AIL_HOME}/var/www/static/js/codemirror-yara.es.js"

if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm is required to update CodeMirror." >&2
    exit 1
fi

if [[ ! -f "${CODEMIRROR_DIR}/package.json" ]]; then
    echo "Error: CodeMirror project not found at ${CODEMIRROR_DIR}." >&2
    exit 1
fi

cleanup() {
    rm -rf "${CODEMIRROR_DIR}/dist" "${CODEMIRROR_DIR}/node_modules"
}
trap cleanup EXIT

echo "Updating CodeMirror to the latest npm release..."
npm --prefix "${CODEMIRROR_DIR}" install --package-lock-only --save-exact codemirror@latest

echo "Updating compatible transitive dependencies..."
npm --prefix "${CODEMIRROR_DIR}" update --package-lock-only

echo "Installing the locked build dependencies..."
npm --prefix "${CODEMIRROR_DIR}" ci

echo "Building the AIL CodeMirror bundle..."
npm --prefix "${CODEMIRROR_DIR}" run build

if [[ ! -f "${BUILD_FILE}" ]]; then
    echo "Error: Vite did not create ${BUILD_FILE}." >&2
    exit 1
fi

install -m 0644 "${BUILD_FILE}" "${AIL_BUNDLE}"

CODEMIRROR_VERSION="$(npm --prefix "${CODEMIRROR_DIR}" pkg get dependencies.codemirror | tr -d '\"')"
echo "CodeMirror ${CODEMIRROR_VERSION} bundle installed at ${AIL_BUNDLE}."
