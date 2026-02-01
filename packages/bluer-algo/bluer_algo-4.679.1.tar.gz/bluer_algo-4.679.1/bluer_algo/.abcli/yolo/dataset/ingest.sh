#! /usr/bin/env bash

function bluer_algo_yolo_dataset_ingest() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_upload=$(bluer_ai_option_int "$options" upload 0)
    local ingest_source=$(python3 -m bluer_algo.yolo.dataset.ingest get_source --index 0)
    ingest_source=$(bluer_ai_option "$options" source $ingest_source)

    local url=https://github.com/ultralytics/yolov5/releases/download/v1.0/coco128.zip

    local object_name=$(bluer_ai_clarify_object $2 yolo-dataset-$(bluer_ai_string_timestamp))
    mkdir -pv $ABCLI_OBJECT_ROOT/$object_name
    local filename="$ABCLI_OBJECT_ROOT/$object_name/coco128.zip"

    bluer_ai_log "ingesting $ingest_source -> $object_name ..."

    bluer_ai_eval - \
        wget -O $filename $url -v
    [[ $? -ne 0 ]] && return 1

    unzip \
        $filename \
        -d $ABCLI_OBJECT_ROOT/$object_name
    [[ $? -ne 0 ]] && return 1

    rm -v $filename

    bluer_ai_eval dryrun=$do_dryrun \
        python3 -m bluer_algo.yolo.dataset.ingest.$ingest_source \
        ingest \
        --object_name $object_name \
        "${@:3}"
    [[ $? -ne 0 ]] && return 1

    if [[ "$do_upload" == 1 ]]; then
        bluer_objects_upload - $object_name
    fi
}
