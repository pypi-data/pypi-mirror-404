#! /usr/bin/env bash

function bluer_algo_image_classifier_dataset_sequence() {
    local options=$1
    local do_download=$(bluer_ai_option_int "$options" download 1)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)
    local length=$(bluer_ai_option "$options" length 2)

    local source_object_name=$(bluer_ai_clarify_object $2 .)

    local destination_object_name=$(bluer_ai_clarify_object $3 dataset-$(bluer_ai_string_timestamp))

    [[ "$do_download" == 1 ]] &&
        bluer_objects_download - $source_object_name

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_algo.image_classifier.dataset \
        sequence \
        --length $length \
        --source_object_name $source_object_name \
        --destination_object_name $destination_object_name \
        "${@:4}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $destination_object_name

    return 0
}
