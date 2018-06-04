#!/usr/bin/env python

import logging
from os.path import abspath, dirname, join as pjoin, exists as pexists

import nibabel as nib
from nilearn.image import new_img_like
from nilearn._utils import check_niimg
import numpy as np
import pandas as pd

PROJ_DIR = dirname(dirname(abspath(__file__)))
SUB_MASK = pjoin(PROJ_DIR, 'code',
                 'atlas-Pauli2018_space-MNI152NLin2009cAsym_'
                 'hemi-both_deterministic.nii.gz')
logging.basicConfig(format='[%(levelname)s]: ++ %(message)s',
                    level=logging.INFO)


def split_prob_along_hemisphere(atlas, axis=0):
    """
    Splits probabilistic ``atlas`` along provided ``axis``

    Parameters
    ----------
    atlas : str or img_like
        Filepath to atlas image or loaded atlas image
    axis : int, optional
        Axis along which to split `atlas`. Default: 0

    Return
    ------
    split : img_like
        Provided ``atlas`` split along ``axis``
    """

    atlas = check_niimg(atlas, atleast_4d=True)
    data = atlas.get_data()
    mask = np.zeros_like(data[:, :, :, [0]])

    rh, lh = mask.copy(), mask.copy()
    rh[:data.shape[axis] // 2] = 1
    lh[data.shape[axis] // 2:] = 1

    split = np.concatenate([rh * data, lh * data], axis=-1)

    return new_img_like(atlas, split)


def split_det_along_hemisphere(atlas, axis=0):
    """
    Splits deterministic ``atlas`` along provided ``axis``

    Parameters
    ----------
    atlas : str or img_like
        Filepath to atlas image or loaded atlas image
    axis : int, optional
        Axis along which to split `atlas`. Default: 0

    Return
    ------
    split : img_like
        Provided ``atlas`` split along ``axis``
    """

    atlas = check_niimg(atlas, ensure_ndim=3)
    data = atlas.get_data()
    mask = np.zeros_like(data)

    rh, lh = mask.copy(), mask.copy()
    rh[:data.shape[axis] // 2] = 1
    lh[data.shape[axis] // 2:] = 1

    rh, lh = rh * data, lh * data
    lh[lh.nonzero()] += np.unique(rh).max()

    split = rh + lh

    return new_img_like(atlas, split)


if __name__ == '__main__':
    # split atlas and save to new file
    logging.info('Splitting {} along axis {}.'.format(SUB_MASK, 0))
    if 'probabilistic' in SUB_MASK:
        out = split_prob_along_hemisphere(SUB_MASK, axis=0)
    else:
        out = split_det_along_hemisphere(SUB_MASK, axis=0)
    fname = SUB_MASK.replace('hemi-both', 'hemi-split')
    logging.info('Saving split atlas to {}.'.format(fname))
    if not pexists(fname):
        nib.save(out, fname)

    # make new parcellation info
    SUB_PARC = SUB_MASK.replace('.nii.gz', '.csv')
    parc = pd.read_csv(SUB_PARC)
    hemisphere = np.hstack([np.tile('rh', len(parc)),
                            np.tile('lh', len(parc))])
    # if deterministic atlas we want real parcellation values
    id = np.trim_zeros(np.unique(out.get_data())).astype(int)
    data = np.column_stack([id,
                            np.tile(parc.label, 2) + '_' + hemisphere,
                            hemisphere,
                            np.tile('subcortical', len(hemisphere))])
    columns = ['id', 'label', 'hemisphere', 'cortical']
    fname = SUB_PARC.replace('hemi-both', 'hemi-split')
    if not pexists(fname):
        pd.DataFrame(data, columns=columns).to_csv(fname, index=False)
