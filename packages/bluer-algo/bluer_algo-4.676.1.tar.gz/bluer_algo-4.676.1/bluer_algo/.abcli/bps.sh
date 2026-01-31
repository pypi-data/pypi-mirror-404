#! /usr/bin/env bash

# continues sandbox/bps/v1

function bluer_algo_bps() {
    local task=${1:-test}

    local options=$2
    local do_start_bluetooth=0
    [[ "|beacon|introspect|receiver|" == *"|$task|"* ]] &&
        do_start_bluetooth=1
    do_start_bluetooth=$(bluer_ai_option_int "$options" start_bluetooth $do_start_bluetooth)
    if [[ "$do_start_bluetooth" == 1 ]]; then
        bluer_algo_bps_start_bluetooth $options
        [[ $? -ne 0 ]] && return 1
    fi

    local function_name=bluer_algo_bps_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    bluer_ai_log_error "@bps: $task: command not found."
}

bluer_ai_source_caller_suffix_path /bps
