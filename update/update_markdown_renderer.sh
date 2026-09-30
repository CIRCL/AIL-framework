#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
AIL_HOME="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MARKDOWN_DIR="${AIL_HOME}/var/www/static/markdown/markdown-renderer"
BUILD_FILE="${MARKDOWN_DIR}/dist/markdown-renderer.es.js"
AIL_BUNDLE="${AIL_HOME}/var/www/static/js/markdown-renderer.es.js"

if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm is required to update the Markdown renderer." >&2
    exit 1
fi

if [[ ! -f "${MARKDOWN_DIR}/package.json" ]]; then
    echo "Error: Markdown renderer project not found at ${MARKDOWN_DIR}." >&2
    exit 1
fi

cleanup() {
    rm -rf "${MARKDOWN_DIR}/dist" "${MARKDOWN_DIR}/node_modules"
}
trap cleanup EXIT

echo "Updating Marked and DOMPurify to their latest npm releases..."
npm --prefix "${MARKDOWN_DIR}" install --package-lock-only --save-exact marked@latest dompurify@latest

echo "Updating compatible transitive dependencies..."
npm --prefix "${MARKDOWN_DIR}" update --package-lock-only

echo "Installing the locked build dependencies..."
npm --prefix "${MARKDOWN_DIR}" ci

echo "Building the AIL Markdown renderer bundle..."
npm --prefix "${MARKDOWN_DIR}" run build

if [[ ! -f "${BUILD_FILE}" ]]; then
    echo "Error: Vite did not create ${BUILD_FILE}." >&2
    exit 1
fi

install -m 0644 "${BUILD_FILE}" "${AIL_BUNDLE}"

MARKED_VERSION="$(npm --prefix "${MARKDOWN_DIR}" pkg get dependencies.marked | tr -d '\"')"
DOMPURIFY_VERSION="$(npm --prefix "${MARKDOWN_DIR}" pkg get dependencies.dompurify | tr -d '\"')"
echo "Marked ${MARKED_VERSION} and DOMPurify ${DOMPURIFY_VERSION} bundle installed at ${AIL_BUNDLE}."
