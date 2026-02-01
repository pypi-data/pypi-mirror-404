#! /usr/bin/env bash

function bluer_algo_bps_simulate_timing() {
    local options=$1
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local object_name=$(bluer_ai_clarify_object $2 bps-timing-simulation-$(bluer_ai_string_timestamp_short))

    python3 -m bluer_algo.bps.utils.simulate timing \
        --object_name $object_name \
        "${@:3}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $object_name

    return 0
}
