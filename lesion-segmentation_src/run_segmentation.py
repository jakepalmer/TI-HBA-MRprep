import subprocess
import shutil
import csv
from argparse import ArgumentParser
from pathlib import Path


# Get command line input
parser = ArgumentParser("Workflow inputs")
parser.add_argument("--subject", type=str, required=True)
args = parser.parse_args()
subject = str(args.subject)

# Make outdir
outdir = f"/tmp/output/{subject}"
Path(outdir).mkdir(parents=True, exist_ok=True)


# --- FUNCTIONS ---


def runBash(cmd):
    """
    Wrapper for command line.
    """
    print(f"    COMMAND: {cmd}")
    subprocess.check_call(cmd, shell=True)


def runPreprocess(subject, outdir):
    """
    Preprocess input scans
    """
    Path(f"{outdir}/t1").mkdir(parents=True, exist_ok=True)
    cmd_t1_anat = f"""
                fsl_anat \
                    -i /tmp/input/{subject}/anat/{subject}_T1w.nii.gz \
                    -o {outdir}/t1 \
                    -t T1
            """
    Path(f"{outdir}/flair").mkdir(parents=True, exist_ok=True)
    cmd_flair_anat = f"""
                fsl_anat \
                    -i /tmp/input/{subject}/anat/{subject}_FLAIR.nii.gz \
                    -o {outdir}/flair \
                    -t T2 \
                    --nononlinreg \
                    --nosubcortseg \
                    --noseg
            """
    cmd_bianca_mask = f"""
            make_bianca_mask \
                {outdir}/t1.anat/T1_biascorr \
                {outdir}/t1.anat/T1_fast_pve_0.nii.gz \
                {outdir}/t1.anat/MNI_to_T1_nonlin_field.nii.gz
            """
    runBash(cmd_t1_anat)
    runBash(cmd_flair_anat)
    runBash(cmd_bianca_mask)


def runMasking(outdir):
    """
    Copy required preprocessed files to outdir and create the
    FLAIR masks (brain and white matter)
    """
    shutil.copy(
        str(f"{outdir}/t1.anat/T1_biascorr_brain.nii.gz"),
        str(f"{outdir}/t1_biascorr_brain.nii.gz")
    )
    shutil.copy(
        str(f"{outdir}/t1.anat/T1_biascorr_bianca_mask.nii.gz"),
        str(f"{outdir}/t1_biascorr_bianca_mask.nii.gz")
    )
    shutil.copy(
        str(f"{outdir}/t1.anat/T1_biascorr_brain_mask.nii.gz"),
        str(f"{outdir}/t1_biascorr_brain_mask.nii.gz")
    )
    shutil.copy(
        str(f"{outdir}/flair.anat/T2_biascorr.nii.gz"),
        str(f"{outdir}/flair_biascorr.nii.gz")
    )
    shutil.copy(
        str(f"{outdir}/flair.anat/T2_orig2std.mat"),
        str(f"{outdir}/flair2std.mat")
    )
    cmd_mask_brain = f"fslmaths {outdir}/flair_biascorr.nii.gz -mas {outdir}/t1_biascorr_brain_mask.nii.gz {outdir}/flair_biascorr_brain.nii.gz"
    cmd_mask_wm = f"fslmaths {outdir}/flair_biascorr.nii.gz -mas {outdir}/t1_biascorr_bianca_mask.nii.gz {outdir}/flair_biascorr_wm.nii.gz"
    runBash(cmd_mask_brain)
    runBash(cmd_mask_wm)


def runMakeMasterfile(outdir):
    """
    Generate the master file required for BIANCA.
    """
    row = [f"{outdir}/flair_biascorr_wm.nii.gz",
           f"{outdir}/t1_biascorr_brain.nii.gz",
           f"{outdir}/flair2std.mat"]
    mfile = open(f"{outdir}/masterfile.txt", "w")
    for element in row:
        mfile.write(element + " ")
    mfile.close()


def runBIANCA(outdir, thr):
    cmd_bianca = f"""
    bianca \
        --singlefile={outdir}/masterfile.txt \
        --querysubjectnum=1 \
        --brainmaskfeaturenum=1 \
        --featuresubset=1,2 \
        --matfeaturenum=3 \
        --spatialweight=2 \
        --patchsizes=3 \
        --loadclassifierdata=/opt/wmh_harmonisation/BIANCA_training_datasets/Mixed_WH-UKB_FLAIR_T1 \
        -o {outdir}/wmh_mask_prob.nii.gz –v
    """
    runBash(cmd_bianca)
    for t in thr:
        cmd = f"fslmaths {outdir}/wmh_mask_prob.nii.gz -thr {t} -bin {outdir}/wmh_mask_bin{t}.nii.gz"
        runBash(cmd)


def runBIANCAstats(outdir, thr, min_vox, subject):
    for t in thr:
        cmd = f"bianca_cluster_stats {outdir}/wmh_mask_prob.nii.gz {t} {min_vox} > {outdir}/wmh_mask_bin{t}_stats.txt"
        runBash(cmd)

        # Collate stats
        fields = ["ID", "probability_threshold_used",
                  "min_cluster_size_used", "WMH_number", "WMH_volume"]
        collated_file = Path("/tmp/output/WMHstats_collated.csv")

        with open(f"{outdir}/wmh_mask_bin{t}_stats.txt") as f:
            lines = f.readlines()
            for line in lines:
                l = line.rstrip().split(" ")
                if "number" in l:
                    n = l[-1]
                elif "volume" in l:
                    v = l[-1]
            row = [[subject, t, min_vox, n, v]]
            if collated_file.is_file():
                with open(collated_file, "a+") as file:
                    writer = csv.writer(file)
                    writer.writerows(row)
            else:
                with open(collated_file, "w") as file:
                    writer = csv.writer(file)
                    writer.writerow(fields)
                    writer.writerows(row)


def tidy(outdir):
    shutil.rmtree(f"{outdir}/t1")
    shutil.rmtree(f"{outdir}/t1.anat")
    shutil.rmtree(f"{outdir}/flair")
    shutil.rmtree(f"{outdir}/flair.anat")


# --- MAIN ROUTINE ---


# Probability threshold and minimum cluster size
# for BIANCA output (can include multiple thresholds)
thr = [0.9]
min_vox = 5

if __name__ == "__main__":
    runPreprocess(subject, outdir)
    runMasking(outdir)
    runMakeMasterfile(outdir)
    runBIANCA(outdir, thr)
    runBIANCAstats(outdir, thr, min_vox, subject)
    tidy(outdir)
