#!/bin/bash

echo ">> Generating"

docker run --rm repronim/neurodocker:master generate docker \
        --base=ubuntu:16.04 \
        --pkg-manager=apt \
        --miniconda \
                conda_install="python=3.7" \
                pip_install="antspynet" \
                use_env="base" > Dockerfile

docker run --rm repronim/neurodocker:master generate singularity \
        --base=ubuntu:16.04 \
        --pkg-manager=apt \
        --miniconda \
                conda_install="python=3.7" \
                pip_install="antspynet" \
                use_env="base" > Singularity     
