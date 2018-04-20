# PPMItoBIDS
The code and software contained herein is designed to convert neuroimaging data from the Parkinon Progression Markers Initiative ([PPMI](http://www.ppmi-info.org)) into [BIDS](bids.neuroimaging.io) format.

## Prerequisites
* Python 3.5 (or higher) with [pandas](https://pypi.org/project/pandas/) installed
* [Singularity](http://singularity.lbl.gov) 2.4 (or higher)

## Instructions
1. Download raw DICOM data from the [PPMI website](http://www.ppmi-info.org/access-data-specimens/download-data/) and unzip it into the `PPMI` folder. The organization of the `PPMI` directory should look something like:
    ```
    └── PPMI/
        ├── 3000/
        |   ├── scan_type_1/                        (e.g., MPRAGE_GRAPPA)
        |   |   ├── 2014-03-10_10_25_03.0/
        |   |   |   └── SXXXXXX/
        |   |   |       └── *dcm
        |   |   └── 2015-04-04_09_58_25.0/
        |   ├── scan_type_2/                        (e.g., AX_FLAIR)
        |   |   ├── 2014-03-10_10_34_42.0/
        |   |   └── 2015-04-04_10_05_31.0/
        |   ├── .../
        |   └── scan_type_N/
        ├── 3001/
        ├── .../
        └── NNNN/
    ```
    That is, subjects should each get their own directory (3000, 3001, ..., NNNN). Within each subject directory there should be a unique directory for each scan type and, within those, a directory for each visit. This is the default layout that occurs if you download DICOM data from the PPMI website, so *you shouldn't have to do any re-organizing!*

2. Download [this](https://bit.ly/2qplVES) Singularity container with the correct versions of the conversion software and place it in the `code` directory.

3. Run `bash code/run_conversion.sh` and go to lunch. Check out the docstring at the top of that script for more info on what it does. However, briefly, it uses `code/ppmi_prep_heudiconv.py` to do some light reorganizing of the downloaded PPMI data and then runs [`heudiconv`](https://github.com/nipy/heudiconv) to convert the DICOM data to BIDS format, using `code/ppmi_heuristic.py` to map the raw DICOM series to BIDS-compatible names. The output BIDS data should be in the `data` directory.

4. Use the organized PPMI BIDS dataset located in `data` for analyses!
