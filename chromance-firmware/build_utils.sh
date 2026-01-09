#!/bin/bash

# Function to calculate hash of all relevant source files
calc_hash() {
    # Find all .cpp and .h files in src and test directories
    # Sort to ensure consistent ordering
    # Calculate hash of contents to detect changes
    find src test -type f \( -name "*.cpp" -o -name "*.h" \) -print0 | sort -z | xargs -0 shasum | shasum | awk '{print $1}'
}

# Checks if recompilation is needed
# Usage: check_recompile_needed <binary_path> <hash_file_path>
# Returns 0 (true) if recompile needed, 1 (false) otherwise
check_recompile_needed() {
    local BINARY="$1"
    local HASH_FILE="$2"
    local CURRENT_HASH=$(calc_hash)

    if [ -f "$BINARY" ] && [ -f "$HASH_FILE" ]; then
        local STORED_HASH=$(cat "$HASH_FILE")
        if [ "$CURRENT_HASH" == "$STORED_HASH" ]; then
            echo "Source files unchanged. Skipping compilation."
            return 1
        fi
    fi

    # Export current hash so the caller can use it to update the file after compilation
    export NEW_BUILD_HASH="$CURRENT_HASH"
    return 0
}

# Updates the hash file with the new hash
# Usage: update_build_hash <hash_file_path>
update_build_hash() {
    local HASH_FILE="$1"
    if [ -n "$NEW_BUILD_HASH" ]; then
        echo "$NEW_BUILD_HASH" > "$HASH_FILE"
    else
        # Fallback if variable not set (recalculate)
        calc_hash > "$HASH_FILE"
    fi
}
