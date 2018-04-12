#!/usr/bin/env python

import pathlib
import pandas as pd

DATA_DIR = (pathlib.Path(__file__).parent.parent / 'PPMI').resolve()
BAD_SCANS = pd.read_csv((DATA_DIR / 'sessions.txt').resolve())


def prep_for_heudiconv(subj_dir, timeout=None):
    """
    Reorganizes `subj_dir` to structure more compatible with ``heudiconv``

    PPMI data starts off with a sub-directory structure that is not conducive
    to use with ```heudiconv``. By default, scans are grouped by scan type
    rather than by session, and there are a number of redundant sub-directories
    that we don't need. This script reorganizes the data, moving things around
    so that the general hierarchy is {subject}/{session}/{scan}, which makes
    for a much easier time converting to NIFTI (BIDS) format.

    An added complication is that a minority of the scans in the PPMI database
    are "bad" to some degree. For most, it is likely that there was some issue
    with exporting/uploading the DICOM files. For others, the conversion
    process we intend to utilize (``heudiconv`` and ``dcm2niix``) fails to
    appropriately convert the files due to some idiosyncratic reason that could
    be fixed but we don't have the patience to fix at the current juncture.
    Nonetheless, these scans need to be removed so that we can run the batch of
    subjects through ``heudiconv`` without any abrupt failures. These scans are
    moved to the `timeout` directory if provided. Otherwise, they are retained
    (but BE WARNED).

    Parameters
    ----------
    subj_dir : str or pathlib.Path
        Path to subject directory as downloaded from ppmi-info.org
    timeout : str or pathlib.Path, optional
        If set, path to directory where bad scans should be moved. Default:
        None
    """

    # coerce subj_dir to path object
    if isinstance(subj_dir, str):
        subj_dir = pathlib.Path(subj_dir).resolve()

    # get all scan types for subject
    scans = [f for f in subj_dir.glob('*') if not f.name.isdigit()]

    # if subject was previously converted update number structure correctly
    prev = len([f for f in subj_dir.glob('*') if f.name.isdigit()])

    # get all sessions for subject (session = same day)
    sessions = sorted(set([v.name[:7] for v in
                           subj_dir.rglob('????-??-??_??_??_??.?')]))

    # iterate through sessions and copy scans to uniform directory structure
    for n, ses in enumerate(sessions, prev + 1):
        # make session directory
        ses_dir = subj_dir / f'{n}'
        ses_dir.mkdir(exist_ok=True)

        # iterate through all scans for a given session (visit) and move
        for scan_type in subj_dir.glob(f'*/{ses}*/*'):
            # idk why this would be but check just in case????
            if not scan_type.is_dir():
                continue

            # if this is a bad scan, move it to `timeout`
            if scan_type.name in BAD_SCANS.scan.values and timeout is not None:
                dest = timeout / subj_dir.name / ses_dir.name
                dest.mkdir(parents=True, exist_ok=True)
                scan_type.rename(dest / scan_type.name)
                continue

            # oterhwise, move it to the appropriate scan directory
            scan_type.rename(ses_dir / scan_type.name)
            # if there are no more scans in the parent directory, remove it
            remain = [f for f in scan_type.parent.glob('*') if f != scan_type]
            if len(remain) == 0:
                scan_type.parent.rmdir()

    # remove empty directories
    for scan in scans:
        scan.rmdir()


if __name__ == '__main__':
    # create the `timeout` directory for bad scans
    timeout = DATA_DIR / 'bad'
    timeout.mkdir()

    # get all the subjects in the data directory and prepare for heudiconv
    for subj_dir in sorted(DATA_DIR.glob('*')):
        if not subj_dir.is_dir(): continue
        prep_for_heudiconv(subj_dir, timeout=timeout)

    # rename PPMI to data
    DATA_DIR.rename(DATA_DIR.parent / 'raw')
