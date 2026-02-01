#! /usr/bin/env bash

function test_bluer_algo_image_classifier_model_prediction_test() {
    local options=$1

    local prediction_object_name=test_bluer_algo_image_classifier_model_prediction_test-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_image_classifier_model_prediction_test \
        ,$options \
        $BLUER_ALGO_FRUITS_360_TEST_DATASET \
        $BLUER_ALGO_FRUITS_360_TEST_MODEL \
        $prediction_object_name
}
