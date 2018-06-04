#!/usr/bin/env python

import glob
import itertools
import logging
from os.path import abspath, dirname, basename, join as pjoin
import re

from nilearn.input_data import NiftiLabelsMasker, NiftiMapsMasker
from nilearn.input_data.nifti_masker import BaseMasker
from nilearn._utils import check_niimg
import numpy as np
import pandas as pd

PROJ_DIR = dirname(dirname(abspath(__file__)))
DERIV_DIR = pjoin(PROJ_DIR, 'derivatives', 'antsclt')
REGEX = re.compile('sub-(\d+)_ses-(\d+)')

SUB_MASK = pjoin(PROJ_DIR, 'code', 'atlas-Pauli2018_'
                                   'space-MNI152NLin2009cAsym_'
                                   'hemi-split_probabilistic.nii.gz')
COR_MASK = pjoin(PROJ_DIR, 'code', 'atlas-Cammoun2012_'
                                   'space-MNI152NLin2009aSym_'
                                   'scale-500_deterministic.nii.gz')

logging.basicConfig(format='[%(levelname)s]: ++ %(message)s',
                    level=logging.INFO)


def get_data(subj, mask, sessions=None, dtype='jacobian'):
    """
    Parameters
    ----------
    subj : (N,) list of img_like
    mask : Niimg_like
    sessions : list of str


    Returns
    -------
    data : (N x M) np.ndarray
        Data extracted from ``imgs``, where ``M`` is the number of parcels in
        ``mask``
    """

    # check mask is correct
    if not isinstance(mask, BaseMasker):
        if not isinstance(mask, str):
            raise ValueError('Mask must be a mask object or filepath.')
        if 'probabilistic' in mask:
            mask = NiftiMapsMasker(mask, resampling_target='maps')
        else:
            mask = NiftiLabelsMasker(mask, resampling_target='labels')

    # only fit mask if it hasn't been fitted to save time
    if not hasattr(mask, 'maps_img_'):
        mask = mask.fit()

    # get images for supplied sessions (or all images)
    subj_dir = pjoin(DERIV_DIR, subj)
    if sessions is not None:
        imgs = list(
            itertools.chain.from_iterable(
                [glob.glob(pjoin(subj_dir, f'*_ses-{ses}_*_{dtype}.nii.gz'))
                 for ses in sorted(sessions)]
            )
        )
    else:
        imgs = sorted(glob.glob(pjoin(subj_dir, '*{dtype}.nii.gz')))

    # extract subject / session information from data (BIDS format)
    demo = np.row_stack([REGEX.findall(i) for i in imgs])
    # fit mask to data and stack across sessions
    data = np.row_stack([mask.transform(check_niimg(img, atleast_4d=True))
                         for img in imgs])
    return data, demo


def get_subjects(qc, return_record=True):
    """
    Gets good subjects / sessions from ``qc``

    Parameters
    ----------
    qc : str
        Filepath to QC information
    return_record : bool, optional
        Whether to return numpy recarray instead of ndarray

    Returns
    -------
    data : np.array
        Record array with `participant_id` and `session` fields for good data
    """

    df = pd.read_csv(qc)
    data = (df.query('seg_r1 > 1 & reg_r1 > 0')
              .dropna(subset=['seg_r1', 'reg_r1'])
              .query('session != "SST"')
              .get(['participant_id', 'session']))
    data = data.to_records(index=False) if return_record else data.get_values()

    return data


if __name__ == '__main__':
    # mask jacobians with probabilistic atlas and CT with deterministic atlas
    masks = [
        (NiftiMapsMasker(check_niimg(SUB_MASK),
                         resampling_target='maps').fit(),
         'jacobian'),
        (NiftiLabelsMasker(check_niimg(COR_MASK),
                           resampling_target='labels').fit(),
         'corticalthickness')
    ]

    # empty dictionaries to store parcellated data / demographics (subj + ses)
    data = dict(jacobian=[], corticalthickness=[])
    demo = dict(jacobian=[], corticalthickness=[])

    # iterate through subjects and mask data
    rec = get_subjects(pjoin(DERIV_DIR, 'qc.csv'), return_record=True)
    for sub in np.unique(rec.participant_id):
        logging.info('Extracting data for {}'.format(sub))
        # get all sessions for given subject
        ses = rec[rec.participant_id == sub].session
        for mask, dtype in masks:
            cdata, cdemo = get_data(sub, mask, sessions=ses, dtype=dtype)
            data[dtype].append(cdata)
            demo[dtype].append(cdemo)

    # save demographics to CSV files
    for key, val in demo.items():
        if len(val) == 0:  # don't write out empty dataframe
            continue
        df = pd.DataFrame(np.row_stack(val),
                          columns=['PARTICIPANT', 'SESSION'])
        if key == 'jacobian':
            fname = pjoin(DERIV_DIR, basename(SUB_MASK))
        else:
            fname = pjoin(DERIV_DIR, basename(COR_MASK))
        df.to_csv(fname.replace('.nii.gz', f'_{key}.csv'), index=False)

    # save data to NPY files
    for key, val in data.items():
        if len(val) == 0:  # don't write out empty array
            continue
        cdata = np.row_stack(val)
        if key == 'jacobian':
            fname = pjoin(DERIV_DIR, basename(SUB_MASK))
        else:
            fname = pjoin(DERIV_DIR, basename(COR_MASK))
        np.save(fname.replace('.nii.gz', f'_{key}.npy'), cdata)
