#! /usr/bin/env bash

function bluer_ugv_get() {
    python3 -m bluer_ugv.README.ugvs \
        get \
        --ugv_name "$1" \
        --what "$2" \
        "${@:3}"
}
