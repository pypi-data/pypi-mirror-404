#! /usr/bin/env bash

function test_bluer_algo_bps_generate() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_algo_bps generate - . \
        --sigma 1.0 \
        --x 0 \
        --y 0 \
        --z 0 \
        "${@:2}"
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_algo_bps generate - . \
        --simulate 1 \
        "${@:2}"
}

function test_bluer_algo_bps_generate_as_str() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_algo_bps generate - . \
        --as_str 1,2,3 \
        "${@:2}"
    [[ $? -eq 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_algo_bps generate - . \
        --as_str 1,2,3,4 \
        "${@:2}"
}

function test_bluer_algo_bps_generate_as_str_validate() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_algo_bps generate - . \
        --as_str 1,2,3 \
        --only_validate 1 \
        "${@:2}"
    [[ $? -eq 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_algo_bps generate - . \
        --as_str 1,2,3,4 \
        --only_validate 1 \
        "${@:2}"
}
