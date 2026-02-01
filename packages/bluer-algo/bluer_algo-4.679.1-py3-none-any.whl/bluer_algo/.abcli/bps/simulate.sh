#! /usr/bin/env bash

function bluer_algo_bps_simulate() {
    local task=${1:-timing}

    local function_name=bluer_algo_bps_simulate_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    bluer_ai_log_error "@bps: simulate: $task: command not found."
}

bluer_ai_source_caller_suffix_path /simulate
