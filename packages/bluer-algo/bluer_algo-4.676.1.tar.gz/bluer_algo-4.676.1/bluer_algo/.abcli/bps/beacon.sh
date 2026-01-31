#! /usr/bin/env bash

function bluer_algo_bps_beacon() {
    local options=$1

    local object_name=$(bluer_ai_clarify_object $2 bps-beacon-$(bluer_ai_string_timestamp))

    bluer_ai_log "starting bps beacon -> $object_name ..."

    bluer_ai_eval ,$options \
        sudo -E \
        $(which python3) -m \
        bluer_algo.bps.utils.beacon \
        --object_name $object_name \
        "${@:3}"
}
