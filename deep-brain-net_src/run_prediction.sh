#!/bin/bash

#--- Setup ---

in="/home/input"
out="/home/output"
subject=${1}

tpl_head="/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
tpl_brain="/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_desc-brain_T1w.nii.gz"
tpl_mask="/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_desc-brain_probseg.nii.gz"

#--- Processing steps

brain_extract()
{
    echo ">> Brain extract"
    antsBrainExtraction.sh \
        -d 3 \
        -a ${in}/${subject}/anat/${subject}_T1w.nii.gz \
        -e ${tpl_head} \
        -m ${tpl_mask} \
        -o ${out}/${subject}/${subject}_
}

linear_registration()
# Linear registration to standard space
{
    echo ">> Subject to standard"
    antsRegistration \
        --dimensionality 3 \
        --float 0 \
        --output [${out}/${subject}/${subject}_BrainExtractionBrain.nii.gz,${out}/${subject}/${subject}_brain_MNI.nii.gz] \
        --interpolation Linear \
        --winsorize-image-intensities [0.005,0.995] \
        --use-histogram-matching 0 \
        --initial-moving-transform [${tpl_brain},${out}/${subject}/${subject}_BrainExtractionBrain.nii.gz,1] \
        --transform Rigid[0.1] \
        --metric MI[${tpl_brain},${out}/${subject}/${subject}_BrainExtractionBrain.nii.gz,1,32,Regular,0.25] \
        --convergence [1000x500x250x100,1e-6,10] \
        --shrink-factors 8x4x2x1 \
        --smoothing-sigmas 3x2x1x0vox \
        --transform Affine[0.1] \
        --metric MI[${tpl_brain},${out}/${subject}/${subject}_BrainExtractionBrain.nii.gz,1,32,Regular,0.25] \
        --convergence [1000x500x250x100,1e-6,10] \
        --shrink-factors 8x4x2x1 \
        --smoothing-sigmas 3x2x1x0vox
    # Remove unused files
    rm ${out}/${subject}/*BrainExtraction*
}

deep_brain_net()
# Run the DeepBrainNet model
{
    echo ">> DeepBrainNet prediction"
    mkdir -p ${out}/${subject}/Test
    python3 /home/code/Slicer.py \
        ${subject} \
        ${out}/${subject}
    python3 /home/code/Model_Test.py \
        ${out}/${subject} \
        ${out}/${subject}/${subject}_prediction.csv \
        /opt/DeepBrainNet/DBN_model.h5 \
        ${subject}
    rm -r ${out}/${subject}/Test
}

#--- Run

# brain_extract
# linear_registration
deep_brain_net
