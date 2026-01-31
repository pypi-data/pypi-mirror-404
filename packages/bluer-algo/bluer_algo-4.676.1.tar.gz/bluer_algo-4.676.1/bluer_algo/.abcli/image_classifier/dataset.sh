#! /usr/bin/env bash

function bluer_algo_image_classifier_dataset() {
    local task=$1

    local function_name=bluer_algo_image_classifier_dataset_$task
    if [[ $(type -t $function_name) == "function" ]]; then
        $function_name "${@:2}"
        return
    fi

    python3 -m bluer_algo.image_classifier.dataset "$@"
}

bluer_ai_source_caller_suffix_path /dataset
