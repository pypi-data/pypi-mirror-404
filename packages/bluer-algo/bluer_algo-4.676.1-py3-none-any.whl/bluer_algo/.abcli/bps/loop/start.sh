#! /usr/bin/env bash

function bluer_algo_bps_loop_start() {
    if [[ -f "$BPS_FILE_LOCK" ]]; then
        bluer_ai_log_error "bps is locked, run \"@bps loop stop\" first."
        return 1
    fi

    bluer_ai_log "starting bps loop..."
    bluer_ai_log "locked" >$BPS_FILE_LOCK
    bluer_ai_log "started" >$BPS_IS_RUNNING

    local options=$1
    local do_upload=$(bluer_ai_option_int "$options" upload 1)
    local do_simulate=$(bluer_ai_option_int "$options" simulate 0)

    local object_name=$(bluer_ai_clarify_object $2 bps-stream-$(bluer_ai_string_timestamp))

    bluer_algo_bps_start_bluetooth

    if [[ ! -z "$BLUER_SBC_BPS_ANCHORED_AT" ]]; then
        bluer_ai_log "⚓️: $BLUER_SBC_BPS_ANCHORED_AT"
        bluer_algo_bps_generate - \
            $object_name \
            --as_str $BLUER_SBC_BPS_ANCHORED_AT
        [[ $? -ne 0 ]] && return 1
    fi

    local advertisement_timeout
    while [[ -f "$BPS_FILE_LOCK" ]]; do
        if [[ -z "$BLUER_SBC_BPS_ANCHORED_AT" ]]; then
            advertisement_timeout=$(bluer_ai_string_random \
                --int 1 \
                --min $BLUER_AI_BPS_LOOP_BEACON_LENGTH_MIN \
                --max $BLUER_AI_BPS_LOOP_BEACON_LENGTH_MAX)
        else
            advertisement_timeout=$BLUER_AI_BPS_LOOP_BEACON_LENGTH_MAX
        fi
        bluer_ai_log "advertisement timeout: $advertisement_timeout s"

        bluer_algo_bps_beacon ~start_bluetooth \
            $object_name \
            --timeout $advertisement_timeout \
            --simulate $do_simulate
        [[ $? -ne 0 ]] && return 1
        bluer_ai_hr

        [[ ! -f "$BPS_FILE_LOCK" ]] &&
            break

        [[ ! -z "$BLUER_SBC_BPS_ANCHORED_AT" ]] &&
            continue

        local receiver_timeout=$(bluer_ai_string_random \
            --int 1 \
            --min $BLUER_AI_BPS_LOOP_RECEIVER_LENGTH_MIN \
            --max $BLUER_AI_BPS_LOOP_RECEIVER_LENGTH_MAX)
        bluer_ai_log "receiver timeout: $receiver_timeout s"

        bluer_algo_bps_receiver ~start_bluetooth \
            $object_name \
            --grep $BLUER_AI_BPS_LOOP_GREP \
            --timeout $receiver_timeout
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done
    bluer_ai_log "stop received."

    bluer_algo_bps_review ~download,upload=$do_upload \
        $object_name

    rm -v $BPS_IS_RUNNING
}
