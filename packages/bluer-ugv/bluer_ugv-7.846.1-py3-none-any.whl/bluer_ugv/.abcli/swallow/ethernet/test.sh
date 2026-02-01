#! /usr/bin/env bash

function bluer_ugv_swallow_ethernet_test() {
    local options=$1

    bluer_ai_eval ,$options \
        sudo -E \
        $(which python3) \
        -m bluer_ugv.swallow.session.classical.ethernet \
        test \
        "${@:2}"
}
