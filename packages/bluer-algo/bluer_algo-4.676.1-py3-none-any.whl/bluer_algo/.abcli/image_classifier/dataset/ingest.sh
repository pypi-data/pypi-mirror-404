#! /usr/bin/env bash

function bluer_algo_image_classifier_dataset_ingest() {
    local options=$1
    local count=$(bluer_ai_option_int "$options" count 100)
    local do_clone=$(bluer_ai_option_int "$options" clone 0)
    local ingest_source=$(python3 -m bluer_algo.image_classifier.dataset.ingest get_source --index 0)
    ingest_source=$(bluer_ai_option "$options" source $ingest_source)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)

    local object_name=$(bluer_ai_clarify_object $2 image_classifier-dataset-$(bluer_ai_string_timestamp))

    bluer_ai_log "ingesting $ingest_source -> $object_name ..."

    [[ "$do_clone" == 1 ]] &&
        bluer_ai_git_clone \
            $BLUER_ALGO_FRUITS_360_REPO_ADDRESS

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_algo.image_classifier.dataset.ingest.$ingest_source \
        ingest \
        --count $count \
        --object_name $object_name \
        "${@:3}"
    [[ $? -ne 0 ]] && return 1

    [[ "$do_upload" == 1 ]] &&
        bluer_objects_upload - $object_name

    return 0
}
