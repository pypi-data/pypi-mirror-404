#! /usr/bin/env bash

function test_bluer_ugv_get() {
    bluer_ai_assert $(bluer_ugv_get) not-found
    [[ $? -ne 0 ]] && return 1

    bluer_ai_hr

    bluer_ai_assert $(bluer_ugv_get arzhang) not-found
    [[ $? -ne 0 ]] && return 1

    bluer_ai_hr

    bluer_ai_assert $(bluer_ugv_get arzhang computer.front) not-found
    [[ $? -ne 0 ]] && return 1

    bluer_ai_hr

    bluer_ai_assert $(bluer_ugv_get swallow computers.front) swallow2
}
