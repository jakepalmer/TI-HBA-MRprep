#!/bin/bash

# NOTE:
# The address to download the model (last line with curl) was retrieved with Chrome
# developer tools "Copy Link Address" similar to these steps:
# https://lornajane.net/posts/2013/chrome-feature-copy-as-curl
# from this site:
# https://upenn.app.box.com/v/DeepBrainNet/folder/116313459451

img_name="deep-brain-net:dev"

echo ">> Generating"

docker run --rm repronim/neurodocker:master generate docker \
        --base=ubuntu:20.04 \
        --pkg-manager=apt \
        --ants version=2.3.0 \
        --miniconda \
        conda_install="python=3.6 pip pandas numpy nibabel keras=2.2.4 tensorflow=1.12.0 pillow scikit-learn git git-annex" \
        pip_install="datalad datalad-installer h5py==2.10.0 --force-reinstall" \
        use_env="base" \
        --run "apt-get update && apt-get install -y \
                libz-dev \
                libpng-dev \
                netbase" \
        --run "git config --global --add user.name test && \
                git config --global --add user.email test && \
                datalad install -r ///templateflow && \
                cd /templateflow && \
                datalad get tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz && \
                datalad get tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_desc-brain_T1w.nii.gz && \
                datalad get tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_desc-brain_probseg.nii.gz" \
        --run "mkdir -p /opt/DeepBrainNet && cd /opt/DeepBrainNet && \
                curl 'https://public.boxcloud.com/d/1/b1!mZBUWon9BFKgUBRB6H-yvsTAulDXv2ztI8P7jDO2kvMqLaG1Qt_9CzAfkTVCqfcTa3o4n9-NBAWpCQXge4HpHvfVOO4BMyN3bLopB-4XN12Gtajkn08ruhHyWY0p2bOvWnh8MXwMhxRRvbKYiuQCTn6HopwSieZX2HmE3Zb9_UiK8xRlSTGPDKfC1K34YwTzpaCAnYVae1Ss4gPY41RR2ibxtXOToZGU01FiJo8u5rfGE59jxpS-WMX2RVS2OgbFSOVtkAoF4m5krd9r2yLmoqXD2wn2Vn6K7y1Fk965g-ioF04HhpNpHFkp29wCAWfbcVck4C_f3f31c1o63K7ylA7v8WQFpeELIk-ct7QtrudUUBrFQYDQQXLAzaB_BCY3Y2ET_QBd0jRy3eKYSfDGY6vpt7y7JWIk3dQWb7j2TikofFyGwFb33NOTB2xIaZAVosyAUiDgr1FqhA6WdXhd0okCAJbG4EZU32181uA1wlpmCAYz5-p0t--xJsH2Y5ZfI0sw0WvCx4HyNLN1LuoxTlCoN9CKq8LY0Odia3ov4E4nPbBosaa2tpLaPdPuBwoMtItedyAx3BHDcom3Jja1XZ5VVmdYQoBwv9qo--lByGJnqTW-pQw5037NRB2JvHWCmM-U6_AVD3UjwsDPy_TIMnnZzeeyteG8AayYVgxUWsDeMAEnMSIi1-hNCLiNImhRZzMWQtt79NwUjbQS0zZ2JJV7L7mJaq2AwFOTvzcuiS5oXMpWTgBb9zXj1hX9Bg4QGuRHFTNE4Im5kcfx616yF3iw_QAqvzey4U0fj0TCcOCKuv8cFv4CbIbRJnBOgxdQl0P_whEGkxLNbFmHLHSkyA4qMCu2RRMaT8TZckfUtFR2IixCxerYxqDJtR50uNgeKzmo8hihsEO5Db887d-ePKOnoXjOXuz6FEC2aJTRhAT0HawpPNKdQ17qfdQa655K8ScZPGWvngBwWZFKU6mDo3_t873gsOLNQllolIF2-jb3FM21yWYtKfLrNZ90HMO5cEAETp54zHrFJLxzkF2famqic38e9QKuWqCM7qrYlm_ek-cJJ3mJHYxusPt2ldIMfjva9Hwi5caQGaX-4vM1CQfiuIUTHJKipTI-sAhilJ-kdAnr64hkXZLOoJa6SXiwcwmZmtTp3llW4aI98wJlFIYZ21gsoSIwwbVkEEHIPhebAErgxYhJgYdR0hJFSJvcM4NBth--hxY0GBxKPVrGs0sODHRDfpwPxK_rIrOIlzM8VvIFuDOo2MeB/download' > DBN_model.h5" > Dockerfile

echo ">> Building"

docker build -t ${img_name} .
