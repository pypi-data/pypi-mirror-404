#! /usr/bin/env bash

function test_bluer_algo_yolo_dataset_review() {
    local options=$1

    local dataset_object_name=$BLUER_ALGO_COCO128_TEST_DATASET

    bluer_objects_download \
        policy=doesnt_exist \
        $dataset_object_name

    bluer_ai_eval ,$options \
        bluer_algo_yolo_dataset_review \
        ~download,$options \
        $dataset_object_name
}
