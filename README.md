# TI HBA MR Preprocessing

This is a basic preprocessing pipeline for MRI data from the Healthy Brain Ageing Clinic at the Thompson Institute, USC.

## Pipeline overview

These are the steps of the pipeline. These steps are explained in more detail below, along with links to helpful resources/documentation and citations.

1. Dicoms are converted to a BIDS compliant dataset with HeuDiConv.
2. Automatic QC for the T1-weighted scan using MRIQC.
3. Subcortical segmentation and cortical parcellation with FastSurfer (includes QC).
4. Brain age prediction with DeepBrainNet.
5. WMH segmentation with FSL's BIANCA.
6. DWI preprocessing with QSIprep.
7. rsfMRI preprocessing with fMRIprep.

Each of these steps should be cited appropriately if used in publication (citations included below).

### Ideas behind implementation

The pipeline was developed with the following ideas in mind:

- `submit_jobs.sh` orchestrates the pipeline by submitting a job on the HPC for each participant. For regular use, this is the only file that should need editing, e.g. editing paths and PBS parameters.
- `run_pipeline.py` includes the main processing pipeline and simply wraps the Singularity commands for each step.
- Each step is implemented in its own container on the HPC. Containers can be built from Dockerfile/Singularity files in the `*_src` folders or from published containters (noted in each section below).

To setup it requires building multiple containers, but the idea was for this pipeline to remain 'modular' so that each processing step is independent and can be modified/removed without affecting the rest of the pipeline (with the exception of dicom to BIDS conversion being required for all subsequent steps). Similarly, the pipeline can be extended by adding a container, processing script/command and a function in the `run_pipeline.py` script.

## Assumed input file structure

The pipeline takes dicoms as its input with the assumed file structure before processing being:

```bash
├── bids
├── derivatives
├── dicom
    ├── HBA_0001_T1
        ├── RESEARCH_PROTOCOLS_*
            ├── AAHEAD_SCOUT_64CH_HEAD_COIL_*
            ├── MPRAGE_*
            ├── EP2D_DIFF_QBALL96DIR_*
            ...
    ├── HBA_0002_T1
        ├── RESEARCH_PROTOCOLS_*
            ├── AAHEAD_SCOUT_64CH_HEAD_COIL_*
            ├── MPRAGE_*
            ├── EP2D_DIFF_QBALL96DIR_*
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
cd /path/on/HPC
source submit_jobs.sh
```

...where `/path/on/HPC` is the appropriate path to the data and code on the HPC.

## Detailed processing steps

> **NOTE:** FastSurfer, QSIprep and fMRIprep require a FreeSurfer license, which can be obtained for free from [here](https://surfer.nmr.mgh.harvard.edu/fswiki/License). The file needs to be passed to the `submit_jobs.sh` script.

### Dicom to BIDS

BIDS is a standard for structuring neuroimaging datasets that is being increasingly implemented that allows a consistent interface and documentation of datasets. A number of open source pipelines expect input to be in BIDS format.

HeuDiConv has been developed to automate the conversion from dicom to BIDS. It requires some setup (i.e. putting together a `heuristic.py` file to provide the rules for conversion), however this will generally only need to be setup once and has been done (see `heudiconv_src/heuristic.py`). This would need updating if the MRI sequences change. Example commands to help with the setup are included in the comments in the docstring for the `runDcm2BIDS` function in the `run_pipeline.py` file.

For more info see [BIDS](https://bids.neuroimaging.io/) and [HeuDiConv](https://heudiconv.readthedocs.io/en/latest/) documentation, also this HeuDiConv [walkthrough](https://reproducibility.stanford.edu/bids-tutorial-series-part-2a/) and [wiki](https://github.com/bids-standard/bids-starter-kit/wiki/). The HeuDiConv [container](https://heudiconv.readthedocs.io/en/latest/installation.html#docker).

### MRIQC

This is an automated QC pipeline for T1-weighted, T2-weighted and fMRI sequences (if present in BIDS folder). It produces visual reports and a range of QC metrics that may be useful for further analysis.

See [documentation](https://mriqc.readthedocs.io/en/stable/), [citation](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0184661) and the [container](https://hub.docker.com/r/poldracklab/mriqc/).

### FastSurfer

FastSurfer is a deep learning implementation of FreeSurfer. It provides essentially the same output but is faster (as you may have guessed) and more accurate.

See the [documentation](https://deep-mi.org/research/fastsurfer/), [citation](https://www.sciencedirect.com/science/article/pii/S1053811920304985) and the [github](https://github.com/Deep-MI/FastSurfer) which also includes [Dockerfiles](https://github.com/Deep-MI/FastSurfer/tree/master/Docker).

#### FastSurfer QC

This is just a quick visual QC step for the output of FastSurfer and is run automatically. It produces a CSV file with some QC metrics (some of which overlap with MRIQC) and screenshots to check the segmentation and cortical parcellation.

This is only designed for quick, preliminary visual QC and full visual QC should be completed before any statistical analysis for publication (see [here](https://www.sciencedirect.com/science/article/pii/S1053811921004511) for discussion of QC approaches).

See the [documentation](https://github.com/Deep-MI/qatools-python).

### DeepBrainNet

This is a deep learning model developed for the prediction of brain age. It produces a single predicted age based on the T1-weighted input, which can then be used to calculate a difference score with chronological age.

The model has been implemented in [ANTsPyNet](https://antsx.github.io/ANTsPyNet/docs/build/html/utilities.html), including the preprocessing steps, which is used in `deep-brain-net_src/run_prediction.py`. The Dockerfile/Singularity file is also included in the `deep-brain-net_src` folder.

See the [citation](https://academic.oup.com/brain/article/143/7/2312/5863667?login=true) for more info about the model development and interpretation and original [code](https://github.com/vishnubashyam/DeepBrainNet) from authors.

### WMH segmentation with BIANCA

BIANCA requires some pre/post processing. The steps used are:

- Preprocess T1 and FLAIR with `fsl_anat` (see [docs](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/fsl_anat))
- Create a white matter mask with `make_bianca_mask` (see BIANCA [docs](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BIANCA/Userguide#Data_preparation))
- Create `masterfile.txt` as input for BIANCA
- The BIANCA output is a probability image, so apply thresholding (default to 0.9 here)
- Extract the total WMH number and volume'

BIANCA also requires some manually labeled WMH masks as training data. A recent [paper](https://www.sciencedirect.com/science/article/pii/S1053811921004663?via%3Dihub#bib0013) suggested the use of consistent training labels may be beneficial to avoid inter-rater variability between manual segmentations. Currently, this pipeline makes use of manual segmentations provided by those authors (included in container) for the training labels. This could be changed in future if a sample of HBA participants were manually segmented.

BIANCA [documentation](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BIANCA/Userguide#Data_preparation), [tutorial](https://fsl.fmrib.ox.ac.uk/fslcourse/lectures/practicals/seg_struc/#bianca) and [citation](https://www.sciencedirect.com/science/article/pii/S1053811916303251?via%3Dihub), as well as the [citation](https://www.sciencedirect.com/science/article/pii/S1053811921004663?via%3Dihub#bib0013) and discussion for training labels that can be found [here](https://issues.dpuk.org/eugeneduff/wmh_harmonisation/-/tree/master/BIANCA_training_datasets).

### QSIprep

> **IMPORTANT:** This step has not been tested extensively. The defaults have been used for almost all options, however these should be checked before using this data in any further analysis.

QSIprep is a BIDS app that runs preprocessing and reconstruction of DWI data. Only preprocessing is completed here but QSIprep is also an excellent tool to use for further analysis. Visual QC reports are also produced which provide and easy way to check the quality of the DWI data.

QSIprep utilises a number of software packages that should be references (as well as the QSIprep citation). Example citation information with references in produced as part of processing and can be found in the `logs` folder of the output.

Some steps in QSIprep (particularly eddy current correction and disortion correction with TOPUP) are resource intensive. Currently the pipeline is set to allow QSIprep's underlying workflow manager ([Nipype](https://nipype.readthedocs.io/en/latest/#)) to manage the CPU and RAM usage by detecting how many CPUs are available and using 90% of available RAM (see MultiProc section [here](https://miykael.github.io/nipype_tutorial/notebooks/basic_plugins.html)).

[Documentation](https://qsiprep.readthedocs.io/en/latest/index.html), [citation](https://www.nature.com/articles/s41592-021-01185-5), Docker [image](https://hub.docker.com/r/pennbbl/qsiprep/) and info for using with [Singularity](https://qsiprep.readthedocs.io/en/latest/installation.html#singularity-container).

### fMRIprep

> **IMPORTANT:** This step has not been tested extensively. The defaults have been used for almost all options, however these should be checked before using this data in any further analysis.

fMRIprep is another BIDS app for preprocessing fMRI data. As for QSIprep, fMRIprep uses several software packages that should also be referenced. Visual QC reports are also produced.

[Documentation](https://fmriprep.org/en/latest/index.html), [citation](https://www.nature.com/articles/s41592-018-0235-4), Docker [image](https://hub.docker.com/r/nipreps/fmriprep) and info for using with [Singularity](https://fmriprep.org/en/latest/installation.html#containerized-execution-docker-and-singularity).
