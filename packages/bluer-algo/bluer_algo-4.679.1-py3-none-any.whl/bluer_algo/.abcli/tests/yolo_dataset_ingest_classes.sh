#! /usr/bin/env bash

function test_bluer_algo_yolo_dataset_ingest_classes() {
    local options=$1

    local object_name=test_bluer_algo_yolo_dataset_ingest_classes-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_yolo_dataset_ingest \
        ,$options \
        $object_name \
        --verbose 1 \
        --classes person+boat
    [[ $? -ne 0 ]] && return 1
    bluer_ai_hr

    bluer_ai_eval ,$options \
        bluer_algo_yolo_dataset_review \
        ~download,$options \
        $object_name
}
