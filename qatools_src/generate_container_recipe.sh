#!/bin/bash

echo ">> Generating"

docker run --rm repronim/neurodocker:master generate docker \
    --base=ubuntu:16.04 \
    --pkg-manager=apt \
    --freesurfer version=6.0.0-min \
    --miniconda \
        conda_install="python=3.7 git pandas numpy scipy matplotlib nibabel scikit-image transforms3d" \
        use_env="base" \
    --run "git clone https://github.com/Deep-MI/qatools-python.git /opt/qatools" > Dockerfile

docker run --rm repronim/neurodocker:master generate singularity \
    --base=ubuntu:16.04 \
    --pkg-manager=apt \
    --freesurfer version=6.0.0-min \
    --miniconda \
        conda_install="python=3.7 git pandas numpy scipy matplotlib nibabel scikit-image transforms3d" \
        use_env="base" \
    --run "git clone https://github.com/Deep-MI/qatools-python.git /opt/qatools" > Singularity
