#! /usr/bin/env bash

function test_bluer_algo_tracker() {
    local options=$1

    local object_name

    bluer_ai_eval ,$options \
        bluer_algo_tracker \
        algo=void,$options
    [[ $? -eq 0 ]] && return 1
    bluer_ai_hr

    local algo
    local do_log
    for algo in $(bluer_algo_tracker list --log 0 --delim space); do
        for do_log in 0 1; do
            object_name=test_bluer_algo_tracker-$(bluer_ai_string_timestamp)
            bluer_ai_eval ,$options \
                bluer_algo_tracker \
                algo=$algo,$options \
                $object_name \
                --frame_count 5 \
                --log $do_log \
                --show_gui 0 \
                --verbose 1
            [[ $? -ne 0 ]] && return 1
            bluer_ai_hr
        done
    done
}
