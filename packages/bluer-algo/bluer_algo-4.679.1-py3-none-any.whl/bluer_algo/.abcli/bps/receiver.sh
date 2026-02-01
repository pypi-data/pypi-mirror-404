#! /usr/bin/env bash

function bluer_algo_bps_receiver() {
    local options=$1
    local use_python=$(bluer_ai_option_int "$options" python 1)

    if [[ "$use_python" == 1 ]]; then
        local do_upload=$(bluer_ai_option_int "$options" upload 0)

        local object_name=$(bluer_ai_clarify_object $2 bps-receiver-$(bluer_ai_string_timestamp))

        bluer_ai_log "starting bps receiver -> $object_name ..."

        bluer_ai_eval ,$options \
            sudo -E \
            $(which python) -m \
            bluer_algo.bps.utils.receiver \
            --object_name $object_name \
            "${@:3}"
        [[ $? -ne 0 ]] && return 1

        [[ "$do_upload" == 1 ]] &&
            bluer_objects_upload - $object_name

        return 0
    else
        bluer_ai_eval ,$options \
            sudo \
            hcitool \
            lescan \
            "${@:2}"
    fi
}
