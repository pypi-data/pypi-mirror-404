#! /usr/bin/env bash

function test_bluer_algo_yolo_model_prediction_test() {
    local options=$1

    local prediction_object_name=test_bluer_algo_yolo_model_prediction_test-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_yolo_model_prediction_test \
        ,$options \
        $BLUER_ALGO_COCO128_TEST_DATASET \
        $BLUER_ALGO_COCO128_TEST_MODEL \
        $prediction_object_name \
        --record_index 3
}
