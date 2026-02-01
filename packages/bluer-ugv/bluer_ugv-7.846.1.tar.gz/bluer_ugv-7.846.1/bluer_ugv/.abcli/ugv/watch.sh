#! /usr/bin/env bash

function bluer_ugv_watch() {
    local ugv_name=$1
    if [[ -z "$ugv_name" ]]; then
        bluer_ai_log_error "ugv name not found."
        return 1
    fi

    local node=${2:-front}

    local computer_name=$(bluer_ugv_get "$ugv_name" computers.$node)
    if [[ "$computer_name" == "not-found" ]]; then
        bluer_ai_log_error "$ugv_name.$node not found."
        return 1
    fi

    bluer_ai_log "ssh $ugv_name.$node ($computer_name)..."

    bluer_ai_log watch rpi $computer_name
}
