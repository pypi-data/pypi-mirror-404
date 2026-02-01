#! /usr/bin/env bash

function bluer_ugv_swallow_env_cat() {
    bluer_ai_cat $abcli_path_assets/env/swallow-raspbian-${1:-driving}
}
