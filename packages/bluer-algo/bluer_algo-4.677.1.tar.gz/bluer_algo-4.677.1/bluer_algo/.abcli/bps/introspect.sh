#! /usr/bin/env bash

function bluer_algo_bps_introspect() {
    local options=$1
    local unique_bus_name=$(bluer_ai_option "$options" unique_bus_name)

    if [[ -z "$unique_bus_name" ]]; then
        bluer_ai_log "unique bus name not found.".
        return 1
    fi

    bluer_ai_eval ,$options \
        sudo \
        busctl \
        --system \
        introspect $unique_bus_name /org/example/Hello \
        --no-pager
    [[ $? -ne 0 ]] && return 1

    bluer_ai_eval ,$options \
        sudo \
        busctl \
        --system \
        call $unique_bus_name /org/example/Hello org.example.Hello Ping
}
