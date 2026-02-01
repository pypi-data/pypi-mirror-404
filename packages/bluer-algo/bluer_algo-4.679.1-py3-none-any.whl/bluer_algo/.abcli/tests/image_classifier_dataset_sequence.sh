#! /usr/bin/env bash

function test_bluer_algo_image_classifier_dataset_sequence() {
    local options=$1

    local object_name=test_bluer_algo_image_classifier_dataset_sequence-$(bluer_ai_string_timestamp)

    bluer_ai_eval ,$options \
        bluer_algo_image_classifier_dataset_sequence \
        ,$options \
        $BLUER_ALGO_SWALLOW_TEST_DATASET \
        $object_name
}
