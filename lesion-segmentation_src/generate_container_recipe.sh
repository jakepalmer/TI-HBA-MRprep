#!/bin/bash

echo ">> Generating"

docker run --rm repronim/neurodocker:master generate docker \
        --base=ubuntu:16.04 \
        --pkg-manager=apt \
        --fsl version=6.0.1 \
        --miniconda \
                conda_install="python=3.7 git" \
                use_env="base" \
        --run "git clone https://issues.dpuk.org/eugeneduff/wmh_harmonisation.git /opt/wmh_harmonisation" > Dockerfile

docker run --rm repronim/neurodocker:master generate singularity \
        --base=ubuntu:16.04 \
        --pkg-manager=apt \
        --fsl version=6.0.1 \
        --miniconda \
                conda_install="python=3.7 git" \
                use_env="base" \
        --run "git clone https://issues.dpuk.org/eugeneduff/wmh_harmonisation.git /opt/wmh_harmonisation" > Singularity
