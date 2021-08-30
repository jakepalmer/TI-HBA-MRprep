import os


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """
    Heuristic evaluator for determining which runs belong where.
    """
    # Structural
    t1w = create_key('sub-{subject}/anat/sub-{subject}_T1w')
    t2w = create_key('sub-{subject}/anat/sub-{subject}_T2w')
    flair = create_key('sub-{subject}/anat/sub-{subject}_FLAIR')
    # DWI
    dwiAP = create_key('sub-{subject}/dwi/sub-{subject}_dir-AP_dwi')
    # dwiPA = create_key('sub-{subject}/dwi/sub-{subject}_dir-PA_dwi')
    dwiPA = create_key('sub-{subject}/fmap/sub-{subject}_dir-PA_epi')
    # rsfMRI
    func = create_key('sub-{subject}/func/sub-{subject}_task-rest_bold')
    fmap_magnitude = create_key('sub-{subject}/fmap/sub-{subject}_magnitude')
    fmap_phasediff = create_key('sub-{subject}/fmap/sub-{subject}_phasediff')

    info = {t1w: [], t2w: [], flair: [], dwiAP: [],
            dwiPA: [], fmap_magnitude: [], fmap_phasediff: []}

    for s in seqinfo:
        if s.series_description == "MPRAGE_Linear" and s.dim1 == 256 and s.dim2 == 256 and s.dim3 == 208:
            info[t1w] = [s.series_id]
        if s.series_description == "t2_space_dark-fluid_sag_p2" and s.dim1 == 256 and s.dim2 == 256 and s.dim3 == 208:
            info[flair] = [s.series_id]
        if s.series_description == "t2_space_sag_iso_p6" and s.dim1 == 256 and s.dim2 == 256 and s.dim3 == 240:
            info[t2w] = [s.series_id]
        if s.series_description == "ep2d_diff_qball96dir_2iso_AP_b2500&b0" and s.dim1 == 114 and s.dim2 == 114 and s.dim3 == 72 and s.dim4 == 97:
            info[dwiAP] = [s.series_id]
        if s.series_description == "ep2d_diff_qball96dir_2iso_PA_b0" and s.dim1 == 114 and s.dim2 == 114 and s.dim3 == 432:
            info[dwiPA] = [s.series_id]
        if s.series_description == "rsfMRI_ep2d_bold_moco_p2_sms4_404meas" and s.dim1 == 74 and s.dim2 == 74 and s.dim3 == 56 and s.dim4 == 404:
            info[func] = [s.series_id]
        if s.series_description == "gre_field_mapping 3x3x3" and s.dim1 == 64 and s.dim2 == 64 and s.dim3 == 112:
            info[fmap_magnitude] = [s.series_id]
        if s.series_description == "gre_field_mapping 3x3x3" and s.dim1 == 64 and s.dim2 == 64 and s.dim3 == 56:
            info[fmap_phasediff] = [s.series_id]

    return info
