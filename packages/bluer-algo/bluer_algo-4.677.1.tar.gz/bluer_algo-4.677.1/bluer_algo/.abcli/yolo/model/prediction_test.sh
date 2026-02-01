#! /usr/bin/env bash

function bluer_algo_yolo_model_prediction_test() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 1)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local dataset_object_name=$(bluer_ai_clarify_object $2 ..)

    local model_object_name=$(bluer_ai_clarify_object $3 .)

    if [[ "$do_download" == 1 ]]; then
        bluer_objects_download \
            policy=doesnt_exist \
            $dataset_object_name
        bluer_objects_download \
            policy=doesnt_exist \
            $model_object_name
    fi

    local prediction_object_name=$(bluer_ai_clarify_object $4 yolo-prediction-$(bluer_ai_string_timestamp))

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_algo.yolo.model \
        prediction_test \
        --dataset_object_name $dataset_object_name \
        --model_object_name $model_object_name \
        --prediction_object_name $prediction_object_name \
        "${@:5}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $prediction_object_name

    return 0
}
