#! /usr/bin/env bash

function bluer_algo_bps_loop_stop() {
    local options=$1
    local rpi=$(bluer_ai_option_int "$options" rpi 0)
    local wait_for_stop=$(bluer_ai_option_int "$options" wait 0)

    if [[ "$rpi" == 1 ]]; then
        local machine_name=$2
        if [[ -z "$machine_name" ]]; then
            bluer_ai_log_error "machine_name not found."
            return 1
        fi

        ssh \
            pi@$machine_name.local \
            "rm -v /home/pi/storage/temp/ignore/bps-lock"
        return
    fi

    rm -v $BPS_FILE_LOCK

    [[ "$wait_for_stop" == 0 ]] &&
        return 0

    while [[ -f "$BPS_IS_RUNNING" ]]; do
        bluer_ai_log "waiting for bps to stop..."
        bluer_ai_sleep seconds=3.0
    done
}
