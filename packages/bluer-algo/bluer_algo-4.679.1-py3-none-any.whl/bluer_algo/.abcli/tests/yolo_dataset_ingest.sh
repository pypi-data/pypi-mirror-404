#! /usr/bin/env bash

function test_bluer_algo_yolo_dataset_ingest() {
    local options=$1

    local object_name=test_bluer_algo_yolo_dataset_ingest-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_yolo_dataset_ingest \
        ,$options \
        $object_name \
        --verbose 1
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_algo_yolo_dataset_review \
        ~download,$options \
        $object_name
}
