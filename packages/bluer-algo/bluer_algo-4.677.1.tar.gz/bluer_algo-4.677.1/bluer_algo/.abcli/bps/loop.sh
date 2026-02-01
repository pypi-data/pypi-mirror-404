#! /usr/bin/env bash

export BPS_FILE_LOCK=$ABCLI_PATH_IGNORE/bps-lock
export BPS_IS_RUNNING=$ABCLI_PATH_IGNORE/bps-is-running

function bluer_algo_bps_loop() {
    local task=${1:-start}

    local function_name=bluer_algo_bps_loop_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    bluer_ai_log_error "@bps: loop: $task: command not found."
}

bluer_ai_source_caller_suffix_path /loop
