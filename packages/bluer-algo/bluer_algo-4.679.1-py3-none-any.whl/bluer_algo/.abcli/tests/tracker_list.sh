#! /usr/bin/env bash

function test_bluer_algo_tracker_list() {
    local options=$1

    local args
    for args in \
        "" \
        "--log 0 --delim space"; do

        bluer_algo_tracker \
            list \
            $args

        [[ $? -ne 0 ]] && return 1
        bluer_ai_hr
    done
}
