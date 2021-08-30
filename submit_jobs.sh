#!/bin/sh

#--- Schedular parameters

pbs_name="MRprep"
pbs_walltime="walltime=02:00:00"
pbs_cpu="ncpus=25"
pbs_ram="mem=16GB"
pbs_queue="P_queue"
pbs_mailto="pembleto@usc.edu.au"
pbs_stdout="/mnt/HPCcache/private/pembleto1i"

#--- Set up the environment

base_dir="/project/RDS-FSC-HBA-RW/Jake/testing"
code_dir="${base_dir}/TI-HBA-MRprep"
dicom_dir="${base_dir}/dicom" # Copy dicoms to here
bids_dir="${base_dir}/bids" # This will be the organised files
derivatives_dir="${base_dir}/derivatives" # Pipeline outputs
singularity_dir="${base_dir}/containers" # Where the singularity containers are
freesurfer_license="${code_dir}/license.txt" # Where the freesurfer license is

#--- Submit jobs

cd ${dicom_dir} || exit

for subject in HBA_*; do
    qsub \
        -N $pbs_name \
        -l $pbs_walltime \
        -l $pbs_cpu \
        -l $pbs_ram \
        -q $pbs_queue \
        -M $pbs_mailto \
        -m abe \
        -o $pbs_stdout \
        -j eo -- python3 ${code_dir}/run_pipeline.py \
                    --subject ${subject} \
                    --license ${freesurfer_license} \
                    --base ${base_dir} \
                    --code ${code_dir} \
                    --dicom ${dicom_dir} \
                    --bids ${bids_dir} \
                    --derivs ${derivatives_dir} \
                    --singularity_dir ${singularity_dir}
done
