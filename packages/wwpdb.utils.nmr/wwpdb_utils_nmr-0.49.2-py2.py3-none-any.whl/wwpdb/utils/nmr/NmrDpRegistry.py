##
# File: NmrDpRegistry.py
# Date: 07-Jan-2025
#
# Updates:
##
""" Registry class for NMR data processing.
    @author: Masashi Yokochi
"""
__docformat__ = "restructuredtext en"
__author__ = "Masashi Yokochi"
__email__ = "yokochi@protein.osaka-u.ac.jp"
__license__ = "Apache License 2.0"
__version__ = "5.0.0"

import sys
import copy
import pynmrstar

from dataclasses import dataclass, field

from typing import IO, List, Union

try:
    from wwpdb.utils.nmr.NmrDpConstant import (INITIAL_ENTRY_ID,
                                               RMSD_NOT_SUPERIMPOSED,
                                               RMSD_OVERLAID_EXACTLY,
                                               CS_ANOMALOUS_ERROR_SCALED_BY_SIGMA,
                                               CS_UNUSUAL_ERROR_SCALED_BY_SIGMA,
                                               CS_DIFF_ERROR_SCALED_BY_SIGMA,
                                               KEY_ITEMS,
                                               CONSIST_KEY_ITEMS,
                                               PK_DATA_ITEMS,
                                               AUX_KEY_ITEMS,
                                               AUX_DATA_ITEMS,
                                               REPRESENTATIVE_MODEL_ID,
                                               REPRESENTATIVE_ALT_ID,
                                               DEFAULT_SUBTYPE_DATA,
                                               DEFAULT_COORD_PROPERTIES)
    from wwpdb.utils.nmr.NmrDpReport import NmrDpReport
except ImportError:
    from nmr.NmrDpConstant import (INITIAL_ENTRY_ID,
                                   RMSD_NOT_SUPERIMPOSED,
                                   RMSD_OVERLAID_EXACTLY,
                                   CS_ANOMALOUS_ERROR_SCALED_BY_SIGMA,
                                   CS_UNUSUAL_ERROR_SCALED_BY_SIGMA,
                                   CS_DIFF_ERROR_SCALED_BY_SIGMA,
                                   KEY_ITEMS,
                                   CONSIST_KEY_ITEMS,
                                   PK_DATA_ITEMS,
                                   AUX_KEY_ITEMS,
                                   AUX_DATA_ITEMS,
                                   REPRESENTATIVE_MODEL_ID,
                                   REPRESENTATIVE_ALT_ID,
                                   DEFAULT_SUBTYPE_DATA,
                                   DEFAULT_COORD_PROPERTIES)
    from nmr.NmrDpReport import NmrDpReport


@dataclass
class NmrDpRegistry:
    """ Registry class for NMR data processing.
    """
    verbose: bool = False
    log: IO = sys.stderr

    debug: bool = False
    mr_debug: bool = False

    # current workflow operation name
    op: str = None

    # whether to enable rescue routine
    rescue_mode: bool = True
    # whether to enable remediation routines
    remediation_mode: bool = False
    # whether NMR combined deposition or not (NMR conventional deposition)
    combined_mode: bool = True
    # whether native NMR combined deposition
    native_combined: bool = False
    # whether to merge NMR metadata on submission
    submission_mode: bool = False
    # whether to allow sequence mismatch during annotation
    annotation_mode: bool = False
    # whether to use datablock name of public release
    release_mode: bool = False
    # whether to allow to raise internal error
    internal_mode: bool = False
    # whether to combine spectral peak list in any plain text format into single NMR-STAR file
    # (must be turned off after Phase 2, DAOTHER-7407)
    merge_any_pk_as_is: bool = False
    # whether to enforce to use _Peak_row_format loop for spectral peak remediation (DAOTHER-8905)
    enforce_peak_row_format: bool = False

    # whether to allow empty coordinate file path
    bmrb_only: bool = False
    # whether not to block deposition because of anomalous cs
    nonblk_anomalous_cs: bool = False
    # whether not to block deposition because bad n-term amino group
    nonblk_bad_nterm: bool = False
    # whether to update polymer sequence
    update_poly_seq: bool = False
    # whether to resolve conflict
    resolve_conflict: bool = False
    # whether to detect missing mandatory tags as errors
    check_mandatory_tag: bool = False
    # whether to detect consistency of author sequence (nmr-star specific)
    check_auth_seq: bool = False
    # whether to skip missing_mandatory_content error for validation server (DAOTHER-8658)
    validation_server: bool = False
    # whether to skip missing_mandatory_content error for data conversion server (DAOTHER-9785)
    conversion_server: bool = False
    # whether to translate conventional pseudo atom nomenclature in combined NMR-STAR file
    transl_pseudo_name: bool = False
    # whether to enable tolerant sequence alignment for residue variants
    tolerant_seq_align: bool = False

    # whether to fix format issue (enabled if NMR conventional deposition or release mode)
    fix_format_issue: bool = False
    # whether to exclude missing mandatory data (enabled if NMR conventional deposition)
    excl_missing_data: bool = False
    # whether to complement missing data (add missing pseudo atoms in NMR restraints, DAOTHER-7681, issue #1)
    cmpl_missing_data: bool = False
    # whether to trust pdbx_nmr_ensemble to get total number of models
    trust_pdbx_nmr_ens: bool = True

    # whether sf_framecode has to be fixed
    has_legacy_sf_issue: bool = False

    # current entry_id, to be replaced
    entry_id: str = INITIAL_ENTRY_ID
    # bmrb id (internal use only)
    bmrb_id: str = None
    # current assembly name
    assembly_name: str = '?'

    # whether to retain original content if possible
    retain_original: bool = True
    # whether to leave internal commentary note in processed NMR-STAR file
    leave_intl_note: bool = True
    # whether to use reduced atom notation in warning/error message
    reduced_atom_notation: bool = True

    # whether entity category exists (nmr-star specific)
    has_star_entity: bool = False
    # whether a CS loop is in the primary NMR-STAR file (used only for NMR data remediation)
    has_star_chem_shift: bool = True
    # whether public MR file contains valid NMR-STAR restraints (used only for NMR data remediation)
    mr_has_valid_star_restraint: bool = False

    # whether permit missing distance restraints (NMR unified deposition, DAOTHER-8088 1.b, 8108)
    permit_missing_dist_restraint: bool = True
    # whether permit missing distance restraints (NMR legacy deposition, DAOTHER-8088 1.b, 8108)
    permit_missing_legacy_dist_restraint: bool = True
    # whether legacy distance restraint has been uploaded
    legacy_dist_restraint_uploaded: bool = False

    # whether stereo-array isotope labeling method has been applied for the study
    sail_flag: bool = False

    # whether pdbx_database_status.recvd_nmr_constraints is 'Y'
    recvd_nmr_constraints: bool = False
    # whether pdbx_database_status.recvd_nmr_data is 'Y'
    recvd_nmr_data: bool = False

    # source, destination, and log file paths
    srcName: str = None

    srcPath: str = None
    dstPath: str = None
    cifPath: str = None

    # current working directory
    dirPath: str = None

    # whether coordinate file is already examined
    cifChecked: bool = False

    # cache path of coordinate assembly check
    asmChkCachePath = None

    # cache path of coordinate properties
    coordPropCachePath = None

    # auxiliary input resource
    inputParamDict: dict = field(default_factory=dict)
    # auxiliary output resource
    outputParamDict: dict = field(default_factory=dict)

    # data processing report
    report: NmrDpReport = None

    # ChemCompUtil
    ccU = None

    # BMRBChemShiftStat
    csStat = None

    # CifToNmrStar
    c2S = None

    # NEFTranslator
    nefT = None

    # NmrDpMrSplitter
    dpS = None

    # NmrDpFirstAid
    dpA = None

    # NmrDpValidation
    dpV = None

    # NmrDpRemediation
    dpR = None

    # current size of file path list for star formatted data files
    file_path_list_len: int = 1
    # current size of file path list for star formatted cs files
    cs_file_path_list_len: int = 1

    # pynmrstar data types: 'Entry', 'Saveframe', 'Loop'
    star_data_type: List[str] = field(default_factory=list)
    # pynmrstar data
    star_data: List[Union[pynmrstar.Entry, pynmrstar.Saveframe, pynmrstar.Loop]] = field(default_factory=list)

    # history of saveframe name corrections
    sf_name_corrections: List[dict] = field(default_factory=list)

    original_error_message: List[dict] = field(default_factory=list)
    divide_mr_error_message: List[dict] = field(default_factory=list)
    strip_mr_error_message: List[dict] = field(default_factory=list)

    # current inventory of each NMR data file
    sf_category_list: List[str] = field(default_factory=list)
    lp_category_list: List[str] = field(default_factory=list)

    # ANTLR4's SLL prediction modes
    sll_pred_holder: dict = field(default_factory=dict)
    sll_pred_forced: List[str] = field(default_factory=list)

    # temporary dictionaries used to merge legacy restraints and spectral peak lists
    list_id_counter: dict = None
    mr_sf_dict_holder: dict = None
    pk_sf_holder: dict = None

    # extended sequence by NMR data in reference to the coordinates
    nmr_ext_poly_seq: List[dict] = None

    # rows of _Chem_comp_assembly loop
    chem_comp_asm_dat: List[list] = None

    # combined nmr cif file path (used only for BMRB internal annotation)
    srcNmrCifPath: str = None
    # saveframe category list of combined nmr cif file (used only for BMRB internal annotation)
    nmr_cif_sf_category_list: List[str] = None

    # defined content subtypes for restraints
    mr_content_subtypes: List[str] = None
    # defined content subtypes for NMR data
    nmr_rep_content_subtypes: List[str] = None

    # criterion for detection of not superimposed models
    rmsd_not_superimposed: float = RMSD_NOT_SUPERIMPOSED
    # criterion for detection of exactly overlaid models
    rmsd_overlaid_exactly: float = RMSD_OVERLAID_EXACTLY

    # criterion on chemical shift for anomalous value scaled by its sigma
    cs_anomalous_error_scaled_by_sigma: float = CS_ANOMALOUS_ERROR_SCALED_BY_SIGMA
    # criterion on chemical shift for unusual value scaled by its sigma
    cs_unusual_error_scaled_by_sigma: float = CS_UNUSUAL_ERROR_SCALED_BY_SIGMA
    # criterion on chemical shift difference error scaled by its sigma
    cs_diff_error_scaled_by_sigma: float = CS_DIFF_ERROR_SCALED_BY_SIGMA

    # key items of loop
    key_items: dict = field(default_factory=lambda: KEY_ITEMS)
    # key items of loop to check consistency
    consist_key_items: dict = field(default_factory=lambda: CONSIST_KEY_ITEMS)
    # loop data items for spectral peak
    pk_data_items: dict = field(default_factory=lambda: PK_DATA_ITEMS)
    # auxiliary loop key items
    aux_key_items: dict = field(default_factory=lambda: AUX_KEY_ITEMS)
    # auxiliary loop data items
    aux_data_items: dict = field(default_factory=lambda: AUX_DATA_ITEMS)

    # main contents of loops
    lp_data: dict = field(default_factory=lambda: copy.deepcopy(DEFAULT_SUBTYPE_DATA))
    # auxiliary contents of loops
    aux_data: dict = field(default_factory=lambda: copy.deepcopy(DEFAULT_SUBTYPE_DATA))
    # contents of saveframe tags
    sf_tag_data: dict = field(default_factory=lambda: copy.deepcopy(DEFAULT_SUBTYPE_DATA))

    # PairwiseAlign
    pA = None

    # CifReader
    cR = None

    # experimental method
    exptl_method: str = None
    # whether solid-state NMR is applied to symmetric samples such as fibrils
    symmetric: str = None
    # whether nmr chain is cyclic polymer or not
    is_cyclic_polymer: dict = field(default_factory=dict)
    # extracted conformational annotation of coordinate file
    nmr_struct_conf: dict = field(default_factory=dict)

    # representative model id
    representative_model_id: int = REPRESENTATIVE_MODEL_ID
    # representative_alt_id
    representative_alt_id: str = REPRESENTATIVE_ALT_ID
    # total number of models
    total_models: int = 0
    # list of effective model_id
    eff_model_ids: List[int] = field(default_factory=list)
    # item tag names of 'atom_site' category of the coordinates
    coord_atom_site_tags: List[str] = None

    # ParserListerUtil.coordAssemblyChecker
    caC: dict = None

    # coordinate properties cache
    cpC: dict = field(default_factory=lambda: copy.deepcopy(DEFAULT_COORD_PROPERTIES))
    # hash code of coordinate properties cache
    cpcHashCode: str = None

    # set of entity_assembly_id having experimental data
    ent_asym_id_with_exptl_data: set = field(default_factory=set)
    # set of label_aysm_id having experimental data
    label_asym_id_with_exptl_data: set = field(default_factory=set)
    # set of auth_asym_id indicating occurrence of chemical exchange (eNOE)
    auth_asym_ids_with_chem_exch: dict = field(default_factory=dict)
    # set of residue numbering scheme indicating occurrence of chemical exchange (eNOE)
    auth_seq_ids_with_chem_exch: dict = field(default_factory=dict)

    # mapping of chain_id for remediation
    chain_id_map_for_remediation: dict = field(default_factory=dict)
    # mapping of chain_id and seq_id for remediation
    seq_id_map_for_remediation: dict = field(default_factory=dict)

    # suspended error items for lazy evaluation
    suspended_errors_for_lazy_eval: List[dict] = field(default_factory=list)
    # suspended warning items for lazy evaluation
    suspended_warnings_for_lazy_eval: List[dict] = field(default_factory=list)

    # atom name mapping of public MR file between the coordinates and submitted file
    mr_atom_name_mapping: List[dict] = None
    # atom name mapping derived from revision history and PDB Versioned Archive
    versioned_atom_name_mapping: List[dict] = None
    # atom name mapping derived from the original uploaded coordinate file
    internal_atom_name_mapping: dict = field(default_factory=dict)
