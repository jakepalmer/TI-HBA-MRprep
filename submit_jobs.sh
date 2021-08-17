#!/bin/sh

#--- Schedular parameters

# pbs_name="MRprep"
# pbs_walltime="walltime=02:00:00"
# pbs_cpu="ncpus=25"
# pbs_ram="mem=16GB"
# pbs_queue="P_queue"
# pbs_mailto="pembleto@usc.edu.au"
# pbs_stdout="/mnt/HPCcache/private/pembleto1i"

#--- Set up the environment

base_dir="/Users/mq44848301/Desktop/usc_mri"
code_dir="${base_dir}/TI-HBA-MRprep"
dicom_dir="${base_dir}/dicom" # Copy dicomes to here
bids_dir="${base_dir}/bids" # This will be the organised files
derivatives_dir="${base_dir}/derivatives" # Pipeline outputs
singularity_dir="/mnt/singularity" # Where the container files are

#--- Submit jobs

cd ${dicom_dir} || exit

### For testing with docker on local ###
for subject in HBA_*; do
    python3 ${code_dir}/run_pipeline.py \
        --subject ${subject} \
        --base ${base_dir} \
        --code ${code_dir} \
        --dicom ${dicom_dir} \
        --bids ${bids_dir} \
        --derivs ${derivatives_dir} \
        --singularity_dir ${singularity_dir}
done

### For HPC ###
# for subject in HBA_*; do
#     qsub \
#         -N $pbs_name \
#         -l $pbs_walltime \
#         -l $pbs_cpu \
#         -l $pbs_ram \
#         -q $pbs_queue \
#         -M $pbs_mailto \
#         -m abe \
#         -o $pbs_stdout \
#         -j eo -- python3 ${code_dir}/run_pipeline.py \
#                     --subject ${subject} \
#                     --base ${base_dir} \
#                     --code ${code_dir} \
#                     --dicom ${dicom_dir} \
#                     --bids ${bids_dir} \
#                     --derivs ${derivatives_dir} \
#                     --singularity_dir ${singularity_dir}
# done