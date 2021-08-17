#!/bin/bash

img_name="qatools:latest"

echo ">> Generating"

docker run --rm repronim/neurodocker:master generate docker \
    --base=ubuntu:20.04 \
    --pkg-manager=apt \
    --freesurfer version=6.0.0-min \
    --run "apt-get update && apt-get install -y \
            python3 \
            python3-pip \
            git" \
    --run "pip3 install \
            pandas \
            numpy \
            scipy \
            matplotlib \
            nibabel \
            scikit-image \
            transforms3d" \
    --run "git clone https://github.com/Deep-MI/qatools-python.git /opt/qatools" > Dockerfile

echo ">> Building"

docker build -t ${img_name} .
