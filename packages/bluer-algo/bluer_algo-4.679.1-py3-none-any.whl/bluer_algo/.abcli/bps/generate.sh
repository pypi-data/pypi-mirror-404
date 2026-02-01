#! /usr/bin/env bash

function bluer_algo_bps_generate() {
    local options=$1

    local object_name=$(bluer_ai_clarify_object $2 bps-stream-$(bluer_ai_string_timestamp))

    bluer_ai_log "generate a bps stream -> $object_name ..."

    bluer_ai_eval ,$options \
        python3 -m \
        bluer_algo.bps.utils.generate \
        --object_name $object_name \
        "${@:3}"
}
