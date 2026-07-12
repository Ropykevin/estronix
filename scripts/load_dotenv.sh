#!/usr/bin/env bash
# Load KEY=VALUE pairs from a .env file into the current shell.
load_dotenv() {
  local file="${1:-.env}"
  if [[ ! -f "${file}" ]]; then
    echo "Env file not found: ${file}" >&2
    return 1
  fi

  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
    if [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
    fi
  done < "${file}"
}
