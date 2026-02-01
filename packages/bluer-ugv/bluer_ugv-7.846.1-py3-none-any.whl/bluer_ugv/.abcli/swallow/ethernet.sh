#! /usr/bin/env bash

function bluer_ugv_swallow_ethernet() {
    local task=$1

    local function_name=bluer_ugv_swallow_ethernet_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 -m bluer_ugv.swallow.session.classical.ethernet "$@"
}

bluer_ai_source_caller_suffix_path /ethernet
