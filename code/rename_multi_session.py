import glob
import json
import os
import os.path as op
import shutil

DATADIR = op.join(op.dirname(op.dirname(op.abspath(__file__))), 'data')


def rename_file(src, dest, move_json=False, remove=False):
    if move_json:
        src = src.replace('.nii.gz', '.json')
        dest = dest.replace('.nii.gz', '.json')

    shutil.copy(src, src + '.bak')   # make backup
    if remove:
        print(f'Removing {op.basename(src)}')
        os.remove(src)               # remove file
    else:
        print(f'Moving {op.basename(src)} to {op.basename(dest)}')
        shutil.move(src, dest)       # rename file


if __name__ == '__main__':
    multises = glob.glob(op.join(DATADIR, 'sub-????/ses-?/anat',
                                 'sub-????_ses-?_run-0[2-9]_*T1w.nii.gz'),
                         recursive=True)
    multises = sorted(list(set(
        ['/'.join(f.replace(DATADIR, '').split('/')[1:3]) for f in multises]
    )))

    for subj in multises:
        # get TSV and make backup of TSV (only backup once)
        tsv = op.join(DATADIR, subj, subj.replace('/', '_') + '_scans.tsv')
        shutil.copy(tsv, tsv + '.bak')

        # make dictionary to hold scan info
        info = dict(keep=[], remove=[])

        # grab JSON sidecars and iterate through those
        sidecars = glob.glob(op.join(DATADIR, subj, 'anat', '*T1w.json'))
        for sc in sorted(sidecars):
            img = sc.replace('.json', '.nii.gz')

            # get series description from JSON
            with open(sc) as src:
                series_desc = json.load(src)['SeriesDescription'].lower()

            # determine what to rename the file
            if series_desc in ['mprage_grappa', 'sag_mprage_grappa']:
                info['keep'].append(img)
            else:
                info['remove'].append(img)

        # remove first in case of name clashes in TSV
        for acqtype in ['remove', 'keep']:
            scans = info[acqtype]
            for run, img in enumerate(sorted(scans)):
                # generate new name for image
                subj = '_'.join(op.basename(img).split('_')[:2])
                new_fname = op.join(op.dirname(img),
                                    subj + '_run-01_T1w.nii.gz')

                with open(tsv, 'r') as src:
                    text = src.read()

                remove = acqtype == 'remove'
                if acqtype == 'keep':
                    # don't need to change things if we're not renaming!
                    if img == new_fname:
                        print(f'Keeping {op.basename(img)}')
                        continue
                if remove:
                    # remove scan from TSV file
                    text = '\n'.join([f for f in text.split('\n') if
                                      op.basename(img) not in f])

                # move / remove files and write out updated TSV
                rename_file(img, new_fname, remove=remove)
                rename_file(img, new_fname, move_json=True, remove=remove)
                with open(tsv, 'w') as dest:
                    dest.write(text)
