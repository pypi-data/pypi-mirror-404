#! /usr/bin/env bash

function test_bluer_algo_image_classifier_model_train() {
    local options=$1

    local model_object_name=test_bluer_algo_image_classifier_model_train-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_image_classifier_model_train \
        ,$options \
        $BLUER_ALGO_FRUITS_360_TEST_DATASET \
        $model_object_name
}
