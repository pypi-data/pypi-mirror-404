#! /usr/bin/env bash

function test_bluer_algo_tracker_sandbox() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_algo_tracker \
        algo=void,sandbox,$options
    [[ $? -eq 0 ]] && return 1
    bluer_ai_hr

    local algo
    for algo in camshift meanshift; do
        bluer_ai_eval ,$options \
            bluer_algo_tracker \
            algo=$algo,sandbox,$options \
            - \
            --frame_count 5 \
            --show_gui 0 \
            --verbose 1
        [[ $? -ne 0 ]] && return 1
        bluer_ai_hr
    done
}
