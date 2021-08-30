import ants
import antspynet as ap
import csv
from pathlib import Path
from argparse import ArgumentParser

# Get command line input
parser = ArgumentParser("Workflow inputs")
parser.add_argument("--subject", type=str, required=True)
args = parser.parse_args()
subject = str(args.subject)

if __name__ == "__main__":
    # Read in T1 image
    image = ants.image_read(f"/tmp/input/{subject}/anat/{subject}_T1w.nii.gz")

    # Run prediction
    prediction = ap.brain_age(image, do_preprocessing=True, verbose=True)

    # Write output
    fields = ["ID", "Predicted_Age"]
    rows = [[subject, prediction["predicted_age"]]]
    collated_file = Path("/tmp/output/predicted_age_collated.csv")

    with open(f"/tmp/output/{subject}_predicted_age.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        writer.writerows(rows)

    if collated_file.is_file():
        with open(collated_file, "a+") as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    else:
        with open(collated_file, "w") as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            writer.writerows(rows)
