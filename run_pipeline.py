# --- SETUP ---

from argparse import ArgumentParser
from pathlib import Path
import subprocess
import os

# Get command line options

parser = ArgumentParser("Workflow inputs")
parser.add_argument("--subject", type=str,
                    help="Subject to process", required=True)
parser.add_argument("--base", type=str, help="Base directory", required=True)
parser.add_argument("--code", type=str, help="Code directory", required=True)
parser.add_argument("--dicom", type=str, help="Dicom directory", required=True)
parser.add_argument("--bids", type=str, help="BIDS directory", required=True)
parser.add_argument("--derivs", type=str,
                    help="BIDS derivatives directory", required=True)
parser.add_argument("--singularity_dir", type=str,
                    help="Where the singularity containers are", required=True)

args = parser.parse_args()
subject = Path(args.subject)
base_dir = Path(args.base)
code_dir = Path(args.code)
dicom_dir = Path(args.dicom)
bids_dir = Path(args.bids)
derivs_dir = Path(args.derivs)
singularity_dir = Path(args.singularity_dir)

# Set containers to be used for each
heudiconv_img = "nipy/heudiconv:latest"
mriqc_img = "poldracklab/mriqc:latest"
fastsurfer_img = "fastsurfer:cpu"
qatools_img = "qatools:latest"
deepbrainnet_img = "deep-brain-net:dev"
# Template for adding singularity containers
# mriqc_img = singularity_dir / "mriqc.sif"


# --- FUNCTIONS ---


def printParameters():
    """
    Print command line options
    """
    print(f""" 
    RUNNING: 
        {subject}
    DIRECTORIES:
        base         = {base_dir}
        code         = {code_dir}
        dicom        = {dicom_dir}
        BIDS         = {bids_dir}
        Derivatives  = {derivs_dir}
        Containers   = {singularity_dir}
    CONTAINERS:
        Heudiconv    = {heudiconv_img}
        MRIQC        = {mriqc_img}
        FastSurfer   = {fastsurfer_img}
        QA Tools     = {qatools_img}
        DeepBrainNet = {deepbrainnet_img}
    """)


def runBash(cmd: str):
    print(f"    COMMAND: {cmd}")
    subprocess.check_call(cmd, shell=True)


def checkFSlicense():
    f_list = []
    dir = f"{code_dir}/fastsurfer_src"
    for f in os.listdir(dir):
        f_list.append(f)

    result = any("license" in x for x in f_list)

    if result == False:
        print("""    ERROR: Cannot find any FreeSurfer license in fastsurfer_src directory. 
    If it is there, make sure it includes the word 'license' somewhere in the file name.
        """)
        return 1, None
    elif result == True:
        for x in f_list:
            if "license" in x:
                license_file = x
        return 0, license_file


def runDcm2BIDS(dicom_dir: Path, bids_dir: Path, code_dir: Path, heudiconv_img: str, subject: str):
    """
    Convert dicoms for BIDS format with Heudiconv.
    - Assumes the heuristic file is created and is in the ``$code/hediconv_src`` directory
    - For walkthrough: https://reproducibility.stanford.edu/bids-tutorial-series-part-2a/
    - Other links: https://github.com/bids-standard/bids-starter-kit/wiki/

    The below command will only need to be run once for a single subject when setting up 
    the pipeline to generate the ``heuristic.py`` or if adding new scan sequences, but command is included
    here for future reference.

    ``docker run --rm -it \
        -v {dicom_dir}:/base/dicom \
        -v {bids_dir}:/base/bids \
        nipy/heudiconv:latest \
            --dicom_dir_template /base/dicom/{{subject}}/*/*/IM* \
            --outdir /base/bids/ \
            --heuristic convertall \
            --subjects HBA_0001_T1 \
            --converter none \
            --overwrite``

    These steps aren't in tutorials but not removing these files was
    leading to errors and they aren't needed for next step.

    ``cp ${bids_dir}/.heudiconv/HBA_0001_T1/info/dicominfo.tsv ${bids_dir}``
    ``cp ${bids_dir}/.heudiconv/HBA_0001_T1/info/heuristic.py ${bids_dir}``
    ``rm -r ${bids_dir}/.heudiconv``

    Documentation:
    https://heudiconv.readthedocs.io/en/latest/
    """

    ### Run conversion ###
    print("\n    STEP: Dicom to BIDS conversion\n")
    cmd = f"""
    docker run --rm -it \
        -v {dicom_dir}:/base/dicom \
        -v {bids_dir}:/base/bids \
        -v {code_dir}/hediconv_src/heuristic.py:/base/heuristic.py \
        {heudiconv_img} \
            --dicom_dir_template /base/dicom/{{subject}}/*/*/IM* \
            --outdir /base/bids/ \
            --heuristic /base/heuristic.py \
            --subjects {subject} \
            --converter dcm2niix -b \
            --overwrite
    """
    runBash(cmd)


def runMRIQC(bids_dir: Path, mriqc_img: str, subject: str):
    """
    Run MRIQC on BIDS data.
    This only runs participant level. It is recomended to run the group level
    for each analysis sample.

    Documentation:
    https://mriqc.readthedocs.io/en/stable/
    """
    print("\n    STEP: MRIQC\n")
    out_dir = derivs_dir / "mriqc"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    docker run -it --rm \
        -v {bids_dir}:/data:ro \
        -v {out_dir}:/out \
        {mriqc_img} /data /out \
        participant --participant_label {subject} --no-sub
    """
    runBash(cmd)


def runFastSurfer(bids_dir: Path, derivs_dir: Path, code_dir: Path, fastsurfer_img: str, subject: str):
    """
    Run FastSurfer on T1 image.

    Documentation:
    https://github.com/Deep-MI/FastSurfer
    """
    print("\n    STEP: FastSurfer\n")
    out_dir = derivs_dir / "fastsurfer"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    license_found, license_file = checkFSlicense()

    cmd = f"""
    docker run --rm \
        -v {bids_dir}:/data \
        -v {derivs_dir}/fastsurfer:/output \
        -v {code_dir}/fastsurfer_src/{license_file}:/fs60/{license_file} \
        {fastsurfer_img} \
        --fs_license /fs60/{license_file} \
        --t1 /data/{subject}/anat/{subject}_T1w.nii.gz \
        --sid {subject} \
        --sd /output \
        --no_cuda \
        --parallel
    """

    if license_found == 0:
        runBash(cmd)
    elif license_found == 1:
        print("    WARNING: Skipping FastSurfer")

    return license_found


def runQAtools(derivs_dir: Path, qatools_img: str, subject: str, license_found: int):
    """
    Run QAtools to produce QC output.
    Output is generated in each participants fastsurfer output directory
    - screenshots for quick visual QC
    - qatools-results.csv includes QC metrics (may be some overlap with MRIQC)
    that can be used for QC of FastSurfer output

    Documentation:
    https://github.com/Deep-MI/qatools-python
    """
    print("\n    STEP: FastSurfer QC")
    if license_found == 0:
        try:
            cmd = f"""
            docker run --rm \
                -v {derivs_dir}:/home \
                {qatools_img} python3 /opt/qatools/qatools.py \
                --subjects_dir /home/fastsurfer \
                --output_dir /home/fastsurfer/{subject} \
                --subjects {subject} \
                --screenshots \
                --fastsurfer
            """
            runBash(cmd)
        except FileNotFoundError:
            print(f"    ERROR: FastSurfer output does not exist for {subject}")
    elif license_found == 1:
        print("\n    WARNING: Skipping FastSurfer QC")


def runDeepBrainNet(derivs_dir: Path, bids_dir: Path, code_dir: Path, deepbrainnet_img: str, subject: str):
    """
    Run DeepBrainNet for brain age prediction.

    Code adapted from:
    https://github.com/vishnubashyam/DeepBrainNet
    Citation:
    https://academic.oup.com/brain/article/143/7/2312/5863667?login=true
    """
    print("\n    STEP: DeepBrainNet\n")

    out_dir = derivs_dir / "deep-brain-net"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = f"""
    docker run --rm \
        -v {bids_dir}:/home/input \
        -v {derivs_dir}/deep-brain-net:/home/output \
        -v {code_dir}/deep-brain-net_src:/home/code \
        {deepbrainnet_img} bash /home/code/run_prediction.sh {subject}
    """
    runBash(cmd)


# --- RUN PREPROCESS ---


# BIDS-ify subject code
bids_subject = "sub-" + str(subject).replace("_", "")

printParameters()
runDcm2BIDS(dicom_dir, bids_dir, code_dir, heudiconv_img, subject)
runMRIQC(bids_dir, mriqc_img, bids_subject)
license_found = runFastSurfer(
    bids_dir, derivs_dir, code_dir, fastsurfer_img, bids_subject)
runQAtools(derivs_dir, qatools_img, bids_subject, license_found)
runDeepBrainNet(derivs_dir, bids_dir, code_dir, deepbrainnet_img, bids_subject)

print("\n----- FINISHED -----\n")
