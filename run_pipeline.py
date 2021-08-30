# --- SETUP ---

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import subprocess
import os
import re

# Get command line options

parser = ArgumentParser("Workflow inputs")
parser.add_argument("--subject", type=str,
                    help="Subject to process", required=True)
parser.add_argument("--license", type=str,
                    help="FreeSurfer license file", required=True)
parser.add_argument("--base", type=str, help="Base directory", required=True)
parser.add_argument("--code", type=str, help="Code directory", required=True)
parser.add_argument("--dicom", type=str, help="Dicom directory", required=True)
parser.add_argument("--bids", type=str, help="BIDS directory", required=True)
parser.add_argument("--derivs", type=str,
                    help="BIDS derivatives directory", required=True)
parser.add_argument("--singularity_dir", type=str,
                    help="Where the singularity containers are",
                    required=True)

args = parser.parse_args()
subject = str(args.subject)
license = Path(args.license)
base_dir = Path(args.base)
code_dir = Path(args.code)
dicom_dir = Path(args.dicom)
bids_dir = Path(args.bids)
derivs_dir = Path(args.derivs)
singularity_dir = Path(args.singularity_dir)


# Singularity:
heudiconv_img = singularity_dir / "heudiconv_latest.sif"
mriqc_img = singularity_dir / "mriqc_latest.sif"
fastsurfer_img = singularity_dir / "fastsurfer_cpu.sif"
qatools_img = singularity_dir / "qatools_latest.sif"
deepbrainnet_img = singularity_dir / "ants-pynet_latest.sif"
lesionseg_img = singularity_dir / "lesion-segmentation_latest.sif"
qsiprep_img = singularity_dir / "qsiprep_latest.sif"
fmriprep_img = singularity_dir / "fmriprep_latest.sif"


# --- UTILITY FUNCTIONS ---


def printParameters():
    """
    Print command line options
    """
    print(f"""RUNNING: 
        {subject}
    DIRECTORIES:
        base                = {base_dir}
        code                = {code_dir}
        dicom               = {dicom_dir}
        BIDS                = {bids_dir}
        derivatives         = {derivs_dir}
        containers          = {singularity_dir}
    CONTAINERS:
        Heudiconv           = {heudiconv_img}
        MRIQC               = {mriqc_img}
        FastSurfer          = {fastsurfer_img}
        QA Tools            = {qatools_img}
        DeepBrainNet        = {deepbrainnet_img}
        WMH segmentation    = {lesionseg_img}
        QSIprep             = {qsiprep_img}
        fMRIprep            = {fmriprep_img}
    """)


def runBash(cmd):
    """
    Wrapper for command line.
    """
    print(f"    COMMAND: {cmd}")
    subprocess.check_call(cmd, shell=True)


# --- MAIN PROCESSING STEPS ---


def runDcm2BIDS(dicom_dir, bids_dir, code_dir, heudiconv_img, subject):
    """
    Convert dicoms for BIDS format with Heudiconv.
    - Assumes the heuristic file is created and is in the `$code/hediconv_src` directory
    - For walkthrough: https://reproducibility.stanford.edu/bids-tutorial-series-part-2a/
    - Other links: https://github.com/bids-standard/bids-starter-kit/wiki/

    The below command will only need to be run once for a single subject when setting up 
    the pipeline to generate the `heuristic.py` or if adding new scan sequences, but command is included
    here for future reference.

    `singularity run \
        --bind $dicom_dir:/base/dicom \
        --bind $bids_dir:/base/bids \
        nipy/heudiconv:latest \
            --dicom_dir_template /base/dicom/{subject}/*/*/*IM* \
            --outdir /base/bids/ \
            --heuristic convertall \
            --subjects HBA_0001_T1 \
            --converter none \
            --overwrite`

    These steps aren't in tutorials but not removing these files was
    leading to errors and they aren't needed for next step.

    `cp ${bids_dir}/.heudiconv/HBA_0001_T1/info/dicominfo.tsv ${bids_dir}`
    `cp ${bids_dir}/.heudiconv/HBA_0001_T1/info/heuristic.py ${bids_dir}`
    `rm -r ${bids_dir}/.heudiconv`

    Documentation:
    https://heudiconv.readthedocs.io/en/latest/
    """

    ### Run conversion ###
    print("    STEP: Dicom to BIDS conversion")
    cmd = f"""
    singularity run \
        --bind {dicom_dir}:/tmp/dicom \
        --bind {bids_dir}:/tmp/bids \
        --bind {code_dir}/hediconv_src/heuristic.py:/tmp/heuristic.py \
        {heudiconv_img} \
            --dicom_dir_template /tmp/dicom/{{subject}}/*/*/*IM* \
            --outdir /tmp/bids/ \
            --heuristic /tmp/heuristic.py \
            --subjects {subject} \
            --converter dcm2niix -b \
            --overwrite
    """
    runBash(cmd)


def runMRIQC(bids_dir, mriqc_img, subject):
    """
    Run MRIQC on BIDS data.
    This only runs participant level. It is recomended to run the group level
    for each analysis sample.

    Documentation:
    https://mriqc.readthedocs.io/en/stable/
    """
    print("    STEP: MRIQC")
    out_dir = derivs_dir / "mriqc"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    singularity run \
        --bind {bids_dir}:/tmp/data:ro \
        --bind {out_dir}:/tmp/out \
        {mriqc_img} /tmp/data /tmp/out \
        participant --participant_label {subject} --no-sub
    """
    runBash(cmd)


def runFastSurfer(bids_dir, derivs_dir, code_dir, fastsurfer_img, subject, license):
    """
    Run FastSurfer on T1 image.

    Documentation:
    https://github.com/Deep-MI/FastSurfer
    """
    print("    STEP: FastSurfer")
    out_dir = derivs_dir / "fastsurfer"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    fs_cmd = f"""
    singularity run \
        --bind {bids_dir}:/tmp/data \
        --bind {out_dir}:/tmp/output \
        --bind {license.parent}:/tmp/fs60/{license.name} \
        {fastsurfer_img} \
            --fs_license /tmp/fs60/{license.name} \
            --t1 /tmp/data/{subject}/anat/{subject}_T1w.nii.gz \
            --sid {subject} \
            --sd /tmp/output \
            --no_cuda \
            --parallel
    """
    qa_cmd = f"""
    singularity run \
        --bind {derivs_dir}:/tmp \
        {qatools_img} python3 /opt/qatools/qatools.py \
            --subjects_dir /tmp/fastsurfer \
            --output_dir /tmp/fastsurfer/{subject} \
            --subjects {subject} \
            --screenshots \
            --fastsurfer
    """

    if license.is_file():
        runBash(fs_cmd)
        runBash(qa_cmd)
    else:
        print("    ERROR: No license found, skipping FastSurfer")


def runDeepBrainNet(derivs_dir, bids_dir, code_dir, deepbrainnet_img, subject):
    """
    Run DeepBrainNet for brain age prediction.

    Running pipeline as implemented in ANTsPyNet:
    https://antsx.github.io/ANTsPyNet/docs/build/html/utilities.html# (find "antspynet.utilities.brain_age")
    Code from authors:
    https://github.com/vishnubashyam/DeepBrainNet
    Citation:
    https://academic.oup.com/brain/article/143/7/2312/5863667?login=true
    """
    print("    STEP: DeepBrainNet")

    out_dir = derivs_dir / "deep-brain-net"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    singularity run \
        --bind {bids_dir}:/tmp/input \
        --bind {out_dir}:/tmp/output \
        --bind {code_dir}:/tmp/code \
        {deepbrainnet_img} python3 /tmp/code/deep-brain-net_src/run_prediction.py  \
            --subject {subject}
    """
    runBash(cmd)


def runWMHsegmentation(derivs_dir, bids_dir, code_dir, lesionseg_img, subject):
    """
    WMH segmentation with BIANCA.

    Documentation:
    https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BIANCA/Userguide#Data_preparation
    """
    print("    STEP: WMH segmentation")

    out_dir = derivs_dir / "lesion-segmentation"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    singularity run \
        --bind {bids_dir}:/tmp/input \
        --bind {out_dir}:/tmp/output \
        --bind {code_dir}:/tmp/code \
        {lesionseg_img} python3 /tmp/code/lesion-segmentation_src/run_segmentation.py  \
            --subject {subject}
    """
    runBash(cmd)


def runQSIprep(derivs_dir, bids_dir, subject, license):
    """
    Run QSIprep for DWI preprocessing.

    Documentation:
    https://qsiprep.readthedocs.io/en/latest/index.html
    Citation:
    https://www.nature.com/articles/s41592-021-01185-5
    """
    print("    STEP: DWI preprocessing")

    # out_dir = derivs_dir / "qsiprep" / f"{subject}"
    out_dir = derivs_dir
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    singularity run --cleanenv \
        --bind {bids_dir}:/tmp/input \
        --bind {out_dir}:/tmp/output \
        --bind {code_dir}:/tmp/code \
        --bind {license}:/tmp/{license.name} \
        {qsiprep_img} \
            /tmp/input \
            /tmp/output \
            participant \
            --participant_label {subject} \
            --unringing-method mrdegibbs \
            --output-resolution 2 \
            --prefer-dedicated-fmaps \
            --work-dir /tmp \
            --fs-license-file /tmp/{license.name} \
            --resource-monitor \
            --stop-on-first-crash
    """
    if license.is_file():
        runBash(cmd)
    else:
        print("    ERROR: No license found, skipping QSIprep")


def runfMRIprep(derivs_dir, bids_dir, subject, license):
    """
    Run fMRIprep for rsfMRI preprocessing.

    Documentation:
    https://fmriprep.org/en/latest/index.html
    """
    print("    STEP: rsfMRI preprocessing")

    out_dir = derivs_dir / "fmriprep" / f"{subject}"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    singularity run --cleanenv \
        --bind {bids_dir}:/tmp/input \
        --bind {out_dir}:/tmp/output \
        --bind {code_dir}:/tmp/code \
        --bind {license}:/tmp/{license.name} \
        {fmriprep_img} \
            /tmp/input  \
            /tmp/output \
            participant \
            --participant_label {subject} \
            --fs-license-file /tmp/{license.name} \
            --stop-on-first-crash
    """
    if license.is_file():
        runBash(cmd)
    else:
        print("    ERROR: No license found, skipping fMRIprep")


# --- RUN PREPROCESS ---


if __name__ == "__main__":
    print(datetime.now().strftime("\n%Y-%m-%d %H:%M:%S"), "[START]\n")

    # BIDS-ify subject code (ie remove non-alphanumeric characters):
    # Remember to pass this code to processing functions as all processing
    # inputs will be taken from the BIDS data set.
    bids_subject = "sub-" + re.sub(r"[^a-zA-Z0-9]", "", str(subject))

    printParameters()
    runDcm2BIDS(dicom_dir, bids_dir, code_dir, heudiconv_img, subject)
    runMRIQC(bids_dir, mriqc_img, bids_subject)
    runFastSurfer(bids_dir, derivs_dir, code_dir,
                  fastsurfer_img, bids_subject, license)
    runDeepBrainNet(derivs_dir, bids_dir, code_dir,
                    deepbrainnet_img, bids_subject)
    runWMHsegmentation(derivs_dir, bids_dir, code_dir,
                       lesionseg_img, bids_subject)
    runQSIprep(derivs_dir, bids_dir, bids_subject, license)
    runfMRIprep(derivs_dir, bids_dir, bids_subject, license)

    print(datetime.now().strftime("\n%Y-%m-%d %H:%M:%S"), "[FINISHED]\n")
