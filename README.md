# TI HBA MR Preprocessing

This is a basic preprocessing pipeline for MRI data from the Thompson Institute, USC.

## Pipeline overview

These are the steps of the pipeline. These steps are explained in more detail below, along with links to helpful resources/documentation and citations.

1. Dicoms are converted to a BIDS compliant dataset with HeuDiConv.
2. Automatic QC for the T1-weighted scan using MRIQC.
3. Subcortical segmentation and cortical parcellation with FastSurfer.
4. FastSurfer QC with QA tools.
5. Brain age prediction with DeepBrainNet

Each of these steps should be cited appropriately if used in publication (citations included below)

### Ideas behind implementation

The pipeline was developed with the following ideas in mind:

- `submit_jobs.sh` orchestrates the pipeline by submitting a job on the HPC for each participant. For regular use, this is the only file that should need editing, e.g. editing paths and PBS parameters.
- `run_pipeline.py` includes the main processing pipeline and simply wraps the Singularity commands for each step.
- Each step is implemented in its own container on the HPC. Singularity containers can be built from Dockerfiles in the `*_src` folders or from published containters (e.g. MRIQC).

Currently, the pipeline only includes processing of T1-weight images, however it should be reasonably straight forward to extend the pipeline for other scan types by adding functions with Singularity commands in the `run_pipeline.py` script. Some recomended options are [QSIprep](https://qsiprep.readthedocs.io/en/latest/index.html) for DWI and [fMRIPrep](https://fmriprep.org/en/stable/) for fMRI.

## Assumed input file structure

The pipeline takes dicoms as its input with the assumed file structure before processing being:

```bash
├── bids
├── derivatives
├── dicom
    ├── HBA_0001_T1
        ├── RESEARCH_PROTOCOLS
            ├── T1
            ├── FLAIR
            ...
    ├── HBA_0002_T1
        ├── RESEARCH_PROTOCOLS
            ├── T1
            ├── FLAIR
            ...
    ...
├── TI-HBA-MRprep
```

Where...

- `dicom` = where the dicoms will be copied for each participant to be processed
- `bids` = the BIDS compliant data converted from `dicom`
- `derivatives` = the pipeline outputs
- `TI-HBA-MRprep` = the code in this repository

## Intended usage

1. Make sure directory structure exists as shown [above](##Assumed-input-file-structure) in the analysis directory on the HPC.
2. Clone this repo and move to the HPC.
3. Copy dicoms to process into the `dicom` directory.
4. Update/check the schedular parameters in `submit_jobs.sh`. It might take some testing to get these right, afterwhich they most likely won't need to be changed often.
5. Update/check the file paths in `submit_jobs.sh`
6. When ready to run the pipeline, type the following in terminal:

```bash
cd /path/to/data/on/HPC
source submit_jobs.sh
```

...where `/path/to/data/on/HPC` is the appropriate path to the data and code on the HPC.

## Detailed processing steps

### Dicom to BIDS

BIDS is an international standard for structuring neuroimaging datasets that is being increasingly implemented that allows a consistent interface and documentation of datasets. A number of open source pipelines expect input to be in BIDS format.

HeuDiConv has been developed to automate the conversion from dicom to BIDS. It requires some setup (i.e. putting together a `heuristic.py` file to provide the rules for conversion), however this will generally only need to be setup once or when the actual MRI sequences change. Example commands to help with the setup are included in the comments in the docstring for the `runDcm2BIDS` function in the `run_pipeline.py` file.

For more info see [BIDS](https://bids.neuroimaging.io/) and [HeuDiConv](https://heudiconv.readthedocs.io/en/latest/) documentation, also this HeuDiConv [walkthrough](https://reproducibility.stanford.edu/bids-tutorial-series-part-2a/) and [wiki](https://github.com/bids-standard/bids-starter-kit/wiki/).

### MRIQC

This is an automated QC pipeline for T1-weighted scans. It produces visual reports and a range of QC metrics that may be useful for further analysis.

See [documentation](https://mriqc.readthedocs.io/en/stable/), [citation](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0184661) and the [container](https://hub.docker.com/r/poldracklab/mriqc/).

### FastSurfer

FastSurfer is a recently developed deep learning implementation of FreeSurfer. It provides essentially the same output but is faster (as you may have guessed) and more accurate.

**NOTE:** FastSurfer requires a FreeSurfer license, which can be obtained for free from [here](https://surfer.nmr.mgh.harvard.edu/fswiki/License) and should be placed in the `fastsurfer_src` directory and include 'license' somewhere in the file name.

See the [documentation](https://deep-mi.org/research/fastsurfer/), [citation](https://www.sciencedirect.com/science/article/pii/S1053811920304985) and the [github](https://github.com/Deep-MI/FastSurfer) which also includes [Dockerfiles](https://github.com/Deep-MI/FastSurfer/tree/master/Docker).

### QA tools

This is just a quick visual QC step for the output of FastSurfer. It produces a CSV file with some QC metrics (some of which overlap with MRIQC) and screenshots to check the segmentation and cortical parcellation.

This is only designed for quick, preliminary visual QC and full visual QC should be completed before any statistical analysis for publication (see [here](https://www.sciencedirect.com/science/article/pii/S1053811921004511) for discussion of QC approaches).

See the [documentation](https://github.com/Deep-MI/qatools-python).

### DeepBrainNet

This is a deep learning model developed for the prediction of brain age. It produces a single predicted age based on the T1-weighted input, which can then be used to calculate a difference score with chronological age.

It requires brain extraction and linear registration to a template. [ANTs](http://stnava.github.io/ANTs/) is used for these steps.

The code is made available on [Github](https://github.com/vishnubashyam/DeepBrainNet), however not much information is provided here on how to implement the model. Therefore, the `deep-brain-net_src` directory in this repository includes the required scripts from the authors as well as some additional code to run the model:

- `Model_Test.py` and `Slicer.py` supplied by the [authors](https://github.com/vishnubashyam/DeepBrainNet)
- `neurodocker.sh` includes the [Neurodocker](https://hub.docker.com/r/repronim/neurodocker/) command used to generate the `Dockerfile`, which can be used to build a Singularity container.
- `run_prediction.sh` includes the brain extraction and registration with ANTs to prepare the scan for the model

See the [citation](https://academic.oup.com/brain/article/143/7/2312/5863667?login=true) for more info about the model development and interpretation.
