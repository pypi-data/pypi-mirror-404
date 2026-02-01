#! /usr/bin/env bash

function test_bluer_algo_help() {
    local options=$1

    local module
    for module in \
        "@algo" \
        \
        "@algo pypi" \
        "@algo pypi browse" \
        "@algo pypi build" \
        "@algo pypi install" \
        \
        "@algo pytest" \
        \
        "@algo test" \
        "@algo test list" \
        \
        "@algo image_classifier" \
        "@algo image_classifier dataset" \
        "@algo image_classifier dataset ingest" \
        "@algo image_classifier dataset review" \
        "@algo image_classifier dataset sequence" \
        "@algo image_classifier model" \
        "@algo image_classifier model prediction_test" \
        "@algo image_classifier model train" \
        \
        "@algo yolo" \
        "@algo yolo dataset" \
        "@algo yolo dataset ingest" \
        "@algo yolo model" \
        "@algo yolo model prediction_test" \
        "@algo yolo model train" \
        \
        "@algo socket" \
        "@algo socket test" \
        \
        "@algo tracker" \
        "@algo tracker list" \
        \
        "@algo bps" \
        "@bps" \
        "@bps beacon" \
        "@bps generate" \
        "@bps install" \
        "@bps introspect" \
        "@bps loop" \
        "@bps loop start" \
        "@bps loop stop" \
        "@bps receiver" \
        "@bps review" \
        "@bps set_anchor" \
        "@bps simulate" \
        "@bps simulate timing" \
        "@bps test_bluetooth" \
        \
        "@image_classifier" \
        "@image_classifier dataset" \
        "@image_classifier dataset ingest" \
        "@image_classifier dataset review" \
        "@image_classifier dataset sequence" \
        "@image_classifier model" \
        "@image_classifier model prediction_test" \
        "@image_classifier model train" \
        \
        "@yolo" \
        "@yolo dataset" \
        "@yolo dataset ingest" \
        "@yolo dataset review" \
        "@yolo model" \
        "@yolo model prediction_test" \
        "@yolo model train" \
        \
        "bluer_algo"; do
        bluer_ai_eval ,$options \
            bluer_ai_help $module
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done

    return 0
}
