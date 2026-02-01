#! /usr/bin/env bash

function bluer_algo_socket() {
    local task=$1

    local function_name=bluer_algo_socket_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 bluer_algo.socket "$@"
}

bluer_ai_source_caller_suffix_path /socket
