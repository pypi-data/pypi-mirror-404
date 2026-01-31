#! /usr/bin/env bash

function bluer_algo_image_classifier_model_train() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 1)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local dataset_object_name=$(bluer_ai_clarify_object $2 .)

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $dataset_object_name

    local model_object_name=$(bluer_ai_clarify_object $3 image_classifier-model-$(bluer_ai_string_timestamp))

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_algo.image_classifier.model \
        train \
        --dataset_object_name $dataset_object_name \
        --model_object_name $model_object_name \
        "${@:4}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $model_object_name

    return 0
}
