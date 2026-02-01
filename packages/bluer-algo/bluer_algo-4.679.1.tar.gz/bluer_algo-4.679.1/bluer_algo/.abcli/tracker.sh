#! /usr/bin/env bash

export BLUER_ALGO_TRACKER_ALGO_VERSIONS="camshift=v6,meanshift=v6"

function bluer_algo_tracker() {
    local options=$1
    local get_list_of_algo=$(bluer_ai_option_int "$options" list 0)
    if [[ "$get_list_of_algo" == 1 ]]; then
        python3 -m bluer_algo.tracker \
            list_algo \
            "${@:2}"
        return
    fi

    local algo=$(bluer_ai_option "$options" algo $BLUER_ALGO_TRACKER_DEFAULT_ALGO)
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local use_sandbox=$(bluer_ai_option_int "$options" sandbox 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local object_name=$(bluer_ai_clarify_object $2 tracker-$(bluer_ai_string_timestamp))

    local callable="python3 -m bluer_algo.tracker track --algo $algo --object_name $object_name"
    local title=$algo
    if [[ "$use_sandbox" == 1 ]]; then
        local version=$(bluer_ai_option $BLUER_ALGO_TRACKER_ALGO_VERSIONS $algo)
        if [[ -z "$version" ]]; then
            bluer_ai_log_error "algo: $algo not found."
            return 1
        fi

        callable="python3 $abcli_path_git/bluer-algo/sandbox/mean-cam-shift/$algo-$version.py"
        title="$algo.sandbox-$version"
    fi

    local use_camera=$(bluer_ai_option_int "$options" camera 0)

    local video_source="camera"
    if [[ "$use_camera" == 0 ]]; then
        local source_object_name="mean-cam-shift-data-v1"
        local url="https://www.bogotobogo.com/python/OpenCV_Python/images/mean_shift_tracking/slow_traffic_small.mp4"
        local filename="$ABCLI_OBJECT_ROOT/$source_object_name/slow_traffic_small.mp4"

        bluer_objects_download \
            policy=doesnt_exist \
            $source_object_name

        local do_download=1
        [[ "$do_dryrun" == 1 ]] &&
            do_download=0
        [[ -f $filename ]] &&
            do_download=0
        do_download=$(bluer_ai_option_int "$options" download $do_download)

        if [[ "$do_download" == 1 ]]; then
            mkdir -pv $ABCLI_OBJECT_ROOT/$source_object_name
            bluer_ai_eval - \
                wget -O $filename $url -v
            [[ $? -ne 0 ]] && return 1
        fi

        video_source="$ABCLI_OBJECT_ROOT/$source_object_name/slow_traffic_small.mp4"
    fi

    bluer_ai_eval dryrun=$do_dryrun \
        $callable \
        --source $video_source \
        --title $title \
        "${@:3}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $object_name

    return 0
}
