#!/usr/bin/env bash
#
# This script is designed to convert a raw PPMI datasets (ppmi-info.org) into
# BIDS format (bids.neuroimaging.io)
#
# To run this conversion, you will need to have downloaded DICOMS from the PPMI
# website and unzipped them into a directory next to this one. Moreover, you
# will need Python 3.5 or higher (with the pandas library), and Singularity
# (http://singularity.lbl.gov) installed on your local computer.
#
# Once you have all those programs installed, you should be able to run this
# script (assuming you are using a POSIX system or something that can run bash
# commands). Once this is started, you should probably head to lunch --- the
# conversion process takes a long while. After it's done, check the "data"
# directory for a (hopefully) fully-functional BIDS dataset.
#

# get directory of this script and make sure PPMI directory exists
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
parent_dir="$( dirname "${script_dir}" )"
if [ ! -d "${parent_dir}/PPMI" ]; then
    echo "The PPMI dataset (or this script?) doesn't seem to be in the right "
    echo "location. Please check that everything is in the right place and "
    echo "try again!"
    exit 1
fi

# copy bad sessions text file into raw PPMI directory
# this prevents heudiconv from trying to convert bad sessions that would cause
# it to crash (due to the DICOMS being corrupted / bad / malformed)
cp "${script_dir}/sessions.txt" "${parent_dir}/PPMI/sessions.txt"

# run ppmi_prep_heudiconv.py
# converts PPMI directory as downloaded from PPMI website into better structure
python "${script_dir}/ppmi_prep_heudiconv.py"

# create output directory for PPMI BIDS dataset, if it doesn't exist
mkdir -p "${parent_dir}/data"

# now, copy heudiconv heuristic that will map raw DICOMs to BIDS format
cp "${script_dir}/ppmi_heuristic.py" "${parent_dir}/raw/ppmi_heuristic.py"

# get all the subjects in the PPMI folder that we'll need to run
subjects=$( find "${parent_dir}/raw" -maxdepth 1                              \
                                     -type d                                  \
                                     -name "????"                             \
                                     -exec basename {} \; | sort )

# run heudiconv on the PPMI dataset
for sess in 1 2 3 4 5; do
    singularity run -B "${parent_dir}/data:/out"                              \
                    -B "${parent_dir}/raw:/data"                              \
                    "${script_dir}/heudiconv.simg"                            \
                    -d /data/{subject}/{session}/*/*dcm                       \
                    -s "${subjects}" -ss "${sess}"                            \
                    --outdir /out                                             \
                    --heuristic /data/ppmi_heuristic.py                       \
                    --converter dcm2niix --bids --minmeta
done
