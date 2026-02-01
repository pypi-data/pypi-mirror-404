#! /usr/bin/env bash

function test_bluer_algo_bps_simulate_timing() {
    local options=$1

    local object_name=test_bluer_algo_bps_simulate_timing-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_bps \
        simulate \
        timing \
        - \
        $object_name \
        "${@:2}"
}
