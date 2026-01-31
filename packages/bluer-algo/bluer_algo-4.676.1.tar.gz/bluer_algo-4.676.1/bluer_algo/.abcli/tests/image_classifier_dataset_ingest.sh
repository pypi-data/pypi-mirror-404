#! /usr/bin/env bash

function test_bluer_algo_image_classifier_dataset_ingest() {
    local options=$1

    local object_name=test_bluer_algo_image_classifier_dataset_ingest-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_image_classifier_dataset_ingest \
        clone,count=15 \
        $object_name \
        --class_count 5
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_algo_image_classifier_dataset_review \
        ~download,$options \
        $object_name
}
