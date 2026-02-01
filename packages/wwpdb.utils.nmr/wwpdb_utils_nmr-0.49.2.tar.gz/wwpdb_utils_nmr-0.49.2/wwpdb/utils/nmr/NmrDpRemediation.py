##
# File: NmrDpRemediation.py
# Date: 07-Jan-2026
#
# Updates:
##
""" Wrapper class for NMR data remediation.
    @author: Masashi Yokochi
"""
__docformat__ = "restructuredtext en"
__author__ = "Masashi Yokochi"
__email__ = "yokochi@protein.osaka-u.ac.jp"
__license__ = "Apache License 2.0"
__version__ = "5.0.0"

import os
import re
import itertools
import copy
import collections
import pynmrstar
import functools

from operator import itemgetter
from typing import List, Tuple, Union, Optional
from datetime import (datetime, timedelta)

try:
    from wwpdb.utils.nmr.NmrDpConstant import (MR_FILE_PATH_LIST_KEY,
                                               AR_FILE_PATH_LIST_KEY,
                                               AC_FILE_PATH_LIST_KEY,
                                               NMR_CONTENT_SUBTYPES,
                                               PK_CONTENT_SUBTYPES,
                                               READABLE_FILE_TYPE,
                                               SF_CATEGORIES,
                                               LP_CATEGORIES,
                                               MR_MAX_SPACER_LINES,
                                               INDEX_TAGS,
                                               DATA_ITEMS,
                                               POTENTIAL_ITEMS,
                                               NUM_DIM_ITEMS,
                                               ALLOWED_TAGS,
                                               SF_TAG_PREFIXES,
                                               SF_ALLOWED_TAGS,
                                               AUX_LP_CATEGORIES,
                                               ITEM_NAMES_IN_CS_LOOP,
                                               ITEM_NAMES_IN_DIST_LOOP,
                                               ITEM_NAMES_IN_DIHED_LOOP,
                                               ITEM_NAMES_IN_RDC_LOOP,
                                               LOW_SEQ_COVERAGE,
                                               EMPTY_VALUE,
                                               STD_MON_DICT,
                                               PROTON_BEGIN_CODE,
                                               PSE_PRO_BEGIN_CODE,
                                               AMINO_PROTON_CODE,
                                               UNKNOWN_RESIDUE,
                                               NMR_STAR_VERSION,
                                               PARAMAGNETIC_ELEMENTS,
                                               MAX_DIM_NUM_OF_SPECTRA,
                                               ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS,
                                               ALLOWED_AMBIGUITY_CODES,
                                               GLOBAL_OFFSET_ATTEMPT,
                                               PERIPH_OFFSET_ATTEMPT,
                                               WORK_MODEL_FILE_NAME_PAT,
                                               COMMENT_PAT,
                                               SEQ_MISMATCH_WARNING_PAT,
                                               INCONSISTENT_RESTRAINT_WARNING_PAT,
                                               CONCAT_SEQ_ID_INS_CODE_PAT,
                                               CHK_DESC_PAT,
                                               CHK_DESC_ONE_PAT,
                                               CHK_DESC_MAND_PAT,
                                               CHK_DESC_MAND_ONE_PAT,
                                               MISMATCHED_INPUT_ERR_MSG,
                                               EXTRANEOUS_INPUT_ERR_MSG,
                                               DIST_AMBIG_LOW,
                                               DIST_AMBIG_UP,
                                               REPRESENTATIVE_ASYM_ID)
    from wwpdb.utils.nmr.NmrDpRegistry import NmrDpRegistry
    from wwpdb.utils.nmr.NmrDpMrSplitter import (detect_encoding,
                                                 get_peak_list_format,
                                                 get_number_of_dimensions_of_peak_list)
    from wwpdb.utils.nmr.NmrDpValidation import is_like_planality_boundary
    from wwpdb.utils.nmr.AlignUtil import (deepcopy,
                                           letterToDigit,
                                           fillBlankCompIdWithOffset,
                                           getScoreOfSeqAlign,
                                           getOneLetterCodeCanSequence,
                                           getOneLetterCodeSequence,
                                           getRestraintFormatName,
                                           getChemShiftFormatName,
                                           updatePolySeqRst,
                                           sortPolySeqRst,
                                           alignPolymerSequence,
                                           assignPolymerSequence,
                                           trimSequenceAlignment,
                                           getPrettyJson)
    from wwpdb.utils.nmr.CifToNmrStar import (has_key_value,
                                              get_first_sf_tag,
                                              set_sf_tag)
    from wwpdb.utils.nmr.NmrVrptUtility import write_as_pickle
    from wwpdb.utils.nmr.mr.ParserListenerUtil import (translateToStdResName,
                                                       translateToStdAtomName,
                                                       isAmbigAtomSelection,
                                                       getTypeOfDihedralRestraint,
                                                       getRestraintName,
                                                       contentSubtypeOf,
                                                       incListIdCounter,
                                                       retrieveOriginalFileName,
                                                       getPdbxNmrSoftwareName,
                                                       getSaveframe,
                                                       getLoop,
                                                       getRow,
                                                       getPotentialType)
    from wwpdb.utils.nmr.mr.AmberMRReader import AmberMRReader
    from wwpdb.utils.nmr.mr.AmberPTReader import AmberPTReader
    from wwpdb.utils.nmr.mr.AriaMRReader import AriaMRReader
    from wwpdb.utils.nmr.mr.AriaMRXReader import AriaMRXReader
    from wwpdb.utils.nmr.mr.BareMRReader import BareMRReader
    from wwpdb.utils.nmr.mr.BarePDBReader import BarePDBReader
    from wwpdb.utils.nmr.mr.BiosymMRReader import BiosymMRReader
    from wwpdb.utils.nmr.mr.CharmmCRDReader import CharmmCRDReader
    from wwpdb.utils.nmr.mr.CharmmMRReader import CharmmMRReader
    from wwpdb.utils.nmr.mr.CnsMRReader import CnsMRReader
    from wwpdb.utils.nmr.mr.CyanaMRReader import CyanaMRReader
    from wwpdb.utils.nmr.mr.CyanaNOAReader import CyanaNOAReader
    from wwpdb.utils.nmr.mr.DynamoMRReader import DynamoMRReader
    from wwpdb.utils.nmr.mr.GromacsMRReader import GromacsMRReader
    from wwpdb.utils.nmr.mr.GromacsPTReader import GromacsPTReader
    from wwpdb.utils.nmr.mr.IsdMRReader import IsdMRReader
    from wwpdb.utils.nmr.mr.RosettaMRReader import RosettaMRReader
    from wwpdb.utils.nmr.mr.SchrodingerMRReader import SchrodingerMRReader
    from wwpdb.utils.nmr.mr.SybylMRReader import SybylMRReader
    from wwpdb.utils.nmr.mr.XplorMRReader import XplorMRReader
    from wwpdb.utils.nmr.pk.AriaPKReader import AriaPKReader
    from wwpdb.utils.nmr.pk.BarePKReader import BarePKReader
    from wwpdb.utils.nmr.pk.CcpnPKReader import CcpnPKReader
    from wwpdb.utils.nmr.pk.OliviaPKReader import OliviaPKReader
    from wwpdb.utils.nmr.pk.NmrPipePKReader import NmrPipePKReader
    from wwpdb.utils.nmr.pk.PonderosaPKReader import PonderosaPKReader
    from wwpdb.utils.nmr.pk.NmrViewPKReader import NmrViewPKReader
    from wwpdb.utils.nmr.pk.NmrViewNPKReader import NmrViewNPKReader
    from wwpdb.utils.nmr.pk.SparkyPKReader import SparkyPKReader
    from wwpdb.utils.nmr.pk.SparkyNPKReader import SparkyNPKReader
    from wwpdb.utils.nmr.pk.SparkyRPKReader import SparkyRPKReader
    from wwpdb.utils.nmr.pk.SparkySPKReader import SparkySPKReader
    from wwpdb.utils.nmr.pk.TopSpinPKReader import TopSpinPKReader
    from wwpdb.utils.nmr.pk.VnmrPKReader import VnmrPKReader
    from wwpdb.utils.nmr.pk.XeasyPKReader import XeasyPKReader
    from wwpdb.utils.nmr.pk.XeasyPROTReader import XeasyPROTReader
    from wwpdb.utils.nmr.pk.XwinNmrPKReader import XwinNmrPKReader
    from wwpdb.utils.nmr.cs.AriaCSReader import AriaCSReader
    from wwpdb.utils.nmr.cs.BareCSReader import BareCSReader
    from wwpdb.utils.nmr.cs.GarretCSReader import GarretCSReader
    from wwpdb.utils.nmr.cs.NmrPipeCSReader import NmrPipeCSReader
    from wwpdb.utils.nmr.cs.OliviaCSReader import OliviaCSReader
    from wwpdb.utils.nmr.cs.PippCSReader import PippCSReader
    from wwpdb.utils.nmr.cs.PpmCSReader import PpmCSReader
    from wwpdb.utils.nmr.cs.NmrStar2CSReader import NmrStar2CSReader
    from wwpdb.utils.nmr.cs.XeasyCSReader import XeasyCSReader
except ImportError:
    from nmr.NmrDpConstant import (MR_FILE_PATH_LIST_KEY,
                                   AR_FILE_PATH_LIST_KEY,
                                   AC_FILE_PATH_LIST_KEY,
                                   NMR_CONTENT_SUBTYPES,
                                   PK_CONTENT_SUBTYPES,
                                   READABLE_FILE_TYPE,
                                   SF_CATEGORIES,
                                   LP_CATEGORIES,
                                   MR_MAX_SPACER_LINES,
                                   INDEX_TAGS,
                                   DATA_ITEMS,
                                   POTENTIAL_ITEMS,
                                   NUM_DIM_ITEMS,
                                   ALLOWED_TAGS,
                                   SF_TAG_PREFIXES,
                                   SF_ALLOWED_TAGS,
                                   AUX_LP_CATEGORIES,
                                   ITEM_NAMES_IN_CS_LOOP,
                                   ITEM_NAMES_IN_DIST_LOOP,
                                   ITEM_NAMES_IN_DIHED_LOOP,
                                   ITEM_NAMES_IN_RDC_LOOP,
                                   LOW_SEQ_COVERAGE,
                                   EMPTY_VALUE,
                                   STD_MON_DICT,
                                   PROTON_BEGIN_CODE,
                                   PSE_PRO_BEGIN_CODE,
                                   AMINO_PROTON_CODE,
                                   UNKNOWN_RESIDUE,
                                   NMR_STAR_VERSION,
                                   PARAMAGNETIC_ELEMENTS,
                                   MAX_DIM_NUM_OF_SPECTRA,
                                   ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS,
                                   ALLOWED_AMBIGUITY_CODES,
                                   GLOBAL_OFFSET_ATTEMPT,
                                   PERIPH_OFFSET_ATTEMPT,
                                   WORK_MODEL_FILE_NAME_PAT,
                                   COMMENT_PAT,
                                   SEQ_MISMATCH_WARNING_PAT,
                                   INCONSISTENT_RESTRAINT_WARNING_PAT,
                                   CONCAT_SEQ_ID_INS_CODE_PAT,
                                   CHK_DESC_PAT,
                                   CHK_DESC_ONE_PAT,
                                   CHK_DESC_MAND_PAT,
                                   CHK_DESC_MAND_ONE_PAT,
                                   MISMATCHED_INPUT_ERR_MSG,
                                   EXTRANEOUS_INPUT_ERR_MSG,
                                   DIST_AMBIG_LOW,
                                   DIST_AMBIG_UP,
                                   REPRESENTATIVE_ASYM_ID)
    from nmr.NmrDpRegistry import NmrDpRegistry
    from nmr.NmrDpMrSplitter import (detect_encoding,
                                     get_peak_list_format,
                                     get_number_of_dimensions_of_peak_list)
    from nmr.NmrDpValidation import is_like_planality_boundary
    from nmr.AlignUtil import (deepcopy,
                               letterToDigit,
                               fillBlankCompIdWithOffset,
                               getScoreOfSeqAlign,
                               getOneLetterCodeCanSequence,
                               getOneLetterCodeSequence,
                               getRestraintFormatName,
                               getChemShiftFormatName,
                               updatePolySeqRst,
                               sortPolySeqRst,
                               alignPolymerSequence,
                               assignPolymerSequence,
                               trimSequenceAlignment,
                               getPrettyJson)
    from nmr.CifToNmrStar import (has_key_value,
                                  get_first_sf_tag,
                                  set_sf_tag)
    from nmr.NmrVrptUtility import write_as_pickle
    from nmr.mr.ParserListenerUtil import (translateToStdResName,
                                           translateToStdAtomName,
                                           isAmbigAtomSelection,
                                           getTypeOfDihedralRestraint,
                                           getRestraintName,
                                           contentSubtypeOf,
                                           incListIdCounter,
                                           retrieveOriginalFileName,
                                           getPdbxNmrSoftwareName,
                                           getSaveframe,
                                           getLoop,
                                           getRow,
                                           getPotentialType)
    from nmr.mr.AmberMRReader import AmberMRReader
    from nmr.mr.AmberPTReader import AmberPTReader
    from nmr.mr.AriaMRReader import AriaMRReader
    from nmr.mr.AriaMRXReader import AriaMRXReader
    from nmr.mr.BareMRReader import BareMRReader
    from nmr.mr.BarePDBReader import BarePDBReader
    from nmr.mr.BiosymMRReader import BiosymMRReader
    from nmr.mr.CharmmCRDReader import CharmmCRDReader
    from nmr.mr.CharmmMRReader import CharmmMRReader
    from nmr.mr.CnsMRReader import CnsMRReader
    from nmr.mr.CyanaMRReader import CyanaMRReader
    from nmr.mr.CyanaNOAReader import CyanaNOAReader
    from nmr.mr.DynamoMRReader import DynamoMRReader
    from nmr.mr.GromacsMRReader import GromacsMRReader
    from nmr.mr.GromacsPTReader import GromacsPTReader
    from nmr.mr.IsdMRReader import IsdMRReader
    from nmr.mr.RosettaMRReader import RosettaMRReader
    from nmr.mr.SchrodingerMRReader import SchrodingerMRReader
    from nmr.mr.SybylMRReader import SybylMRReader
    from nmr.mr.XplorMRReader import XplorMRReader
    from nmr.pk.AriaPKReader import AriaPKReader
    from nmr.pk.BarePKReader import BarePKReader
    from nmr.pk.CcpnPKReader import CcpnPKReader
    from nmr.pk.OliviaPKReader import OliviaPKReader
    from nmr.pk.NmrPipePKReader import NmrPipePKReader
    from nmr.pk.PonderosaPKReader import PonderosaPKReader
    from nmr.pk.NmrViewPKReader import NmrViewPKReader
    from nmr.pk.NmrViewNPKReader import NmrViewNPKReader
    from nmr.pk.SparkyPKReader import SparkyPKReader
    from nmr.pk.SparkyNPKReader import SparkyNPKReader
    from nmr.pk.SparkyRPKReader import SparkyRPKReader
    from nmr.pk.SparkySPKReader import SparkySPKReader
    from nmr.pk.TopSpinPKReader import TopSpinPKReader
    from nmr.pk.VnmrPKReader import VnmrPKReader
    from nmr.pk.XeasyPKReader import XeasyPKReader
    from nmr.pk.XeasyPROTReader import XeasyPROTReader
    from nmr.pk.XwinNmrPKReader import XwinNmrPKReader
    from nmr.cs.AriaCSReader import AriaCSReader
    from nmr.cs.BareCSReader import BareCSReader
    from nmr.cs.GarretCSReader import GarretCSReader
    from nmr.cs.NmrPipeCSReader import NmrPipeCSReader
    from nmr.cs.OliviaCSReader import OliviaCSReader
    from nmr.cs.PippCSReader import PippCSReader
    from nmr.cs.PpmCSReader import PpmCSReader
    from nmr.cs.NmrStar2CSReader import NmrStar2CSReader
    from nmr.cs.XeasyCSReader import XeasyCSReader


def get_chem_shift_format(fPath: str) -> Optional[str]:
    """ Return chemical shift format for a input file.
    """

    with open(fPath, 'r', encoding='utf-8', errors='ignore') as ifh:

        for idx, line in enumerate(ifh):

            if line.isspace() or COMMENT_PAT.match(line):
                continue

            file_type = get_chem_shift_format_from_string(line)

            if file_type is not None or idx >= MR_MAX_SPACER_LINES:
                return file_type

    return None


def get_chem_shift_format_from_string(string: str) -> Optional[str]:
    """ Return chemical shift format for a given input.
    """

    if '<!DOCTYPE chemical_shift_list SYSTEM' in string or '<chemical_shift_list>' in string:
        return 'nm-shi-ari'

    if 'VARS' in string and 'RESID ' in string and 'RESNAME ' in string and 'ATOMNAME ' in string and 'SHIFT' in string:
        return 'nm-shi-npi'

    if 'SHIFT_FL_FRMT' in string and 'RES_SIAD' in string:
        return 'nm-shi-pip'

    if 'TYPEDEF SEQUENCE' in string or 'TYPEDEF ASS_TBL_' in string:
        return 'nm-shi-oli'

    return None


class NmrDpRemediation:
    """ Wrapper class for NMR data remediation.
    """
    __slots__ = ('__class_name__',
                 '__version__',
                 '__reg',
                 '__paramag')

    def __init__(self, registry: NmrDpRegistry):
        self.__class_name__ = self.__class__.__name__
        self.__version__ = __version__

        self.__reg = registry

        self.__paramag = False

    def cleanUpSf(self) -> bool:
        """ Clean-up third-party saveframes.
        """

        __errors = self.__reg.report.getTotalErrors()

        for fileListId in range(self.__reg.file_path_list_len):

            if fileListId >= len(self.__reg.star_data):
                break

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']
            category_order = self.__reg.c2S.category_order if file_type == 'nmr-star' else self.__reg.c2S.category_order_nef

            if self.__reg.star_data_type[fileListId] == 'Entry':

                for sf in reversed(self.__reg.star_data[fileListId].frame_list):

                    if sf.tag_prefix not in category_order:
                        del self.__reg.star_data[fileListId][sf]

            if input_source_dic['content_subtype'] is None:
                continue

            for content_subtype in input_source_dic['content_subtype']:

                sf_category = SF_CATEGORIES[file_type][content_subtype]

                if self.__reg.star_data_type[fileListId] == 'Loop':
                    pass

                elif self.__reg.star_data_type[fileListId] == 'Saveframe':
                    sf = self.__reg.star_data[fileListId]

                    self.__cleanUpSf(file_type, content_subtype, sf)

                else:

                    for sf in self.__reg.star_data[fileListId].get_saveframes_by_category(sf_category):

                        self.__cleanUpSf(file_type, content_subtype, sf)

        return self.__reg.report.getTotalErrors() == __errors

    def __cleanUpSf(self, file_type: str, content_subtype: str,  # pylint: disable=no-self-use
                    sf: Union[pynmrstar.Saveframe, pynmrstar.Loop]):
        """ Clean-up third-party saveframes.
        """

        tags_to_be_removed = [t[0] for t in sf.tags if t[0] not in SF_ALLOWED_TAGS[file_type][content_subtype]]

        if len(tags_to_be_removed) == 0:
            return

        sf.remove_tag(tags_to_be_removed)

    def removeUnusedPdbInsCode(self, file_list_id: int, content_subtype: str,
                               sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                               lp_category: str) -> bool:
        """ Remove unused PDB_ind_code tags from loops.
        """

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        if loop is None:
            return False

        if content_subtype == 'chem_shift':
            tags = ['PDB_ins_code']
        elif content_subtype in ('dist_restraint', 'rdc_restraint'):
            tags = ['PDB_ins_code_1', 'PDB_ins_code_2']
        elif content_subtype == 'dihed_restraint':
            tags = ['PDB_ins_code_1', 'PDB_ins_code_2', 'PDB_ins_code_3', 'PDB_ins_code_4']
        else:
            return False

        if set(tags) & set(loop.tags) != set(tags):
            return False

        try:

            dat = loop.get_tag(tags)

            for row in dat:
                if row is not None and len(row) > 0:
                    for col in row:
                        if col is not None and col not in EMPTY_VALUE:
                            return False

            loop.remove_tag(tags)

            return True

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.removeUnusedPdbInsCode() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.removeUnusedPdbInsCode() ++ Error  - {str(e)}\n")

        return False

    def fixChainIdInLoop(self, file_list_id: int, file_type: str, content_subtype: str, sf_framecode: str,
                         chain_id: str, _chain_id: str):
        """ Fix chain ID of interesting loop.
        """

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        if file_type == 'nmr-star' and content_subtype == 'spectral_peak_alt':
            lp_category = '_Assigned_peak_chem_shift'

        if self.__reg.star_data_type[file_list_id] == 'Loop':
            sf = self.__reg.star_data[file_list_id]

            if sf_framecode == '':
                self.__fixChainIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, _chain_id)

        elif self.__reg.star_data_type[file_list_id] == 'Saveframe':
            sf = self.__reg.star_data[file_list_id]

            if get_first_sf_tag(sf, 'sf_framecode') == sf_framecode:
                self.__fixChainIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, _chain_id)

        else:

            for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):

                if get_first_sf_tag(sf, 'sf_framecode') != sf_framecode:
                    continue

                if not any(True for loop in sf.loops if loop.category == lp_category):
                    continue

                self.__fixChainIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, _chain_id)

    def __fixChainIdInLoop(self, file_list_id: int, file_type: str, content_subtype: str,
                           sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                           lp_category: str, chain_id: str, _chain_id: str):
        """ Fix chain ID of interesting loop.
        """

        uniq_chain_ids = self.__reg.report.getChainIdsForSameEntity() is None

        chain_id_name = 'chain_code' if file_type == 'nef' else 'Entity_assembly_ID'
        entity_id_name = None if file_type == 'nef' else 'Entity_ID'

        max_dim = 2

        if content_subtype in ('poly_seq', 'dist_restraint', 'rdc_restraint'):
            max_dim = 3

        elif content_subtype == 'dihed_restraint':
            max_dim = 5

        elif content_subtype == 'spectral_peak':

            try:

                _num_dim = get_first_sf_tag(sf, NUM_DIM_ITEMS[file_type])
                num_dim = int(_num_dim)

                if num_dim not in range(1, MAX_DIM_NUM_OF_SPECTRA):
                    raise ValueError()

            except ValueError:  # raised error already at __testIndexConsistency()
                return

            max_dim = num_dim + 1

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        if max_dim == 2:

            chain_id_col = loop.tags.index(chain_id_name) if chain_id_name in loop.tags else -1
            entity_id_col = -1
            if entity_id_name is not None:
                entity_id_col = loop.tags.index(entity_id_name) if entity_id_name in loop.tags else -1

            if chain_id_col == -1:
                return

            for row in loop:

                if row[chain_id_col] != chain_id:
                    continue

                row[chain_id_col] = _chain_id

                if uniq_chain_ids and entity_id_col != -1:
                    row[entity_id_col] = _chain_id

        else:

            for i in range(1, max_dim):

                _chain_id_name = chain_id_name + '_' + str(i)
                _entity_id_name = None if entity_id_name is None else entity_id_name + '_' + str(i)

                chain_id_col = loop.tags.index(_chain_id_name) if _chain_id_name in loop.tags else -1
                entity_id_col = -1
                if _entity_id_name is not None:
                    entity_id_col = loop.tags.index(_entity_id_name) if _entity_id_name in loop.tags else -1

                if chain_id_col == -1:
                    continue

                for row in loop:

                    if row[chain_id_col] != chain_id:
                        continue

                    row[chain_id_col] = _chain_id

                    if uniq_chain_ids and entity_id_col != -1:
                        row[entity_id_col] = _chain_id

    def fixSeqIdInLoop(self, file_list_id: int, file_type: str, content_subtype: str, sf_framecode: str,
                       chain_id: str, seq_id_conv_dict: dict):
        """ Fix sequence ID of interesting loop.
        """

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        if file_type == 'nmr-star' and content_subtype == 'spectral_peak_alt':
            lp_category = '_Assigned_peak_chem_shift'

        if self.__reg.star_data_type[file_list_id] == 'Loop':
            sf = self.__reg.star_data[file_list_id]

            if sf_framecode == '':
                self.__fixSeqIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, seq_id_conv_dict)

        elif self.__reg.star_data_type[file_list_id] == 'Saveframe':
            sf = self.__reg.star_data[file_list_id]

            if get_first_sf_tag(sf, 'sf_framecode') == sf_framecode:
                self.__fixSeqIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, seq_id_conv_dict)

        else:

            for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):

                if get_first_sf_tag(sf, 'sf_framecode') != sf_framecode:
                    continue

                if not any(True for loop in sf.loops if loop.category == lp_category):
                    continue

                self.__fixSeqIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, seq_id_conv_dict)

    def __fixSeqIdInLoop(self, file_list_id: int, file_type: str, content_subtype: str,
                         sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                         lp_category: str, chain_id: str, seq_id_conv_dict: dict):
        """ Fix sequence ID of interesting loop.
        """

        chain_id_name = 'chain_code' if file_type == 'nef' else 'Entity_assembly_ID'
        seq_id_name = 'sequence_code' if file_type == 'nef' else 'Comp_index_ID'
        seq_id_alt_name = None if file_type == 'nef' else 'Seq_ID'

        max_dim = 2

        if content_subtype in ('poly_seq', 'dist_restraint', 'rdc_restraint'):
            max_dim = 3

        elif content_subtype == 'dihed_restraint':
            max_dim = 5

        elif content_subtype == 'spectral_peak':

            try:

                _num_dim = get_first_sf_tag(sf, NUM_DIM_ITEMS[file_type])
                num_dim = int(_num_dim)

                if num_dim not in range(1, MAX_DIM_NUM_OF_SPECTRA):
                    raise ValueError()

            except ValueError:  # raised error already at __testIndexConsistency()
                return

            max_dim = num_dim + 1

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        if max_dim == 2:

            chain_id_col = loop.tags.index(chain_id_name) if chain_id_name in loop.tags else -1
            seq_id_col = loop.tags.index(seq_id_name) if seq_id_name in loop.tags else -1
            seq_id_alt_col = -1
            if seq_id_alt_name is not None:
                seq_id_alt_col = loop.tags.index(seq_id_alt_name) if seq_id_alt_name in loop.tags else -1

            if -1 in (chain_id_col, seq_id_col):
                return

            for row in loop:

                if row[chain_id_col] != chain_id:
                    continue

                seq_id = row[seq_id_col]

                if seq_id in seq_id_conv_dict:
                    row[seq_id_col] = seq_id_conv_dict[seq_id]

                if seq_id_alt_col == -1:
                    continue

                seq_id_alt = row[seq_id_alt_col]

                if seq_id_alt in seq_id_conv_dict:
                    row[seq_id_alt_col] = seq_id_conv_dict[seq_id_alt]

        else:

            for i in range(1, max_dim):

                _chain_id_name = chain_id_name + '_' + str(i)
                _seq_id_name = seq_id_name + '_' + str(i)

                chain_id_col = loop.tags.index(_chain_id_name) if _chain_id_name in loop.tags else -1
                seq_id_col = loop.tags.index(_seq_id_name) if _seq_id_name in loop.tags else -1
                seq_id_alt_col = -1
                if seq_id_alt_name is not None:
                    _seq_id_alt_name = seq_id_alt_name + '_' + str(i)
                    seq_id_alt_col = loop.tags.index(_seq_id_alt_name) if _seq_id_alt_name in loop.tags else -1

                if -1 in (chain_id_col, seq_id_col):
                    continue

                for row in loop:

                    if row[chain_id_col] != chain_id:
                        continue

                    seq_id = row[seq_id_col]

                    if seq_id in seq_id_conv_dict:
                        row[seq_id_col] = seq_id_conv_dict[seq_id]

                    if seq_id_alt_col == -1:
                        continue

                    seq_id_alt = row[seq_id_alt_col]

                    if seq_id_alt in seq_id_conv_dict:
                        row[seq_id_alt_col] = seq_id_conv_dict[seq_id_alt]

    def fixCompIdInLoop(self, file_list_id: int, file_type: str, content_subtype: str, sf_framecode: str,
                        chain_id: str, seq_id: int, comp_id_conv_dict: dict):
        """ Fix comp ID of interesting loop.
        """

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        if file_type == 'nmr-star' and content_subtype == 'spectral_peak_alt':
            lp_category = '_Assigned_peak_chem_shift'

        if self.__reg.star_data_type[file_list_id] == 'Loop':
            sf = self.__reg.star_data[file_list_id]

            if sf_framecode == '':
                self.__fixCompIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, seq_id, comp_id_conv_dict)

        elif self.__reg.star_data_type[file_list_id] == 'Saveframe':
            sf = self.__reg.star_data[file_list_id]

            if get_first_sf_tag(sf, 'sf_framecode') == sf_framecode:
                self.__fixCompIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, seq_id, comp_id_conv_dict)

        else:

            for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):

                if get_first_sf_tag(sf, 'sf_framecode') != sf_framecode:
                    continue

                if not any(True for loop in sf.loops if loop.category == lp_category):
                    continue

                self.__fixCompIdInLoop(file_list_id, file_type, content_subtype, sf, lp_category, chain_id, seq_id, comp_id_conv_dict)

    def __fixCompIdInLoop(self, file_list_id: int, file_type: str, content_subtype: str,
                          sf: Union[pynmrstar.Saveframe, pynmrstar.Loop], lp_category: str,
                          chain_id: str, seq_id: int, comp_id_conv_dict: dict) -> bool:
        """ Fix sequence ID of interesting loop.
        """

        chain_id_name = 'chain_code' if file_type == 'nef' else 'Entity_assembly_ID'
        seq_id_name = 'sequence_code' if file_type == 'nef' else 'Comp_index_ID'
        comp_id_name = 'residue_name' if file_type == 'nef' else 'Comp_ID'

        max_dim = 2

        if content_subtype in ('poly_seq', 'dist_restraint', 'rdc_restraint'):
            max_dim = 3

        elif content_subtype == 'dihed_restraint':
            max_dim = 5

        elif content_subtype == 'spectral_peak':

            try:

                _num_dim = get_first_sf_tag(sf, NUM_DIM_ITEMS[file_type])
                num_dim = int(_num_dim)

                if num_dim not in range(1, MAX_DIM_NUM_OF_SPECTRA):
                    raise ValueError()

            except ValueError:  # raised error already at __testIndexConsistency()
                return

            max_dim = num_dim + 1

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        if max_dim == 2:

            chain_id_col = loop.tags.index(chain_id_name) if chain_id_name in loop.tags else -1
            seq_id_col = loop.tags.index(seq_id_name) if seq_id_name in loop.tags else -1
            comp_id_col = loop.tags.index(comp_id_name) if comp_id_name in loop.tags else -1

            if -1 in (chain_id_col, seq_id_col, comp_id_col):
                return

            for row in loop:

                if row[chain_id_col] != chain_id:
                    continue

                _seq_id = row[seq_id_col]

                if _seq_id in EMPTY_VALUE or int(_seq_id) != seq_id:
                    continue

                comp_id = row[comp_id_col]

                if comp_id in comp_id_conv_dict:
                    row[comp_id_col] = comp_id_conv_dict[comp_id]

        else:

            for i in range(1, max_dim):

                _chain_id_name = chain_id_name + '_' + str(i)
                _seq_id_name = seq_id_name + '_' + str(i)
                _comp_id_name = comp_id_name + '_' + str(i)

                chain_id_col = loop.tags.index(_chain_id_name) if _chain_id_name in loop.tags else -1
                seq_id_col = loop.tags.index(_seq_id_name) if _seq_id_name in loop.tags else -1
                comp_id_col = loop.tags.index(_comp_id_name) if _comp_id_name in loop.tags else -1

                if -1 in (chain_id_col, seq_id_col, comp_id_col):
                    continue

                for row in loop:

                    if row[chain_id_col] != chain_id:
                        continue

                    _seq_id = row[seq_id_col]

                    if _seq_id in EMPTY_VALUE or int(_seq_id) != seq_id:
                        continue

                    comp_id = row[comp_id_col]

                    if comp_id in comp_id_conv_dict:
                        row[comp_id_col] = comp_id_conv_dict[comp_id]

    def fixEnumerationFailure(self, warnings) -> bool:
        """ Fix enumeration failures if possible.
        """

        if not self.__reg.combined_mode:
            return True

        if len(self.__reg.star_data) == 0:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']
        file_type = input_source_dic['file_type']

        if warnings is None:
            return True

        for w in warnings:

            if "be one of" not in w['description']:
                continue

            if w['description'].startswith('The mandatory type'):
                try:
                    g = CHK_DESC_MAND_PAT.search(w['description']).groups()
                except AttributeError:
                    g = CHK_DESC_MAND_ONE_PAT.search(w['description']).groups()
                mandatory_tag = True
            else:
                try:
                    g = CHK_DESC_PAT.search(w['description']).groups()
                except AttributeError:
                    g = CHK_DESC_ONE_PAT.search(w['description']).groups()
                mandatory_tag = False

            itName = g[0]
            itValue = None if g[1] in EMPTY_VALUE else g[1]
            itEnum = [str(e.strip("'")) for e in re.sub(r"\', \'", "\',\'", g[2]).split(',')]

            if self.__reg.star_data_type[0] == 'Entry' or self.__reg.star_data_type[0] == 'Saveframe':

                if 'sf_framecode' not in w:

                    err = "Could not specify 'sf_framecode' in NMR data processing report."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - {err}\n")

                else:

                    sf = self.__reg.dpA.getSaveframeByName(0, w['sf_framecode'])

                    if sf is None:

                        err = f"Could not specify {w['sf_framecode']!r} saveframe unexpectedly in {file_name!r} file."

                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - " + err)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - {err}\n")

                        continue

                    if 'category' not in w:

                        tagNames = [t[0] for t in sf.tags]

                        if itName not in tagNames:

                            err = f"Could not find saveframe tag {itName} in {w['sf_framecode']!r} saveframe, {file_name!r} file."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - {err}\n")

                        else:

                            itCol = tagNames.index(itName)

                            val = sf.tags[itCol][1]
                            if val in EMPTY_VALUE:
                                val = None

                            if val is itValue or val == itValue:

                                undefined_enums = ('undefined', 'unknown')

                                # assumes 'undefined', 'unknown' enum values at the end of the array
                                if (len(itEnum) == 2 and itEnum[1] in undefined_enums)\
                                   or (len(itEnum) == 3 and itEnum[1] in undefined_enums and itEnum[2] in undefined_enums):
                                    sf.tags[itCol][1] = itEnum[0]

                                # specific remediation follows
                                else:

                                    sf_category = get_first_sf_tag(sf, 'sf_category')

                                    try:

                                        content_subtype = next(c for c in input_source_dic['content_subtype']
                                                               if SF_CATEGORIES[file_type][c] == sf_category)

                                        if (file_type == 'nef' and itName == 'restraint_origin')\
                                           or (file_type == 'nmr-star' and itName == 'Constraint_type'):

                                            lp_data = next((lp['data'] for lp in self.__reg.lp_data[content_subtype]
                                                            if lp['file_name'] == file_name
                                                            and lp['sf_framecode'] == w['sf_framecode']), None)

                                            if lp_data is None:
                                                lp_category = LP_CATEGORIES[file_type][content_subtype]

                                                key_items = self.__reg.key_items[file_type][content_subtype]
                                                data_items = DATA_ITEMS[file_type][content_subtype]

                                                try:

                                                    lp_data = self.__reg.nefT.check_data(sf, lp_category, key_items, data_items,
                                                                                         None, None, None,
                                                                                         enforce_allowed_tags=(file_type == 'nmr-star'),
                                                                                         excl_missing_data=self.__reg.excl_missing_data)[0]

                                                    self.__reg.lp_data[content_subtype].append({'file_name': file_name,
                                                                                                'sf_framecode': w['sf_framecode'],
                                                                                                'data': lp_data})

                                                except Exception:
                                                    pass

                                            if lp_data is not None:

                                                if content_subtype == 'dist_restraint':

                                                    if mandatory_tag:
                                                        sf.tags[itCol][1] = 'undefined' if file_type == 'nef' else 'general distance'

                                                    # 'NOE', 'NOE build-up', 'NOE not seen', 'ROE', 'ROE build-up', 'hydrogen bond',
                                                    # 'disulfide bond', 'paramagnetic relaxation', 'symmetry', 'general distance'

                                                    elif self.__testDistRestraintAsHydrogenBond(lp_data):
                                                        sf.tags[itCol][1] = 'hbond' if file_type == 'nef' else 'hydrogen bond'

                                                    elif self.__testDistRestraintAsDisulfideBond(lp_data):
                                                        sf.tags[itCol][1] = 'disulfide_bond' if file_type == 'nef' else 'disulfide bond'

                                                    elif self.__testDistRestraintAsSymmetry(lp_data):
                                                        sf.tags[itCol][1] = 'symmetry'

                                                    else:
                                                        sf.tags[itCol][1] = 'undefined' if file_type == 'nef' else 'general distance'

                                                elif content_subtype == 'dihed_restraint':

                                                    if mandatory_tag:
                                                        sf.tags[itCol][1] = 'undefined'

                                                    # 'J-couplings', 'backbone chemical shifts'

                                                    elif self.__testDihedRestraintAsBackBoneChemShifts(lp_data):
                                                        sf.tags[itCol][1] = 'chemical_shift' if file_type == 'nef'\
                                                            else 'backbone chemical shifts'

                                                    # else:
                                                    #    sf.tags[itCol][1] = 'J-couplings'

                                                    else:
                                                        sf.tags[itCol][1] = 'undefined'

                                                elif content_subtype == 'rdc_restraint':

                                                    if mandatory_tag:
                                                        sf.tags[itCol][1] = 'undefined'
                                                    else:
                                                        sf.tags[itCol][1] = 'measured' if file_type == 'nef' else 'RDC'

                                        if (file_type == 'nef' and itName == 'potential_type')\
                                           or (file_type == 'nmr-star' and itName == 'Potential_type'):

                                            lp_data = next((lp['data'] for lp in self.__reg.lp_data[content_subtype]
                                                            if lp['file_name'] == file_name
                                                            and lp['sf_framecode'] == w['sf_framecode']), None)

                                            if lp_data is None:
                                                lp_category = LP_CATEGORIES[file_type][content_subtype]

                                                key_items = self.__reg.key_items[file_type][content_subtype]
                                                data_items = DATA_ITEMS[file_type][content_subtype]

                                                try:

                                                    lp_data = self.__reg.nefT.check_data(sf, lp_category, key_items, data_items,
                                                                                         None, None, None,
                                                                                         enforce_allowed_tags=(file_type == 'nmr-star'),
                                                                                         excl_missing_data=self.__reg.excl_missing_data)[0]

                                                    self.__reg.lp_data[content_subtype].append({'file_name': file_name,
                                                                                                'sf_framecode': w['sf_framecode'],
                                                                                                'data': lp_data})

                                                except Exception:
                                                    pass

                                            if lp_data is not None:

                                                # 'log-harmonic', 'parabolic'
                                                # 'square-well-parabolic', 'square-well-parabolic-linear',
                                                # 'upper-bound-parabolic', 'lower-bound-parabolic',
                                                # 'upper-bound-parabolic-linear', 'lower-bound-parabolic-linear'

                                                if mandatory_tag:
                                                    sf.tags[itCol][1] = 'undefined'
                                                elif self.__testRestraintPotentialSWP(content_subtype, lp_data):
                                                    sf.tags[itCol][1] = 'square-well-parabolic'
                                                elif self.__testRestraintPotentialSWPL(content_subtype, lp_data):
                                                    sf.tags[itCol][1] = 'square-well-parabolic-linear'
                                                elif self.__testRestraintPotentialUBP(content_subtype, lp_data):
                                                    sf.tags[itCol][1] = 'upper-bound-parabolic'
                                                elif self.__testRestraintPotentialLBP(content_subtype, lp_data):
                                                    sf.tags[itCol][1] = 'lower-bound-parabolic'
                                                elif self.__testRestraintPotentialUBPL(content_subtype, lp_data):
                                                    sf.tags[itCol][1] = 'upper-bound-parabolic-linear'
                                                elif self.__testRestraintPotentialLBPL(content_subtype, lp_data):
                                                    sf.tags[itCol][1] = 'lower-bound-parabolic-linear'
                                                elif self.__testRestraintPonentialLHorP(content_subtype, lp_data):
                                                    if content_subtype == 'dist_restraint':
                                                        sf.tags[itCol][1] = 'log-harmonic'
                                                    else:
                                                        sf.tags[itCol][1] = 'parabolic'
                                                else:
                                                    sf.tags[itCol][1] = 'undefined'

                                    except StopIteration:

                                        err = "Could not specify content_subtype in NMR data processing report."

                                        self.__reg.report.error.appendDescription('internal_error',
                                                                                  f"+{self.__class_name__}.fixEnumerationFailure() "
                                                                                  "++ Error  - " + err)

                                        if self.__reg.verbose:
                                            self.__reg.log.write(f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - {err}\n")

                    else:

                        loop = sf.get_loop(w['category'])

                        if itName not in loop.tags:

                            err = f"Could not find loop tag {itName} in {w['category']} category, "\
                                f"{w['sf_framecode']!r} saveframe, {file_name!r} file."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - {err}\n")

                        else:

                            itCol = loop.tags.index(itName)

                            for row in loop:

                                val = row[itCol]

                                if val in EMPTY_VALUE:
                                    continue

                                if val == itValue:

                                    if len(itEnum) == 1:
                                        row[itCol] = itEnum[0]

                                    elif file_type == 'nef' and itName == 'folding':

                                        # 'circular', 'mirror', 'none'

                                        if val in ('aliased', 'folded', 'not observed'):
                                            if val == 'aliased':
                                                row[itCol] = 'mirror'
                                            elif val == 'folded':
                                                row[itCol] = 'circular'
                                            else:
                                                row[itCol] = 'none'

                                    elif file_type == 'nmr-star' and itName == 'Under_sampling_type':

                                        # 'aliased', 'folded', 'not observed'

                                        if val in ('circular', 'mirror', 'none'):
                                            if val == 'circular':
                                                row[itCol] = 'folded'
                                            elif val == 'mirror':
                                                row[itCol] = 'aliased'
                                            else:
                                                row[itCol] = 'not observed'

            else:

                err = f"Unexpected PyNMRSTAR object type {self.__reg.star_data_type[0]} found about {file_name!r} file."

                self.__reg.report.error.appendDescription('internal_error',
                                                          f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - " + err)

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.fixEnumerationFailure() ++ Error  - {err}\n")

        return True

    def __testDistRestraintAsHydrogenBond(self, lp_data: List[dict]) -> bool:
        """ Detect whether given distance restraints are derived from hydrogen bonds.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None or len(lp_data) == 0:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
        chain_id_1_name = item_names['chain_id_1']
        chain_id_2_name = item_names['chain_id_2']
        seq_id_1_name = item_names['seq_id_1']
        seq_id_2_name = item_names['seq_id_2']
        atom_id_1_name = item_names['atom_id_1']
        atom_id_2_name = item_names['atom_id_2']

        def ext_atom_types(row):
            return (row[chain_id_1_name], row[chain_id_2_name],
                    row[seq_id_1_name], row[seq_id_2_name],
                    row[atom_id_1_name][0], row[atom_id_2_name][0])

        target_value_name = item_names['target_value']
        if 'target_value_alt' in item_names and target_value_name not in lp_data[0].keys():
            target_value_name = item_names['target_value_alt']
        lower_limit_name = item_names['lower_limit']
        upper_limit_name = item_names['upper_limit']
        lower_linear_limit_name = item_names['lower_linear_limit']
        upper_linear_limit_name = item_names['upper_linear_limit']

        def get_est_value_range(row):
            target_value = row.get(target_value_name)
            upper_limit = lower_limit = None

            if target_value is None:

                if has_key_value(row, lower_limit_name)\
                        and has_key_value(row, upper_limit_name):
                    target_value = (row[lower_limit_name] + row[upper_limit_name]) / 2.0
                    upper_limit = row[lower_limit_name]
                    lower_limit = row[upper_limit_name]

                elif has_key_value(row, lower_linear_limit_name)\
                        and has_key_value(row, upper_linear_limit_name):
                    target_value = (row[lower_linear_limit_name] + row[upper_linear_limit_name]) / 2.0

                elif has_key_value(row, upper_linear_limit_name):
                    target_value = row[upper_linear_limit_name]
                    upper_limit = target_value

                elif has_key_value(row, upper_limit_name):
                    target_value = row[upper_limit_name]
                    upper_limit = target_value

                elif has_key_value(row, lower_linear_limit_name):
                    target_value = row[lower_linear_limit_name]
                    lower_limit = target_value

                elif has_key_value(row, lower_limit_name):
                    target_value = row[lower_limit_name]
                    lower_limit = target_value

            return target_value, upper_limit, lower_limit

        try:

            for row in lp_data:

                chain_id_1, chain_id_2, seq_id_1, seq_id_2, \
                    atom_id_1_, atom_id_2_ = ext_atom_types(row)

                if chain_id_1 == chain_id_2 and seq_id_1 == seq_id_2:
                    return False

                target_value, upper_limit, lower_limit = get_est_value_range(row)

                if target_value is None:
                    return False

                if upper_limit is not None:
                    target_value -= 0.4

                if lower_limit is not None:
                    target_value += 0.4

                if (atom_id_1_ == 'F' and atom_id_2_ in PROTON_BEGIN_CODE) or (atom_id_2_ == 'F' and atom_id_1_ in PROTON_BEGIN_CODE):

                    if target_value < 1.2 or target_value > 1.5:
                        return False

                elif (atom_id_1_ == 'F' and atom_id_2_ == 'F') or (atom_id_2_ == 'F' and atom_id_1_ == 'F'):

                    if target_value < 2.2 or target_value > 2.5:
                        return False

                elif (atom_id_1_ == 'O' and atom_id_2_ in PROTON_BEGIN_CODE) or (atom_id_2_ == 'O' and atom_id_1_ in PROTON_BEGIN_CODE):

                    if target_value < 1.5 or target_value > 2.5:
                        return False

                elif (atom_id_1_ == 'O' and atom_id_2_ == 'N') or (atom_id_2_ == 'O' and atom_id_1_ == 'N'):

                    if target_value < 2.5 or target_value > 3.5:
                        return False

                elif (atom_id_1_ == 'O' and atom_id_2_ == 'O') or (atom_id_2_ == 'O' and atom_id_1_ == 'O'):

                    if target_value < 2.5 or target_value > 3.5:
                        return False

                elif (atom_id_1_ == 'N' and atom_id_2_ in PROTON_BEGIN_CODE) or (atom_id_2_ == 'N' and atom_id_1_ in PROTON_BEGIN_CODE):

                    if target_value < 1.5 or target_value > 2.5:
                        return False

                elif (atom_id_1_ == 'N' and atom_id_2_ == 'N') or (atom_id_2_ == 'N' and atom_id_1_ == 'N'):

                    if target_value < 2.5 or target_value > 3.5:
                        return False

                else:
                    return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testDistRestraintAsHydrogenBond() "
                                                      "++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testDistRestraintAsHydrogenBond() "
                                     f"++ Error  - {str(e)}\n")

            return False

        return True

    def __testDistRestraintAsDisulfideBond(self, lp_data: List[dict]) -> bool:
        """ Detect whether given distance restraints are derived from disulfide bonds.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None or len(lp_data) == 0:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
        chain_id_1_name = item_names['chain_id_1']
        chain_id_2_name = item_names['chain_id_2']
        seq_id_1_name = item_names['seq_id_1']
        seq_id_2_name = item_names['seq_id_2']
        atom_id_1_name = item_names['atom_id_1']
        atom_id_2_name = item_names['atom_id_2']

        def ext_atom_types(row):
            return (row[chain_id_1_name], row[chain_id_2_name],
                    row[seq_id_1_name], row[seq_id_2_name],
                    row[atom_id_1_name][0], row[atom_id_2_name][0])

        target_value_name = item_names['target_value']
        if 'target_value_alt' in item_names and target_value_name not in lp_data[0].keys():
            target_value_name = item_names['target_value_alt']
        lower_limit_name = item_names['lower_limit']
        upper_limit_name = item_names['upper_limit']
        lower_linear_limit_name = item_names['lower_linear_limit']
        upper_linear_limit_name = item_names['upper_linear_limit']

        def get_est_value_range(row):
            target_value = row.get(target_value_name)
            upper_limit = lower_limit = None

            if target_value is None:

                if has_key_value(row, lower_limit_name)\
                        and has_key_value(row, upper_limit_name):
                    target_value = (row[lower_limit_name] + row[upper_limit_name]) / 2.0
                    upper_limit = row[lower_limit_name]
                    lower_limit = row[upper_limit_name]

                elif has_key_value(row, lower_linear_limit_name)\
                        and has_key_value(row, upper_linear_limit_name):
                    target_value = (row[lower_linear_limit_name] + row[upper_linear_limit_name]) / 2.0

                elif has_key_value(row, upper_linear_limit_name):
                    target_value = row[upper_linear_limit_name]
                    upper_limit = target_value

                elif has_key_value(row, upper_limit_name):
                    target_value = row[upper_limit_name]
                    upper_limit = target_value

                elif has_key_value(row, lower_linear_limit_name):
                    target_value = row[lower_linear_limit_name]
                    lower_limit = target_value

                elif has_key_value(row, lower_limit_name):
                    target_value = row[lower_limit_name]
                    lower_limit = target_value

            return target_value, upper_limit, lower_limit

        try:

            for row in lp_data:
                chain_id_1, chain_id_2, seq_id_1, seq_id_2, \
                    atom_id_1_, atom_id_2_ = ext_atom_types(row)

                if chain_id_1 == chain_id_2 and seq_id_1 == seq_id_2:
                    return False

                target_value, upper_limit, lower_limit = get_est_value_range(row)

                if target_value is None:
                    return False

                if upper_limit is not None:
                    target_value -= 0.4

                if lower_limit is not None:
                    target_value += 0.4

                if atom_id_1_ == 'S' and atom_id_2_ == 'S':

                    if target_value < 1.9 or target_value > 2.3:
                        return False

                else:
                    return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testDistRestraintAsDisulfideBond() "
                                                      "++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testDistRestraintAsDisulfideBond() "
                                     f"++ Error  - {str(e)}\n")

            return False

        return True

    def __testDistRestraintAsSymmetry(self, lp_data: List[dict]) -> bool:
        """ Detect whether given distance restraints are derived from symmetric assembly.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
        chain_id_1_name = item_names['chain_id_1']
        chain_id_2_name = item_names['chain_id_2']
        seq_id_1_name = item_names['seq_id_1']
        seq_id_2_name = item_names['seq_id_2']
        comp_id_1_name = item_names['comp_id_1']
        comp_id_2_name = item_names['comp_id_2']

        def ext_comp_names(row):
            return (row[chain_id_1_name], row[chain_id_2_name],
                    row[seq_id_1_name], row[seq_id_2_name],
                    row[comp_id_1_name], row[comp_id_2_name])

        try:

            for row in lp_data:
                chain_id_1, chain_id_2, seq_id_1, seq_id_2, \
                    comp_id_1, comp_id_2 = ext_comp_names(row)

                if chain_id_1 == chain_id_2:
                    return False

                has_symmetry = False

                for _row in lp_data:

                    if _row is row:
                        continue

                    _chain_id_1, _chain_id_2, _seq_id_1, _seq_id_2, \
                        _comp_id_1, _comp_id_2 = ext_comp_names(_row)

                    if _chain_id_1 != _chain_id_2 and _chain_id_1 != chain_id_1 and _chain_id_2 != chain_id_2:

                        if seq_id_1 == _seq_id_1 and comp_id_1 == _comp_id_1\
                           and seq_id_2 == _seq_id_2 and comp_id_2 == _comp_id_2:
                            has_symmetry = True
                            break

                        if seq_id_1 == _seq_id_2 and comp_id_1 == _comp_id_2\
                           and seq_id_2 == _seq_id_1 and comp_id_2 == _comp_id_1:
                            has_symmetry = True
                            break

                if not has_symmetry:
                    return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testDistRestraintAsSymmetry() "
                                                      "++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testDistRestraintAsSymmetry() "
                                     f"++ Error  - {str(e)}\n")

            return False

        return True

    def __testDihedRestraintAsBackBoneChemShifts(self, lp_data: List[dict]) -> bool:
        """ Detect whether given dihedral angle restraints are derived from backbone chemical shifts.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']
        file_type = input_source_dic['file_type']

        item_names = ITEM_NAMES_IN_DIHED_LOOP[file_type]
        chain_id_1_name = item_names['chain_id_1']
        chain_id_2_name = item_names['chain_id_2']
        chain_id_3_name = item_names['chain_id_3']
        chain_id_4_name = item_names['chain_id_4']
        seq_id_1_name = item_names['seq_id_1']
        seq_id_2_name = item_names['seq_id_2']
        seq_id_3_name = item_names['seq_id_3']
        seq_id_4_name = item_names['seq_id_4']
        comp_id_1_name = item_names['comp_id_1']
        comp_id_2_name = item_names['comp_id_2']
        comp_id_3_name = item_names['comp_id_3']
        comp_id_4_name = item_names['comp_id_4']
        atom_id_1_name = item_names['atom_id_1']
        atom_id_2_name = item_names['atom_id_2']
        atom_id_3_name = item_names['atom_id_3']
        atom_id_4_name = item_names['atom_id_4']
        angle_type_name = item_names['angle_type']
        lower_limit_name = item_names['lower_limit']
        upper_limit_name = item_names['upper_limit']

        def ext_atoms(row):
            return ({'chain_id': row[chain_id_1_name], 'seq_id': row[seq_id_1_name],
                     'comp_id': row[comp_id_1_name], 'atom_id': row[atom_id_1_name]},
                    {'chain_id': row[chain_id_2_name], 'seq_id': row[seq_id_2_name],
                     'comp_id': row[comp_id_2_name], 'atom_id': row[atom_id_2_name]},
                    {'chain_id': row[chain_id_3_name], 'seq_id': row[seq_id_3_name],
                     'comp_id': row[comp_id_3_name], 'atom_id': row[atom_id_3_name]},
                    {'chain_id': row[chain_id_4_name], 'seq_id': row[seq_id_4_name],
                     'comp_id': row[comp_id_4_name], 'atom_id': row[atom_id_4_name]})

        dh_chain_ids, cs_chain_ids = set(), set()
        dh_seq_ids, cs_seq_ids = {}, {}

        try:

            for row in lp_data:
                atom1, atom2, atom3, atom4 = ext_atoms(row)

                angle_type = row[angle_type_name]

                if angle_type in EMPTY_VALUE:
                    continue

                angle_type = angle_type.lower()

                if angle_type not in ('phi', 'psi'):
                    return False

                peptide, nucleotide, carbohydrate = self.__reg.csStat.getTypeOfCompId(atom2['comp_id'])

                if not peptide:
                    return False

                plane_like = is_like_planality_boundary(row, lower_limit_name, upper_limit_name)

                data_type = getTypeOfDihedralRestraint(peptide, nucleotide, carbohydrate,
                                                       [atom1, atom2, atom3, atom4], plane_like)

                if data_type is None or data_type.lower() not in ('phi', 'psi'):
                    return False

                chain_id = atom1['chain_id']
                dh_chain_ids.add(chain_id)

                seq_ids = [atom1['seq_id'], atom2['seq_id'], atom3['seq_id'], atom4['seq_id']]
                seq_id_common = collections.Counter(seq_ids).most_common()

                if chain_id not in dh_seq_ids:
                    dh_seq_ids[chain_id] = set()

                dh_seq_ids[chain_id].add(seq_id_common[0][0])

            # check backbone CA atoms

            content_subtype = 'chem_shift'

            if not has_key_value(input_source_dic['content_subtype'], content_subtype):
                return False

            sf_category = SF_CATEGORIES[file_type][content_subtype]
            lp_category = LP_CATEGORIES[file_type][content_subtype]

            key_items = self.__reg.key_items[file_type][content_subtype]
            data_items = DATA_ITEMS[file_type][content_subtype]

            item_names = ITEM_NAMES_IN_CS_LOOP[file_type]
            chain_id_name = item_names['chain_id']
            seq_id_name = item_names['seq_id']
            atom_id_name = item_names['atom_id']

            for sf in self.__reg.star_data[0].get_saveframes_by_category(sf_category):
                sf_framecode = get_first_sf_tag(sf, 'sf_framecode')

                if self.__reg.report.error.exists(file_name, sf_framecode):
                    continue

                lp_data = next((lp['data'] for lp in self.__reg.lp_data[content_subtype]
                                if lp['file_name'] == file_name and lp['sf_framecode'] == sf_framecode), None)

                if lp_data is None:

                    try:

                        lp_data = self.__reg.nefT.check_data(sf, lp_category, key_items, data_items, None, None, None,
                                                             enforce_allowed_tags=(file_type == 'nmr-star'),
                                                             excl_missing_data=self.__reg.excl_missing_data)[0]

                        self.__reg.lp_data[content_subtype].append({'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                    'data': lp_data})

                    except Exception:
                        pass

                if lp_data is not None:

                    for row in lp_data:
                        chain_id = row[chain_id_name]
                        seq_id = row[seq_id_name]
                        atom_id = row[atom_id_name]

                        if chain_id in dh_chain_ids and seq_id in dh_seq_ids[chain_id] and atom_id == 'CA':
                            cs_chain_ids.add(chain_id)

                            if chain_id not in cs_seq_ids:
                                cs_seq_ids[chain_id] = set()

                            cs_seq_ids[chain_id].add(seq_id)

            if cs_chain_ids != dh_chain_ids:
                return False

            for k, v in dh_seq_ids.items():

                if len(cs_seq_ids[k] & v) < len(v) * 0.8:
                    return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testDihedRestraintAsBackBoneChemShifts() "
                                                      "++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testDihedRestraintAsBackBoneChemShifts() "
                                     f"++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPotentialSWP(self, content_subtype: str, lp_data: List[dict]) -> bool:
        """ Detect square-well-parabolic potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if has_key_value(row, lower_limit_name)\
                   and has_key_value(row, upper_limit_name)\
                   and not has_key_value(row, lower_linear_limit_name)\
                   and not has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialSWP() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialSWP() ++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPotentialSWPL(self, content_subtype: str, lp_data: List[str]) -> bool:
        """ Detect square-well-parabolic-linear potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if has_key_value(row, lower_limit_name)\
                   and has_key_value(row, upper_limit_name)\
                   and has_key_value(row, lower_linear_limit_name)\
                   and has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialSWPL() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialSWPL() ++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPotentialUBP(self, content_subtype: str, lp_data: List[dict]) -> bool:
        """ Detect upper-bound-parabolic potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if not has_key_value(row, lower_limit_name)\
                   and has_key_value(row, upper_limit_name)\
                   and not has_key_value(row, lower_linear_limit_name)\
                   and not has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialUBP() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialUBP() ++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPotentialLBP(self, content_subtype: str, lp_data: List[str]) -> bool:
        """ Detect lower-bound-parabolic potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if has_key_value(row, lower_limit_name)\
                   and not has_key_value(row, upper_limit_name)\
                   and not has_key_value(row, lower_linear_limit_name)\
                   and not has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialLBP() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialLBP() ++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPotentialUBPL(self, content_subtype: str, lp_data: List[dict]) -> bool:
        """ Detect upper-bound-parabolic-linear potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if not has_key_value(row, lower_limit_name)\
                   and has_key_value(row, upper_limit_name)\
                   and not has_key_value(row, lower_linear_limit_name)\
                   and has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialUBPL() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialUBPL() ++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPotentialLBPL(self, content_subtype: str, lp_data: List[dict]) -> bool:
        """ Detect lower-bound-parabolic-linear potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if has_key_value(row, lower_limit_name)\
                   and not has_key_value(row, upper_limit_name)\
                   and has_key_value(row, lower_linear_limit_name)\
                   and not has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialLBPL() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialLBPL() ++ Error  - {str(e)}\n")

            return False

        return True

    def __testRestraintPonentialLHorP(self, content_subtype: str, lp_data: List[dict]) -> bool:
        """ Detect log-harmonic or parabolic potential.
        """

        if not self.__reg.combined_mode:
            return True

        if lp_data is None or len(lp_data) == 0:
            return False

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        try:

            item_names = POTENTIAL_ITEMS[file_type][content_subtype]
            target_value_name = item_names['target_value']
            if 'target_value_alt' in item_names and target_value_name not in lp_data[0].keys():
                target_value_name = item_names['target_value_alt']
            lower_limit_name = item_names['lower_limit']
            upper_limit_name = item_names['upper_limit']
            lower_linear_limit_name = item_names['lower_linear_limit']
            upper_linear_limit_name = item_names['upper_linear_limit']

            for row in lp_data:
                if has_key_value(row, target_value_name)\
                   and not has_key_value(row, lower_limit_name)\
                   and not has_key_value(row, upper_limit_name)\
                   and not has_key_value(row, lower_linear_limit_name)\
                   and not has_key_value(row, upper_linear_limit_name):
                    continue

                return False

        except Exception as e:

            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.__testRestraintPotentialLHorP() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__testRestraintPotentialLHorP() ++ Error  - {str(e)}\n")

            return False

        return True

    def updatePolymerSequence(self) -> Tuple[bool, Optional[pynmrstar.Saveframe]]:
        """ Update polymer sequence.
        """

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']
        file_type = input_source_dic['file_type']

        master_entry = self.__reg.star_data[0]

        content_subtype = 'poly_seq'

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        key_items = self.__reg.key_items[file_type][content_subtype]
        data_items = DATA_ITEMS[file_type][content_subtype]

        orig_lp_data = None

        has_res_var_dat = has_nef_index = has_entry_id = False

        sf_framecode = 'assembly'

        for sf in master_entry.get_saveframes_by_category(sf_category):
            sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

            try:

                _lp_category = '_Entity_assembly'

                _loop = sf.get_loop(_lp_category)

                tags = ['Conformational_isomer', 'Details']

                dat = _loop.get_tag(tags)

                for row in dat:
                    if row[0] == 'yes' and 'Conformational isomer' in row[1]:
                        return False, None

            except KeyError:
                pass

            orig_lp_data = next((lp['data'] for lp in self.__reg.lp_data[content_subtype]
                                 if lp['file_name'] == file_name and lp['sf_framecode'] == sf_framecode), None)

            if orig_lp_data is None:

                try:

                    orig_lp_data = self.__reg.nefT.check_data(sf, lp_category, key_items, data_items, None, None, None,
                                                              enforce_allowed_tags=(file_type == 'nmr-star'),
                                                              excl_missing_data=self.__reg.excl_missing_data)[0]

                except Exception:
                    pass

            if orig_lp_data is not None and len(orig_lp_data) > 0:

                if file_type == 'nef':
                    if 'residue_variant' in orig_lp_data[0]:
                        if any(True for _row in orig_lp_data if _row['residue_variant'] not in EMPTY_VALUE):
                            has_res_var_dat = True

                else:
                    if 'Auth_variant_ID' in orig_lp_data[0]:
                        if any(True for _row in orig_lp_data if _row['Auth_variant_ID'] not in EMPTY_VALUE):
                            has_res_var_dat = True

                    if 'NEF_index' in orig_lp_data[0]:
                        if any(True for _row in orig_lp_data if _row['NEF_index'] not in EMPTY_VALUE):
                            has_nef_index = True

                    if 'Entry_ID' in orig_lp_data[0]:
                        has_entry_id = True

            elif not self.__reg.has_star_entity and not self.__reg.update_poly_seq and file_type == 'nef':  # DAOTHER-6694, 8751
                return False, None

        orig_asm_sf = None

        try:
            orig_asm_sf = master_entry.get_saveframes_by_category(sf_category)[0]
        except IndexError:
            pass

        entity_assembly = self.__reg.caC['entity_assembly']

        if entity_assembly is None:
            return False, None

        components_ex_water = 0
        for item in entity_assembly:
            if isinstance(item['entity_copies'], int):
                components_ex_water += item['entity_copies']

        ligand_total = sum(len(item['label_asym_id'].split(',')
                               if 'fixed_label_asym_id' not in item else item['fixed_label_asym_id'].split(','))
                           for item in entity_assembly
                           if item['entity_type'] == 'non-polymer' and 'ION' not in item['entity_desc'])
        ion_total = sum(len(item['label_asym_id'].split(',')
                            if 'fixed_label_asym_id' not in item else item['fixed_label_asym_id'].split(','))
                        for item in entity_assembly
                        if item['entity_type'] == 'non-polymer' and 'ION' in item['entity_desc'])

        self.__reg.sail_flag = False

        if self.__reg.cR.hasItem('struct_keywords', 'text'):
            struct_keywords = self.__reg.cR.getDictList('struct_keywords')
            text = struct_keywords[0]['text'].lower()
            if 'sail' in text or 'stereo-array isotope labeling' in text:
                self.__reg.sail_flag = True

        if self.__reg.cR.hasItem('pdbx_nmr_exptl_sample', 'isotopic_labeling'):
            exptl_sample = self.__reg.cR.getDictList('pdbx_nmr_exptl_sample')
            for item in exptl_sample:
                text = item['isotopic_labeling'].lower()
                if 'sail' in text or 'stereo-array isotope labeling' in text:
                    self.__reg.sail_flag = True
                    break

        chem_comp = self.__reg.cR.getDictList('chem_comp')

        self.__paramag = len(chem_comp) > 0\
            and any(True for cc in chem_comp if cc['type'] == 'non-poly' and cc['id'] in PARAMAGNETIC_ELEMENTS)

        has_cys = any(True for cc in chem_comp
                      if ((cc['type'] == 'L-peptide linking' and cc['id'] == 'CYS')
                          or (cc['type'] == 'D-peptide linking' and cc['id'] == 'DCY')))
        if has_cys:
            cys_total = 0
            for ps in self.__reg.caC['polymer_sequence']:
                cys_total += ps['comp_id'].count('CYS') + ps['comp_id'].count('DCY')
            disul_cys = other_cys = 0
            if self.__reg.cR.hasCategory('struct_conn'):
                bonds = self.__reg.cR.getDictList('struct_conn')
                for bond in bonds:
                    auth_comp_id_1 = bond['ptnr1_auth_comp_id']
                    atom_id_1 = bond['ptnr1_label_atom_id']
                    auth_comp_id_2 = bond['ptnr2_auth_comp_id']
                    atom_id_2 = bond['ptnr2_label_atom_id']

                    if auth_comp_id_1 in ('CYS', 'DCY') and atom_id_1 == 'SG':
                        if auth_comp_id_2 in ('CYS', 'DCY') and atom_id_2 == 'SG':
                            disul_cys += 1
                        else:
                            other_cys += 1

                    if auth_comp_id_2 in ('CYS', 'DCY') and atom_id_2 == 'SG':
                        if auth_comp_id_1 in ('CYS', 'DCY') and atom_id_1 == 'SG':
                            disul_cys += 1
                        else:
                            other_cys += 1

            free_cys = cys_total - disul_cys - other_cys

            if free_cys > 0:
                if free_cys == cys_total:
                    thiol_state = 'all free'
                elif disul_cys > 0 and other_cys > 0:
                    thiol_state = 'free disulfide and other bound'
                elif other_cys == 0:
                    thiol_state = 'free and disulfide bound'
                else:
                    thiol_state = 'free and other bound'
            else:
                if disul_cys > 0 and other_cys > 0:
                    thiol_state = 'disulfide and other bound'
                elif other_cys == 0:
                    thiol_state = 'all disulfide bound'
                else:
                    thiol_state = 'all other bound'
        else:
            thiol_state = 'not present'

        formula_weight = 0.0
        for item in entity_assembly:
            fw = item['entity_fw']
            num = item['entity_copies']
            if isinstance(fw, float) and isinstance(num, int):
                formula_weight += fw * num
            else:
                formula_weight = '.'
                break

        ec_numbers = []
        for item in entity_assembly:
            if 'entity_ec' in item and item['entity_ec'] not in EMPTY_VALUE and item['entity_ec'] not in ec_numbers:
                ec_numbers.append(item['entity_ec'])
        if len(ec_numbers) == 0:
            ec_number = '.'
        else:
            ec_number = ','.join(ec_numbers)

        details = ''
        for item in entity_assembly:
            if 'entity_details' not in item:
                continue
            _details = item['entity_details'].strip().rstrip('\n')
            if _details in EMPTY_VALUE or _details + '\n' in details:
                continue
            if len(details.strip()) > 0:
                details += _details + '\n'
        if len(details) == 0:
            details = '.'
        else:
            details = details[:-1]
            if len(details) == 0:
                details = '.'

        asm_sf = pynmrstar.Saveframe.from_scratch(sf_framecode)
        asm_sf.set_tag_prefix(SF_TAG_PREFIXES[file_type][content_subtype])

        if file_type == 'nef':
            asm_sf.add_tag('sf_category', SF_CATEGORIES[file_type][content_subtype])
            asm_sf.add_tag('sf_framecode', sf_framecode)

        else:
            asm_sf.add_tag('Sf_category', SF_CATEGORIES[file_type][content_subtype])
            asm_sf.add_tag('Sf_framecode', sf_framecode)
            asm_sf.add_tag('Entry_ID', self.__reg.entry_id)
            asm_sf.add_tag('ID', 1)
            assembly_name = self.__reg.assembly_name
            if assembly_name in EMPTY_VALUE and self.__reg.cR.hasItem('struct', 'pdbx_descriptor'):
                struct = self.__reg.cR.getDictList('struct')
                assembly_name = struct[0]['pdbx_descriptor']
            asm_sf.add_tag('Name', assembly_name)
            asm_sf.add_tag('BMRB_code', None)
            asm_sf.add_tag('Number_of_components', components_ex_water if components_ex_water > 0 else None)
            asm_sf.add_tag('Organic_ligands', ligand_total if ligand_total > 0 else None)
            asm_sf.add_tag('Metal_ions', ion_total if ion_total > 0 else None)
            asm_sf.add_tag('Non_standard_bonds', None)  # filled 'yes' if the assembly contains non-standard bonds
            asm_sf.add_tag('Ambiguous_conformational_states', None)
            asm_sf.add_tag('Ambiguous_chem_comp_sites', None)
            asm_sf.add_tag('Molecules_in_chemical_exchange', None)  # filled 'yes' if conformational isomers exist
            asm_sf.add_tag('Paramagnetic', 'yes' if self.__paramag else 'no')
            asm_sf.add_tag('Thiol_state', thiol_state)
            asm_sf.add_tag('Molecular_mass', f'{formula_weight:.3f}' if isinstance(formula_weight, float) else None)
            asm_sf.add_tag('Enzyme_commission_number', ec_number)
            asm_sf.add_tag('Details', details)
            asm_sf.add_tag('DB_query_date', None)
            asm_sf.add_tag('DB_query_revised_last_date', None)

        entity_type_of = {item['entity_id']: item['entity_type'] for item in entity_assembly}
        entity_total = {entity_id: len([item for item in entity_assembly if item['entity_id'] == entity_id])
                        for entity_id in entity_type_of.keys()}
        entity_count = {entity_id: 0 for entity_id in entity_type_of.keys()}

        if file_type == 'nmr-star':

            # refresh _Entity_assembly loop

            lp_category = '_Entity_assembly'

            ea_loop = pynmrstar.Loop.from_scratch(lp_category)

            ea_key_items = [{'name': 'ID', 'type': 'positive-int'},
                            {'name': 'Entity_assembly_name', 'type': 'str'},
                            {'name': 'Entity_ID', 'type': 'positive-int', 'default': '1'},
                            {'name': 'Entity_label', 'type': 'str'},
                            ]
            ea_data_items = [{'name': 'Asym_ID', 'type': 'str', 'mandatory': False},  # label_asym_id
                             {'name': 'PDB_chain_ID', 'type': 'str', 'mandatory': False},  # auth_asym_id
                             {'name': 'Experimental_data_reported', 'type': 'enum', 'mandatory': False,
                              'enum': ('no', 'yes')},
                             {'name': 'Physical_state', 'type': 'enum', 'mandatory': False,
                              'enum': ('native', 'denatured', 'molten globule', 'unfolded',
                                       'intrinsically disordered', 'partially disordered', 'na')},
                             {'name': 'Conformational_isomer', 'type': 'enum', 'mandatory': False,
                              'enum': ('no', 'yes')},
                             {'name': 'Chemical_exchange_state', 'type': 'enum', 'mandatory': False,
                              'enum': ('no', 'yes')},
                             {'name': 'Magnetic_equivalence_group_code', 'type': 'str', 'mandatory': False},
                             {'name': 'Role', 'type': 'str', 'mandatory': False},
                             {'name': 'Details', 'type': 'str', 'default': '.', 'mandatory': False},
                             {'name': 'Assembly_ID', 'type': 'pointer-index', 'mandatory': False, 'default': '1', 'default-from': 'parent'},
                             {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                             ]

            tags = [lp_category + '.' + _item['name'] for _item in ea_key_items]
            tags.extend([lp_category + '.' + _item['name'] for _item in ea_data_items])

            ea_loop.add_tag(tags)

            for item in entity_assembly:
                entity_id = item['entity_id']
                entity_type = item['entity_type']
                entity_count[entity_id] += 1

                row = [None] * len(tags)

                row[0] = item['entity_assembly_id']
                row[1] = (f'entity_{entity_id}' + ('' if entity_total[entity_id] == 1 else f'_{entity_count[entity_id]}'))\
                    if entity_type not in ('non-polymer', 'water') else f"entity_{item['comp_id']}"
                item['entity_assembly_name'] = row[1]
                row[2] = item['entity_id']
                row[3] = f'$entity_{entity_id}' if entity_type not in ('non-polymer', 'water') else f"$entity_{item['comp_id']}"
                _label_asym_id = 'label_asym_id' if 'fixed_label_asym_id' not in item else 'fixed_label_asym_id'
                _auth_asym_id = 'auth_asym_id' if 'fixed_auth_asym_id' not in item else 'fixed_auth_asym_id'
                row[4] = item[_label_asym_id]
                row[5] = item[_auth_asym_id]
                if len(self.__reg.label_asym_id_with_exptl_data) > 0:
                    if any(True for label_asym_id in item[_label_asym_id].split(',')
                           if label_asym_id in self.__reg.label_asym_id_with_exptl_data):
                        row[6] = 'yes'
                # Physical_state
                # Conformational_isomer
                if len(self.__reg.auth_asym_ids_with_chem_exch) > 0:
                    if any(True for auth_asym_id in item[_auth_asym_id].split(',')
                           if auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch.keys()):
                        row[8] = row[9] = 'yes'
                if entity_total[entity_id] > 0 and entity_type == 'polymer' and len(self.__reg.label_asym_id_with_exptl_data) > 0:
                    equiv_entity_assemblies = [_item for _item in entity_assembly if _item['entity_id'] == entity_id]
                    _item = next((_item for _item in equiv_entity_assemblies
                                  if any(True for label_asym_id in _item[_label_asym_id].split(',')
                                         if label_asym_id in self.__reg.label_asym_id_with_exptl_data)), None)
                    if _item is not None:
                        group_id = sorted(sorted(set(_item[_label_asym_id].split(','))), key=len)[0]
                        if any(True for __item in equiv_entity_assemblies
                               if not any(True for label_asym_id in __item[_label_asym_id].split(',')
                                          if label_asym_id in self.__reg.label_asym_id_with_exptl_data)):
                            if _item == item or row[6] is None or row[6] == 'no':
                                row[10] = group_id
                row[11], row[12] = item['entity_role'], item['entity_details']
                row[13], row[14] = 1, self.__reg.entry_id

                if len(self.__reg.auth_asym_ids_with_chem_exch) > 0:
                    auth_asym_id = row[5]
                    if auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch.keys():
                        conformational_states = len(self.__reg.auth_asym_ids_with_chem_exch[auth_asym_id]) + 1
                        beg_model_id = 1
                        end_model_id = self.__reg.total_models // conformational_states
                        seq_ids = [k for k, v in self.__reg.auth_seq_ids_with_chem_exch.items()
                                   if v['chain_id'] == auth_asym_id]
                        if len(seq_ids) > 0:
                            row[12] = f'Conformational isomer 1, PDB_model_num range: {beg_model_id}-{end_model_id}, '\
                                f'original sequence number range: {min(seq_ids)}-{max(seq_ids)}'
                            set_sf_tag(asm_sf, 'Molecules_in_chemical_exchange', 'yes')

                ea_loop.add_data(row)

            if len(self.__reg.auth_asym_ids_with_chem_exch) > 0:
                _entity_assembly_id = ea_loop.data[-1][0]
                for idx, item in enumerate(entity_assembly):
                    entity_type = item['entity_type']
                    if entity_type in ('non-polymer', 'water'):
                        continue
                    auth_asym_id = item['auth_asym_id']
                    if auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch.keys():
                        for offset, _auth_asym_id in enumerate(self.__reg.auth_asym_ids_with_chem_exch[auth_asym_id], start=2):
                            row = ea_loop.data[idx]
                            _row = copy.copy(row)
                            _entity_assembly_id += 1
                            _row[0] = _entity_assembly_id
                            _row[1] = f'entity_{entity_id}_{offset}'
                            _row[5] = _auth_asym_id
                            conformational_states = len(self.__reg.auth_asym_ids_with_chem_exch[auth_asym_id]) + 1
                            model_ids_per_state = self.__reg.total_models // conformational_states
                            beg_model_id = 1 + model_ids_per_state * (offset - 1)
                            end_model_id = model_ids_per_state * offset
                            seq_ids = [k for k, v in self.__reg.auth_seq_ids_with_chem_exch.items()
                                       if v['chain_id'] == _auth_asym_id]
                            if len(seq_ids) > 0:
                                _row[12] = f'Conformational isomer {offset}, PDB_model_num range: {beg_model_id}-{end_model_id}, '\
                                    f'original sequence number range: {min(seq_ids)}-{max(seq_ids)}'

                            ea_loop.add_data(_row)

            asm_sf.add_loop(ea_loop)

        # refresh _nef_sequence or _Chem_comp_assembly loop

        lp_category = LP_CATEGORIES[file_type][content_subtype]

        loop = pynmrstar.Loop.from_scratch(lp_category)

        has_index_tag = INDEX_TAGS[file_type][content_subtype] is not None

        if has_index_tag:
            loop.add_tag(lp_category + '.' + INDEX_TAGS[file_type][content_subtype])

        for key_item in key_items:
            loop.add_tag(lp_category + '.' + key_item['name'])

        for data_item in data_items:
            data_name = data_item['name']
            if data_name != 'NEF_index' or (data_name == 'NEF_index' and has_nef_index):
                loop.add_tag(lp_category + '.' + data_name)

        if has_entry_id:
            loop.add_tag(lp_category + '.Entry_ID')

        cif_poly_seq = self.__reg.caC['polymer_sequence']
        entity_assembly = self.__reg.caC['entity_assembly']
        auth_to_star_seq = self.__reg.caC['auth_to_star_seq']
        auth_to_orig_seq = self.__reg.caC['auth_to_orig_seq']
        asym_to_orig_seq = {}
        if self.__reg.caC is not None:
            if 'asym_to_orig_seq' in self.__reg.caC:
                asym_to_orig_seq = self.__reg.caC['asym_to_orig_seq']
            else:
                for _k, _v in auth_to_orig_seq.items():
                    auth_asym_id = _k[0]
                    if auth_asym_id not in asym_to_orig_seq:
                        asym_to_orig_seq[auth_asym_id] = {}
                    asym_to_orig_seq[auth_asym_id][(_k[1], _k[2])] = _v
                self.__reg.caC['asym_to_orig_seq'] = asym_to_orig_seq
                if self.__reg.asmChkCachePath is not None:
                    write_as_pickle(self.__reg.caC, self.__reg.asmChkCachePath)

        # DAOTHER-9644: sort by Entity_assembly_ID and Comp_index_ID due to inserted sequence for truncated loop
        _auth_to_star_seq = dict(sorted(auth_to_star_seq.items(), key=lambda item: item[1]))

        entity_type_of = {item['entity_id']: item['entity_type'] for item in entity_assembly}

        seq_keys = set()

        nef_index = 1
        _entity_assembly_id = index = 0

        if file_type == 'nef':

            idx_col = loop.tags.index('index')
            chain_id_col = loop.tags.index('chain_code')
            seq_id_col = loop.tags.index('sequence_code')
            comp_id_col = loop.tags.index('residue_name')
            seq_link_col = loop.tags.index('linking')
            auth_var_id_col = loop.tags.index('residue_variant')
            cis_res_col = loop.tags.index('cis_peptide')

            for k, v in _auth_to_star_seq.items():
                auth_asym_id, auth_seq_id, comp_id = k
                entity_assembly_id, seq_id, entity_id, genuine = v

                if auth_seq_id is None or not genuine:
                    continue

                seq_key = (entity_assembly_id, seq_id)

                if seq_key in seq_keys:
                    continue

                if entity_assembly_id != _entity_assembly_id:
                    _entity_assembly_id = entity_assembly_id
                    index = 1

                seq_keys.add(seq_key)

                if self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                   and any(True for d in self.__reg.nmr_ext_poly_seq
                           if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] < auth_seq_id):
                    for d in self.__reg.nmr_ext_poly_seq:
                        if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] < auth_seq_id and 'touch' not in d:
                            _auth_seq_id, _auth_comp_id = d['auth_seq_id'], d['auth_comp_id']
                            _seq_key = (entity_assembly_id, _auth_seq_id)
                            if _seq_key in seq_keys or _auth_comp_id in EMPTY_VALUE or not _auth_comp_id[0].isalnum():  # 2l1f, DAOTHER-9694
                                continue
                            seq_keys.add(_seq_key)
                            row = [None] * len(loop.tags)
                            row[chain_id_col], row[seq_id_col], row[comp_id_col], row[idx_col] =\
                                auth_asym_id, _auth_seq_id, _auth_comp_id, nef_index
                            row[seq_link_col] = 'start' if index == 1 else 'middle' if _auth_comp_id not in UNKNOWN_RESIDUE else 'dummy'

                            loop.add_data(row)

                            d['touch'] = True

                            nef_index += 1
                            index += 1

                if auth_asym_id in asym_to_orig_seq:
                    auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                         if _k == (auth_seq_id, comp_id)), comp_id)
                else:
                    auth_comp_id = comp_id

                row = [None] * len(loop.tags)

                row[chain_id_col], row[seq_id_col] = auth_asym_id, auth_seq_id

                entity_type = entity_type_of[entity_id]

                row[comp_id_col] = auth_comp_id

                if entity_type == 'polymer':
                    ps = next(ps for ps in cif_poly_seq if ps['auth_chain_id'] == auth_asym_id)
                    nmr_ps = self.__reg.report.getNmrPolymerSequenceWithModelChainId(auth_asym_id,
                                                                                     label_scheme=False)
                    if nmr_ps is None and 'identical_auth_chain_id' in ps:
                        nmr_ps = self.__reg.report.getNmrPolymerSequenceWithModelChainId(ps['identical_auth_chain_id'][0],
                                                                                         label_scheme=False)

                    if nmr_ps is not None:
                        try:
                            j = ps['auth_seq_id'].index(auth_seq_id)
                            label_seq_id = ps['seq_id'][j]
                            length = len(ps['seq_id'])
                            cyclic = self.__reg.dpV.isCyclicPolymer(nmr_ps['chain_id'])
                            if cyclic and label_seq_id in (1, length):
                                row[seq_link_col] = 'cyclic'
                            elif label_seq_id == 1 and length == 1:
                                row[seq_link_col] = 'single'
                            elif index == 1:
                                row[seq_link_col] = 'start'
                            elif j == length - 1:
                                row[seq_link_col] = 'end'
                            elif label_seq_id - 1 == ps['seq_id'][j - 1] and label_seq_id + 1 == ps['seq_id'][j + 1]:
                                row[seq_link_col] = 'middle'
                            elif label_seq_id == 1:
                                row[seq_link_col] = 'middle'
                            else:
                                row[seq_link_col] = 'break'

                            entity_poly_type = next((item['entity_poly_type'] for item in entity_assembly
                                                     if item['entity_id'] == entity_id and item['entity_type'] == 'polymer'), None)
                            if entity_poly_type is not None and entity_poly_type.startswith('polypeptide'):
                                if self.__reg.dpV.isProtCis(nmr_ps['chain_id'], seq_id):
                                    row[cis_res_col] = 'true'
                                elif auth_comp_id in ('PRO', 'GLY'):
                                    row[cis_res_col] = 'false'
                                else:
                                    row[cis_res_col] = '.'
                        except ValueError:
                            pass

                row[idx_col] = nef_index

                if auth_var_id_col != -1 and has_res_var_dat:
                    orig_row = next((_row for _row in orig_lp_data
                                     if _row['chain_code'] == auth_asym_id
                                     and _row['sequence_code'] == auth_seq_id
                                     and _row['residue_name'] == auth_comp_id), None)
                    if orig_row is not None:
                        row[auth_var_id_col] = orig_row['residue_variant']

                if auth_comp_id not in EMPTY_VALUE:
                    loop.add_data(row)

                nef_index += 1
                index += 1

                if row[seq_link_col] == 'end' and self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                   and any(True for d in self.__reg.nmr_ext_poly_seq
                           if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] > auth_seq_id):
                    for d in self.__reg.nmr_ext_poly_seq:
                        if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] > auth_seq_id and 'touch' not in d:
                            if loop.data[-1][seq_link_col] == 'end':
                                loop.data[-1][seq_link_col] = 'middle'
                            _auth_seq_id, _auth_comp_id = d['auth_seq_id'], d['auth_comp_id']
                            _seq_key = (entity_assembly_id, _auth_seq_id)
                            # 2l1f, DAOTHER-9694:
                            if _seq_key in seq_keys or _auth_comp_id in EMPTY_VALUE or not _auth_comp_id[0].isalnum():
                                continue
                            seq_keys.add(_seq_key)
                            row = [None] * len(loop.tags)
                            row[chain_id_col], row[seq_id_col], row[comp_id_col], row[idx_col] =\
                                auth_asym_id, _auth_seq_id, _auth_comp_id, nef_index
                            row[seq_link_col] = 'end' if _auth_comp_id not in UNKNOWN_RESIDUE else 'dummy'

                            loop.add_data(row)

                            d['touch'] = True

                            nef_index += 1

            if len(self.__reg.auth_asym_ids_with_chem_exch) > 0:
                for item in entity_assembly:
                    entity_type = item['entity_type']
                    if entity_type in ('non-polymer', 'water'):
                        continue
                    auth_asym_id = item['auth_asym_id']
                    if auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch.keys():
                        for _auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch[auth_asym_id]:
                            for row in loop:
                                if row[chain_id_col] == auth_asym_id:
                                    _row = copy.copy(row)
                                    _row[chain_id_col] = _auth_asym_id
                                    _row[idx_col] = nef_index

                                    loop.add_data(_row)

                                    nef_index += 1

            asm_sf.add_loop(loop)

            if self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0:
                for d in self.__reg.nmr_ext_poly_seq:
                    if 'touch' in d:
                        del d['touch']

            # refresh _nef_covalent_links loop

            if self.__reg.cR.hasCategory('struct_conn'):

                lp_category = '_nef_covalent_links'

                b_loop = pynmrstar.Loop.from_scratch(lp_category)

                b_key_items = [{'name': 'chain_code_1', 'type': 'str'},
                               {'name': 'sequence_code_1', 'type': 'int'},
                               {'name': 'residue_name_1', 'type': 'str'},
                               {'name': 'atom_name_1', 'type': 'str'},
                               {'name': 'chain_code_2', 'type': 'str'},
                               {'name': 'sequence_code_2', 'type': 'int'},
                               {'name': 'residue_name_2', 'type': 'str'},
                               {'name': 'atom_name_2', 'type': 'str'}
                               ]

                tags = [lp_category + '.' + _item['name'] for _item in b_key_items]

                b_loop.add_tag(tags)

                bonds = self.__reg.cR.getDictList('struct_conn')

                for bond in bonds:
                    bond_type = bond['conn_type_id']
                    auth_asym_id_1 = bond['ptnr1_auth_asym_id']
                    auth_seq_id_1 = bond['ptnr1_auth_seq_id']
                    auth_comp_id_1 = bond['ptnr1_auth_comp_id']
                    atom_id_1 = bond['ptnr1_label_atom_id']
                    auth_asym_id_2 = bond['ptnr2_auth_asym_id']
                    auth_seq_id_2 = bond['ptnr2_auth_seq_id']
                    auth_comp_id_2 = bond['ptnr2_auth_comp_id']
                    atom_id_2 = bond['ptnr2_label_atom_id']

                    if bond_type == 'covale':
                        pass
                    elif bond_type.startswith('covale_'):  # 'covale_base', 'covale_phosphate', 'covale_sugar'
                        pass
                    elif bond_type == 'disulf':
                        pass
                    elif bond_type == 'hydrog':
                        continue
                    elif bond_type == 'metalc':
                        pass
                    elif bond_type == 'mismat':
                        continue
                    elif bond_type == 'modres':
                        continue
                    elif bond_type == 'saltbr':
                        continue

                    row = [None] * len(tags)

                    try:

                        seq_key_1 = (auth_asym_id_1, int(auth_seq_id_1), auth_comp_id_1)

                        if seq_key_1 in auth_to_star_seq:
                            row[0], row[1], row[2], row[3] = auth_asym_id_1, auth_seq_id_1, auth_comp_id_1, atom_id_1

                    except ValueError:
                        pass

                    try:

                        seq_key_2 = (auth_asym_id_2, int(auth_seq_id_2), auth_comp_id_2)

                        if seq_key_2 in auth_to_star_seq:
                            row[4], row[5], row[6], row[7] = auth_asym_id_2, auth_seq_id_2, auth_comp_id_2, atom_id_2

                    except ValueError:
                        pass

                    if None not in (row[0], row[4]):
                        b_loop.add_data(row)

                if len(b_loop) > 0:
                    asm_sf.add_loop(b_loop)

        else:

            chain_id_col = loop.tags.index('Entity_assembly_ID')
            ent_id_col = loop.tags.index('Entity_ID')
            seq_id_col = loop.tags.index('Comp_index_ID')
            alt_seq_id_col = loop.tags.index('Seq_ID')
            comp_id_col = loop.tags.index('Comp_ID')
            auth_asym_id_col = loop.tags.index('Auth_asym_ID')
            auth_seq_id_col = loop.tags.index('Auth_seq_ID')
            auth_comp_id_col = loop.tags.index('Auth_comp_ID')
            seq_link_col = loop.tags.index('Sequence_linking')
            cis_res_col = loop.tags.index('Cis_residue')
            asm_id_col = loop.tags.index('Assembly_ID')
            idx_col = loop.tags.index('NEF_index') if 'NEF_index' in loop.tags else -1
            auth_var_id_col = loop.tags.index('Auth_variant_ID') if 'Auth_variant_ID' in loop.tags else -1
            entry_id_col = loop.tags.index('Entry_ID') if 'Entry_ID' in loop.tags else -1

            for k, v in _auth_to_star_seq.items():
                auth_asym_id, auth_seq_id, comp_id = k
                entity_assembly_id, seq_id, entity_id, genuine = v

                if auth_seq_id is None or not genuine:
                    continue

                seq_key = (entity_assembly_id, seq_id)

                if seq_key in seq_keys:
                    continue

                if entity_assembly_id != _entity_assembly_id:
                    _entity_assembly_id = entity_assembly_id
                    index = 1

                seq_keys.add(seq_key)

                if self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                   and any(True for d in self.__reg.nmr_ext_poly_seq
                           if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] < auth_seq_id):
                    for d in self.__reg.nmr_ext_poly_seq:
                        if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] < auth_seq_id and 'touch' not in d:
                            _offset = seq_id - auth_seq_id
                            _auth_seq_id, _auth_comp_id = d['auth_seq_id'], d['auth_comp_id']
                            _seq_id = _auth_seq_id + _offset
                            _seq_key = (entity_assembly_id, _seq_id)
                            # 2l1f, DAOTHER-9694
                            if _seq_key in seq_keys or _auth_comp_id in EMPTY_VALUE or not _auth_comp_id[0].isalnum():
                                continue
                            seq_keys.add(_seq_key)
                            row = [None] * len(loop.tags)
                            row[chain_id_col], row[ent_id_col], row[seq_id_col], row[alt_seq_id_col] =\
                                entity_assembly_id, entity_id, _seq_id, _seq_id
                            row[comp_id_col], row[auth_asym_id_col], row[auth_seq_id_col], row[auth_comp_id_col] =\
                                _auth_comp_id, auth_asym_id, _auth_seq_id, _auth_comp_id
                            row[seq_link_col] = 'start' if index == 1 else 'middle' if _auth_comp_id not in UNKNOWN_RESIDUE else 'dummy'
                            row[asm_id_col] = 1
                            if idx_col != -1:
                                row[idx_col] = nef_index
                            if entry_id_col != -1:
                                row[entry_id_col] = self.__reg.entry_id

                            loop.add_data(row)

                            d['touch'] = True

                            nef_index += 1
                            index += 1

                if auth_asym_id in asym_to_orig_seq:
                    auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                         if _k == (auth_seq_id, comp_id)), comp_id)
                else:
                    auth_comp_id = comp_id

                row = [None] * len(loop.tags)

                row[chain_id_col], row[ent_id_col] = entity_assembly_id, entity_id
                row[seq_id_col] = row[alt_seq_id_col] = seq_id
                seq_keys.add((entity_assembly_id, seq_id))

                entity_type = entity_type_of[entity_id]

                row[comp_id_col], row[auth_asym_id_col], row[auth_seq_id_col], row[auth_comp_id_col] =\
                    auth_comp_id, auth_asym_id, auth_seq_id, auth_comp_id

                if entity_type == 'polymer':
                    ps = next(ps for ps in cif_poly_seq if ps['auth_chain_id'] == auth_asym_id)
                    nmr_ps = self.__reg.report.getNmrPolymerSequenceWithModelChainId(auth_asym_id,
                                                                                     label_scheme=False)
                    if nmr_ps is None and 'identical_auth_chain_id' in ps:
                        nmr_ps = self.__reg.report.getNmrPolymerSequenceWithModelChainId(ps['identical_auth_chain_id'][0],
                                                                                         label_scheme=False)

                    if nmr_ps is not None:
                        try:
                            j = ps['auth_seq_id'].index(auth_seq_id)
                            label_seq_id = ps['seq_id'][j]
                            if label_seq_id is not None:
                                try:
                                    length = len(ps['seq_id'])
                                    cyclic = self.__reg.dpV.isCyclicPolymer(nmr_ps['chain_id'])
                                    if cyclic and label_seq_id in (1, length):
                                        row[seq_link_col] = 'cyclic'
                                    elif label_seq_id == 1 and length == 1:
                                        row[seq_link_col] = 'single'
                                    elif index == 1:
                                        row[seq_link_col] = 'start'
                                    elif j == length - 1:
                                        row[seq_link_col] = 'end'
                                    elif label_seq_id - 1 == ps['seq_id'][j - 1] and label_seq_id + 1 == ps['seq_id'][j + 1]:
                                        row[seq_link_col] = 'middle'
                                    elif label_seq_id == 1:
                                        row[seq_link_col] = 'middle'
                                    else:
                                        row[seq_link_col] = 'break'
                                except IndexError:
                                    pass

                            entity_poly_type = next((item['entity_poly_type'] for item in entity_assembly
                                                     if item['entity_id'] == entity_id and item['entity_type'] == 'polymer'), None)
                            if entity_poly_type is not None and entity_poly_type.startswith('polypeptide'):
                                if self.__reg.dpV.isProtCis(nmr_ps['chain_id'], seq_id):
                                    row[cis_res_col] = 'yes'
                                elif auth_comp_id in ('PRO', 'GLY'):
                                    row[cis_res_col] = 'no'
                                else:
                                    row[cis_res_col] = '.'
                        except ValueError:
                            pass

                row[asm_id_col] = 1

                if idx_col != -1:
                    row[idx_col] = nef_index

                if auth_var_id_col != -1 and has_res_var_dat:
                    orig_row = next((_row for _row in orig_lp_data
                                     if _row['Entity_assembly_ID'] == str(entity_assembly_id)
                                     and _row['Comp_index_ID'] == seq_id
                                     and _row['Comp_ID'] == auth_comp_id), None)
                    if orig_row is not None:
                        row[auth_var_id_col] = orig_row['Auth_variant_ID']

                if entry_id_col != -1:
                    row[entry_id_col] = self.__reg.entry_id

                if comp_id not in EMPTY_VALUE:
                    loop.add_data(row)

                nef_index += 1
                index += 1

                if row[seq_link_col] == 'end' and self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                   and any(True for d in self.__reg.nmr_ext_poly_seq
                           if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] > auth_seq_id):
                    for d in self.__reg.nmr_ext_poly_seq:
                        if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] > auth_seq_id and 'touch' not in d:
                            if loop.data[-1][seq_link_col] == 'end':
                                loop.data[-1][seq_link_col] = 'middle'
                            _offset = seq_id - auth_seq_id
                            _auth_seq_id, _auth_comp_id = d['auth_seq_id'], d['auth_comp_id']
                            _seq_id = _auth_seq_id + _offset
                            _seq_key = (entity_assembly_id, _seq_id)
                            # 2l1f, DAOTHER-9694:
                            if _seq_key in seq_keys or _auth_comp_id in EMPTY_VALUE or not _auth_comp_id[0].isalnum():
                                continue
                            seq_keys.add(_seq_key)
                            row = [None] * len(loop.tags)
                            row[chain_id_col], row[ent_id_col], row[seq_id_col], row[alt_seq_id_col] =\
                                entity_assembly_id, entity_id, _seq_id, _seq_id
                            row[comp_id_col], row[auth_asym_id_col], row[auth_seq_id_col], row[auth_comp_id_col] =\
                                _auth_comp_id, auth_asym_id, _auth_seq_id, _auth_comp_id
                            row[seq_link_col] = 'end' if _auth_comp_id not in UNKNOWN_RESIDUE else 'dummy'
                            row[asm_id_col] = 1
                            if idx_col != -1:
                                row[idx_col] = nef_index
                            if entry_id_col != -1:
                                row[entry_id_col] = self.__reg.entry_id

                            loop.add_data(row)

                            d['touch'] = True

                            nef_index += 1

            if len(self.__reg.auth_asym_ids_with_chem_exch) > 0:
                _entity_assembly_id = loop.data[-1][chain_id_col]
                for item in entity_assembly:
                    entity_type = item['entity_type']
                    if entity_type in ('non-polymer', 'water'):
                        continue
                    entity_id = item['entity_id']
                    auth_asym_id = item['auth_asym_id']
                    if auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch.keys():
                        for _auth_asym_id in self.__reg.auth_asym_ids_with_chem_exch[auth_asym_id]:
                            _entity_assembly_id += 1
                            for row in loop:
                                if row[ent_id_col] == entity_id and row[auth_asym_id_col] == auth_asym_id:
                                    _row = copy.copy(row)
                                    _row[chain_id_col] = _entity_assembly_id
                                    _row[auth_asym_id_col] = _auth_asym_id

                                    if idx_col != -1:
                                        _row[idx_col] = nef_index

                                    loop.add_data(_row)

                                    nef_index += 1

            asm_sf.add_loop(loop)

            if self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0:
                for d in self.__reg.nmr_ext_poly_seq:
                    if 'touch' in d:
                        del d['touch']

            self.__reg.chem_comp_asm_dat =\
                loop.get_tag(['Entity_assembly_ID', 'Entity_ID', 'Comp_index_ID', 'Seq_ID', 'Comp_ID', 'Auth_asym_ID', 'Auth_seq_ID'])

            # refresh _Bond loop

            if self.__reg.cR.hasCategory('struct_conn'):

                lp_category = '_Bond'

                b_loop = pynmrstar.Loop.from_scratch(lp_category)

                b_key_items = [{'name': 'ID', 'type': 'positive-int'},
                               {'name': 'Type', 'type': 'enum',
                                'enum': ('amide', 'covalent', 'directed', 'disulfide', 'ester', 'ether',
                                         'hydrogen', 'metal coordination', 'peptide', 'thioether', 'oxime',
                                         'thioester', 'phosphoester', 'phosphodiester', 'diselenide', 'na')},
                               {'name': 'Value_order', 'type': 'enum',
                                'enum': ('sing', 'doub', 'trip', 'quad', 'arom', 'poly', 'delo', 'pi', 'directed')},
                               {'name': 'Entity_assembly_ID_1', 'type': 'positive-int-as-str'},
                               {'name': 'Entity_assembly_name_1', 'type': 'str'},
                               {'name': 'Entity_ID_1', 'type': 'positive-int'},
                               {'name': 'Comp_ID_1', 'type': 'str'},
                               {'name': 'Comp_index_ID_1', 'type': 'int'},
                               {'name': 'Seq_ID_1', 'type': 'int'},
                               {'name': 'Atom_ID_1', 'type': 'str'},
                               {'name': 'Entity_assembly_ID_2', 'type': 'positive-int-as-str'},
                               {'name': 'Entity_assembly_name_2', 'type': 'str'},
                               {'name': 'Entity_ID_2', 'type': 'positive-int'},
                               {'name': 'Comp_ID_2', 'type': 'str'},
                               {'name': 'Comp_index_ID_2', 'type': 'int'},
                               {'name': 'Seq_ID_2', 'type': 'int'},
                               {'name': 'Atom_ID_2', 'type': 'str'},
                               ]
                b_data_items = [{'name': 'Auth_asym_ID_1', 'type': 'str', 'mandaory': False},
                                {'name': 'Auth_seq_ID_1', 'type': 'int', 'mandatory': False},
                                {'name': 'Auth_comp_ID_1', 'type': 'str', 'mandatory': False},
                                {'name': 'Auth_atom_ID_1', 'type': 'str', 'mandatory': False},
                                {'name': 'Auth_asym_ID_2', 'type': 'str', 'mandaory': False},
                                {'name': 'Auth_seq_ID_2', 'type': 'int', 'mandatory': False},
                                {'name': 'Auth_comp_ID_2', 'type': 'str', 'mandatory': False},
                                {'name': 'Auth_atom_ID_2', 'type': 'str', 'mandatory': False},
                                {'name': 'Assembly_ID', 'type': 'pointer-index', 'mandatory': False,
                                 'default': '1', 'default-from': 'parent'},
                                {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                                ]

                tags = [lp_category + '.' + _item['name'] for _item in b_key_items]
                tags.extend([lp_category + '.' + _item['name'] for _item in b_data_items])

                b_loop.add_tag(tags)

                bonds = self.__reg.cR.getDictList('struct_conn')

                index = 1

                non_std_bond = False

                for bond in bonds:

                    try:

                        bond_type = bond['conn_type_id']
                        auth_asym_id_1 = bond['ptnr1_auth_asym_id']
                        auth_seq_id_1 = int(bond['ptnr1_auth_seq_id'])
                        auth_comp_id_1 = bond['ptnr1_auth_comp_id']
                        atom_id_1 = bond['ptnr1_label_atom_id']
                        auth_asym_id_2 = bond['ptnr2_auth_asym_id']
                        auth_seq_id_2 = int(bond['ptnr2_auth_seq_id'])
                        auth_comp_id_2 = bond['ptnr2_auth_comp_id']
                        atom_id_2 = bond['ptnr2_label_atom_id']

                    except ValueError:
                        continue

                    row = [None] * len(tags)

                    row[0] = index

                    if bond_type == 'covale':
                        row[1], row[2] = 'covalent', 'sing'
                        non_std_bond = True
                    elif bond_type.startswith('covale_'):  # 'covale_base', 'covale_phosphate', 'covale_sugar'
                        row[1] = 'covalent'
                        non_std_bond = True
                    elif bond_type == 'disulf':
                        row[1], row[2] = 'disulfide', 'sing'
                    elif bond_type == 'hydrog':
                        row[1], row[2] = 'hydrogen', 'sing'
                        continue
                    elif bond_type == 'metalc':
                        row[1], row[2] = 'metal coordination', 'sing'
                        non_std_bond = True
                    elif bond_type == 'mismat':
                        row[1] = 'na'
                        non_std_bond = True
                        continue
                    elif bond_type == 'modres':
                        row[1] = 'na'
                        non_std_bond = True
                        continue
                    elif bond_type == 'saltbr':
                        row[1] = 'na'
                        continue

                    seq_key_1 = (auth_asym_id_1, auth_seq_id_1, auth_comp_id_1)

                    entity_id_1 = entity_id_2 = None

                    if seq_key_1 in auth_to_star_seq:
                        entity_assembly_id_1, seq_id_1, entity_id_1, _ = auth_to_star_seq[seq_key_1]
                        entity_assembly_name_1 = next((item['entity_assembly_name'] for item in entity_assembly
                                                       if item['entity_id'] == entity_id_1), None)
                        row[3], row[4], row[5], row[6], row[7], row[8], row[9] =\
                            entity_assembly_id_1, entity_assembly_name_1, entity_id_1, auth_comp_id_1, seq_id_1, seq_id_1, atom_id_1

                        row[17], row[18], row[19], row[20] =\
                            auth_asym_id_1, auth_seq_id_1, auth_comp_id_1, atom_id_1

                    seq_key_2 = (auth_asym_id_2, auth_seq_id_2, auth_comp_id_2)

                    if seq_key_2 in auth_to_star_seq:
                        entity_assembly_id_2, seq_id_2, entity_id_2, _ = auth_to_star_seq[seq_key_2]
                        entity_assembly_name_2 = next((item['entity_assembly_name'] for item in entity_assembly
                                                       if item['entity_id'] == entity_id_2), None)
                        row[10], row[11], row[12], row[13], row[14], row[15], row[16] =\
                            entity_assembly_id_2, entity_assembly_name_2, entity_id_2, auth_comp_id_2, seq_id_2, seq_id_2, atom_id_2

                        row[21], row[22], row[23], row[24] =\
                            auth_asym_id_2, auth_seq_id_2, auth_comp_id_2, atom_id_2

                    if entity_id_1 is not None and entity_id_2 is not None and entity_id_1 == entity_id_2:
                        entity_poly_type = next((item['entity_poly_type'] for item in entity_assembly
                                                 if item['entity_id'] == entity_id_1 and item['entity_type'] == 'polymer'), None)
                        if entity_poly_type is not None and entity_poly_type.startswith('polypeptide')\
                           and {atom_id_1, atom_id_2} == {'C', 'N'} and abs(auth_seq_id_1 - auth_seq_id_2) > 1:
                            row[1], row[2] = 'peptide', "sing"

                    row[25], row[26] = 1, self.__reg.entry_id

                    b_loop.add_data(row)

                    index += 1

                if index > 1:
                    asm_sf.add_loop(b_loop)

                if non_std_bond:
                    set_sf_tag(asm_sf, 'Non_standard_bonds', 'yes')

                bonds_w_leaving = [bond for bond in bonds
                                   if ('pdbx_leaving_atom_flag' in bond and bond['pdbx_leaving_atom_flag'] in ('both', 'one'))
                                   or (bond['ptnr1_label_comp_id'] in ('CYS', 'DCS') and bond['ptnr1_label_atom_id'] == 'SG')
                                   or (bond['ptnr2_label_comp_id'] in ('CYS', 'DCS') and bond['ptnr2_label_atom_id'] == 'SG')
                                   or (bond['ptnr1_label_comp_id'] == 'HIS' and bond['ptnr1_label_atom_id'] in ('ND1', 'NE2'))
                                   or (bond['ptnr2_label_comp_id'] == 'HIS' and bond['ptnr2_label_atom_id'] in ('ND1', 'NE2'))]

                if len(bonds_w_leaving) > 0:

                    # _Entity_deleted_atom loop

                    lp_category = '_Entity_deleted_atom'

                    eda_loop = pynmrstar.Loop.from_scratch(lp_category)

                    eda_key_items = [{'name': 'ID', 'type': 'positive-int'},
                                     {'name': 'Entity_assembly_ID', 'type': 'positive-int-as-str'},
                                     {'name': 'Comp_index_ID', 'type': 'int'},
                                     {'name': 'Seq_ID', 'type': 'int'},
                                     {'name': 'Comp_ID', 'type': 'str'},
                                     {'name': 'Atom_ID', 'type': 'str'}
                                     ]
                    eda_data_items = [{'name': 'Auth_entity_assembly_ID', 'type': 'positive-int-as-str'},
                                      {'name': 'Auth_seq_ID', 'type': 'int'},
                                      {'name': 'Auth_comp_ID', 'type': 'str'},
                                      {'name': 'Auth_atom_ID', 'type': 'str'},
                                      {'name': 'Assembly_ID', 'type': 'pointer-index', 'mandatory': False,
                                       'default': '1', 'default-from': 'parent'},
                                      {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                                      ]

                    tags = [lp_category + '.' + _item['name'] for _item in eda_key_items]
                    tags.extend([lp_category + '.' + _item['name'] for _item in eda_data_items])

                    eda_loop.add_tag(tags)

                    index = 1

                    for bond in bonds_w_leaving:

                        leaving_flag = bond.get('pdbx_leaving_atom_flag', '')

                        if leaving_flag in ('one', 'both'):
                            leaving_atom_id = None

                            comp_id = bond['ptnr1_label_comp_id']
                            atom_id = bond['ptnr1_label_atom_id']
                            auth_asym_id = bond['ptnr1_auth_asym_id']
                            auth_seq_id = bond['ptnr1_auth_seq_id']

                            if not auth_seq_id.isdigit():
                                continue

                            if self.__reg.ccU.updateChemCompDict(comp_id):
                                for b in self.__reg.ccU.lastBondDictList:
                                    if atom_id in (b['atom_id_1'], b['atom_id_2']):
                                        _atom_id = b['atom_id_1'] if b['atom_id_1'] != atom_id\
                                            else b['atom_id_2']
                                        if any(True for a in self.__reg.ccU.lastAtomDictList
                                               if _atom_id == a['atom_id'] and a['leaving_atom_flag'] == 'Y'):
                                            leaving_atom_id = _atom_id
                                            break

                                if leaving_atom_id is not None:

                                    seq_key = (auth_asym_id, int(auth_seq_id), comp_id)

                                    if seq_key in auth_to_star_seq:
                                        if auth_asym_id in asym_to_orig_seq:
                                            auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                                                 if _k == (seq_key[1], comp_id)), comp_id)
                                        else:
                                            auth_comp_id = comp_id

                                        row = [None] * len(tags)

                                        row[0] = index

                                        entity_assembly_id, seq_id, _, _ = auth_to_star_seq[seq_key]

                                        row[1], row[4], row[5] =\
                                            entity_assembly_id, auth_comp_id, leaving_atom_id
                                        row[2] = row[3] = seq_id

                                        row[6], row[7], row[8], row[9] =\
                                            auth_asym_id, auth_seq_id, auth_comp_id, leaving_atom_id

                                        row[10], row[11] = 1, self.__reg.entry_id

                                        eda_loop.add_data(row)

                                        index += 1

                            if leaving_flag == 'both' or leaving_atom_id is None:
                                leaving_atom_id = None

                                comp_id = bond['ptnr2_label_comp_id']
                                atom_id = bond['ptnr2_label_atom_id']
                                auth_asym_id = bond['ptnr2_auth_asym_id']
                                auth_seq_id = bond['ptnr2_auth_seq_id']

                                if not auth_seq_id.isdigit():
                                    continue

                                if self.__reg.ccU.updateChemCompDict(comp_id):
                                    for b in self.__reg.ccU.lastBondDictList:
                                        if atom_id in (b['atom_id_1'], b['atom_id_2']):
                                            _atom_id = b['atom_id_1'] if b['atom_id_1'] != atom_id\
                                                else b['atom_id_2']
                                            if any(True for a in self.__reg.ccU.lastAtomDictList
                                                   if _atom_id == a['atom_id']
                                                   and a['leaving_atom_flag'] == 'Y'):
                                                leaving_atom_id = _atom_id
                                                break

                                    if leaving_atom_id is not None:

                                        seq_key = (auth_asym_id, int(auth_seq_id), comp_id)

                                        if seq_key in auth_to_star_seq:
                                            if auth_asym_id in asym_to_orig_seq:
                                                auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                                                     if _k == (seq_key[1], comp_id)), comp_id)
                                            else:
                                                auth_comp_id = comp_id

                                            row = [None] * len(tags)

                                            row[0] = index

                                            entity_assembly_id, seq_id, _, _ = auth_to_star_seq[seq_key]

                                            row[1], row[4], row[5] =\
                                                entity_assembly_id, auth_comp_id, leaving_atom_id
                                            row[2] = row[3] = seq_id

                                            row[6], row[7], row[8], row[9] =\
                                                auth_asym_id, auth_seq_id, auth_comp_id, leaving_atom_id

                                            row[10], row[11] = 1, self.__reg.entry_id

                                            eda_loop.add_data(row)

                                            index += 1

                        else:

                            if bond['ptnr1_label_comp_id'] in ('CYS', 'DCS') and bond['ptnr1_label_atom_id'] == 'SG':
                                comp_id = bond['ptnr1_label_comp_id']
                                atom_id = 'SG'
                                auth_asym_id = bond['ptnr1_auth_asym_id']
                                auth_seq_id = bond['ptnr1_auth_seq_id']

                                if not auth_seq_id.isdigit():
                                    continue

                                leaving_atom_id = 'HG'

                                seq_key = (auth_asym_id, int(auth_seq_id), comp_id)

                                if seq_key in auth_to_star_seq:
                                    auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                                         if _k == (seq_key[1], comp_id)), comp_id)

                                    row = [None] * len(tags)

                                    row[0] = index

                                    entity_assembly_id, seq_id, _, _ = auth_to_star_seq[seq_key]

                                    row[1], row[4], row[5] =\
                                        entity_assembly_id, auth_comp_id, leaving_atom_id
                                    row[2] = row[3] = seq_id

                                    row[6], row[7], row[8], row[9] =\
                                        auth_asym_id, auth_seq_id, auth_comp_id, leaving_atom_id

                                    row[10], row[11] = 1, self.__reg.entry_id

                                    eda_loop.add_data(row)

                                    index += 1

                            elif bond['ptnr1_label_comp_id'] == 'HIS' and bond['ptnr1_label_atom_id'] in ('ND1', 'NE2'):
                                comp_id = 'HIS'
                                atom_id = bond['ptnr1_label_atom_id']
                                auth_asym_id = bond['ptnr1_auth_asym_id']
                                auth_seq_id = bond['ptnr1_auth_seq_id']

                                if not auth_seq_id.isdigit():
                                    continue

                                leaving_atom_id = 'HD1' if atom_id == 'ND1' else 'HE2'

                                seq_key = (auth_asym_id, int(auth_seq_id), comp_id)

                                if seq_key in auth_to_star_seq:
                                    if auth_asym_id in asym_to_orig_seq:
                                        auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                                             if _k == (seq_key[1], comp_id)), comp_id)
                                    else:
                                        auth_comp_id = comp_id

                                    row = [None] * len(tags)

                                    row[0] = index

                                    entity_assembly_id, seq_id, _, _ = auth_to_star_seq[seq_key]

                                    row[1], row[4], row[5] =\
                                        entity_assembly_id, auth_comp_id, leaving_atom_id
                                    row[2] = row[3] = seq_id

                                    row[6], row[7], row[8], row[9] =\
                                        auth_asym_id, auth_seq_id, auth_comp_id, leaving_atom_id

                                    row[10], row[11] = 1, self.__reg.entry_id

                                    eda_loop.add_data(row)

                                    index += 1

                            if bond['ptnr2_label_comp_id'] in ('CYS', 'DCS') and bond['ptnr2_label_atom_id'] == 'SG':
                                comp_id = bond['ptnr2_label_comp_id']
                                atom_id = 'SG'
                                auth_asym_id = bond['ptnr2_auth_asym_id']
                                auth_seq_id = bond['ptnr2_auth_seq_id']

                                if not auth_seq_id.isdigit():
                                    continue

                                leaving_atom_id = 'HG'

                                seq_key = (auth_asym_id, int(auth_seq_id), comp_id)

                                if seq_key in auth_to_star_seq:
                                    if auth_asym_id in asym_to_orig_seq:
                                        auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                                             if _k == (seq_key[1], comp_id)), comp_id)
                                    else:
                                        auth_comp_id = comp_id

                                    row = [None] * len(tags)

                                    row[0] = index

                                    entity_assembly_id, seq_id, _, _ = auth_to_star_seq[seq_key]

                                    row[1], row[4], row[5] =\
                                        entity_assembly_id, auth_comp_id, leaving_atom_id
                                    row[2] = row[3] = seq_id

                                    row[6], row[7], row[8], row[9] =\
                                        auth_asym_id, auth_seq_id, auth_comp_id, leaving_atom_id

                                    row[10], row[11] = 1, self.__reg.entry_id

                                    eda_loop.add_data(row)

                                    index += 1

                            elif bond['ptnr2_label_comp_id'] == 'HIS' and bond['ptnr2_label_atom_id'] in ('ND1', 'NE2'):
                                comp_id = 'HIS'
                                atom_id = bond['ptnr2_label_atom_id']
                                auth_asym_id = bond['ptnr2_auth_asym_id']
                                auth_seq_id = bond['ptnr2_auth_seq_id']

                                if not auth_seq_id.isdigit():
                                    continue

                                leaving_atom_id = 'HD1' if atom_id == 'ND1' else 'HE2'

                                seq_key = (auth_asym_id, int(auth_seq_id), comp_id)

                                if seq_key in auth_to_star_seq:
                                    if auth_asym_id in asym_to_orig_seq:
                                        auth_comp_id = next((_v[1] for _k, _v in asym_to_orig_seq[auth_asym_id].items()
                                                             if _k == (seq_key[1], comp_id)), comp_id)
                                    else:
                                        auth_comp_id = comp_id

                                    row = [None] * len(tags)

                                    row[0] = index

                                    entity_assembly_id, seq_id, _, _ = auth_to_star_seq[seq_key]

                                    row[1], row[4], row[5] =\
                                        entity_assembly_id, auth_comp_id, leaving_atom_id
                                    row[2] = row[3] = seq_id

                                    row[6], row[7], row[8], row[9] =\
                                        auth_asym_id, auth_seq_id, auth_comp_id, leaving_atom_id

                                    row[10], row[11] = 1, self.__reg.entry_id

                                    eda_loop.add_data(row)

                                    index += 1

                    asm_sf.add_loop(eda_loop)

        if orig_asm_sf is not None:

            # append extra categories

            if self.__reg.retain_original and file_type == 'nmr-star':

                for loop in orig_asm_sf.loops:

                    if loop.category == LP_CATEGORIES[file_type][content_subtype]:
                        continue

                    if loop.category in AUX_LP_CATEGORIES[file_type][content_subtype]:
                        continue

                    asm_sf.add_loop(loop)

            del master_entry[orig_asm_sf]

        for sf in master_entry.frame_list:
            if sf.name == sf_framecode:
                master_entry.remove_saveframe(sf_framecode)
                break

        master_entry.add_saveframe(asm_sf)

        return True, asm_sf

    def updateEntitySaveframe(self) -> bool:
        """ Update entity saveframe(s).
        """

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        master_entry = self.__reg.star_data[0]

        cif_poly_seq = self.__reg.caC['polymer_sequence']
        entity_assembly = self.__reg.caC['entity_assembly']

        # refresh _Entity saveframe

        content_subtype = 'entity'

        ent_sfs = master_entry.get_saveframes_by_category(SF_CATEGORIES[file_type][content_subtype])

        for sf in reversed(ent_sfs):
            sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
            master_entry.remove_saveframe(sf_framecode)
        # """
        # sf_key_items = [{'name': 'Sf_category', 'type': 'str', 'mandatory': True},
        #                 {'name': 'Sf_framecode', 'type': 'str', 'mandatory': True},
        #                 {'name': 'Entry_ID', 'type': 'str', 'mandatory': True},
        #                 {'name': 'ID', 'type': 'positive-int', 'mandatory': True},
        #                 ]
        # sf_items = [{'name': 'BMRB_code', 'type': 'str'},
        #                  {'name': 'Name', 'type': 'str'},
        #                  {'name': 'Type', 'type': 'enum',
        #                   'enum': ('polymer', 'non-polymer', 'water', 'aggregate', 'solvent')},
        #                  {'name': 'Polymer_common_type', 'type': 'enum',
        #                   'enum': ('protein', 'DNA', 'RNA', 'DNA/RNA hybrid', 'polysaccharide')},
        #                  {'name': 'Polymer_type', 'type': 'enum',
        #                   'enum': ('cyclic-pseudo-peptide', 'polypeptide(L)', 'polydeoxyribonucleotide', 'polyribonucleotide',
        #                            'polydeoxyribonucleotide/polyribonucleotide hybrid',
        #                            'polypeptide(D)', 'polysaccharide(D)', 'polysaccharide(L)', 'other')},
        #                  {'name': 'Polymer_type_details', 'type': 'str'},
        #                  {'name': 'Polymer_strand_ID', 'type': 'str'},
        #                  {'name': 'Polymer_seq_one_letter_code_can', 'type': 'str'},
        #                  {'name': 'Polymer_seq_one_letter_code', 'type': 'str'},
        #                  {'name': 'Target_identifier', 'type': 'str'},
        #                  {'name': 'Polymer_author_defined_seq', 'type': 'str'},
        #                  {'name': 'Polymer_author_seq_details', 'type': 'str'},
        #                  {'name': 'Ambiguous_conformational_states', 'type': 'enum',
        #                   'enum': ('yes', 'no')},
        #                  {'name': 'Ambiguous_chem_comp_sites', 'type': 'enum',
        #                   'enum': ('yes', 'no')},
        #                  {'name': 'Nstd_monomer', 'type': 'enum',
        #                   'enum': ('yes', 'no')},
        #                  {'name': 'Nstd_chirality', 'type': 'enum',
        #                   'enum': ('yes', 'no')},
        #                  {'name': 'Nstd_linkage', 'type': 'enum',
        #                   'enum': ('yes', 'no')},
        #                  {'name': 'Nonpolymer_comp_ID', 'type': 'str'},
        #                  {'name': 'Nonpolymer_comp_label', 'type': 'str'},
        #                  {'name': 'Number_of_monomers', 'type': 'int'},
        #                  {'name': 'Number_of_nonpolymer_components', 'type': 'int'},
        #                  {'name': 'Paramagnetic', 'type': 'enum',
        #                   'enum': ('yes', 'no')},
        #                  {'name': 'Thiol_state', 'type': 'enum',
        #                   'enum': ('all disulfide bound', 'all other bound', 'all free', 'not present',
        #                            'not available', 'unknown', 'not reported',
        #                            'free and disulfide bound', 'free and other bound',
        #                            'free disulfide and other bound', 'disulfide and other bound')},
        #                  {'name': 'Src_method', 'type': 'str'},
        #                  {'name': 'Parent_entity_ID}, 'type': 'int'},
        #                  {'name': 'Fragment', 'type': 'str'},
        #                  {'name': 'Mutation', 'type': 'str'},
        #                  {'name': 'EC_number', 'type': 'str'},
        #                  {'name': 'Calc_isoelectric_point', 'type': 'float'},
        #                  {'name': 'Formula_weight', 'type': 'float'},
        #                  {'name': 'Formula_weight_exptl', 'type': 'float'},
        #                  {'name': 'Formula_weight_exptl_meth', 'type': 'str'},
        #                  {'name': 'Details', 'type': 'str'},
        #                  {'name': 'DB_query_date', 'type': 'str'},
        #                  {'name': 'DB_query_revised_last_date', 'type': 'str'}
        #                  ]
        # """
        entity_ids = []

        for item in entity_assembly:
            entity_id = item['entity_id']

            if entity_id in entity_ids:
                continue

            entity_ids.append(entity_id)

            entity_type = item['entity_type']

            sf_framecode = f'entity_{entity_id}' if entity_type not in ('non-polymer', 'water') else f"entity_{item['comp_id']}"

            ent_sf = pynmrstar.Saveframe.from_scratch(sf_framecode)
            ent_sf.set_tag_prefix(SF_TAG_PREFIXES[file_type][content_subtype])
            ent_sf.add_tag('Sf_category', SF_CATEGORIES[file_type][content_subtype])
            ent_sf.add_tag('Sf_framecode', sf_framecode)
            ent_sf.add_tag('Entry_ID', self.__reg.entry_id)
            ent_sf.add_tag('ID', entity_id)
            ent_sf.add_tag('BMRB_code', None if entity_type not in ('non-polymer', 'water') else item['comp_id'])
            ent_sf.add_tag('Name', item['entity_desc'])
            ent_sf.add_tag('Type', entity_type)

            if entity_type == 'polymer':
                poly_type = item['entity_poly_type']
                if poly_type.startswith('polypeptide'):
                    common_type = 'protein'
                elif any(True for comp_id in item['comp_id_set'] if comp_id in ('DA', 'DC', 'DG', 'DT'))\
                        and any(True for comp_id in item['comp_id_set'] if comp_id in ('A', 'C', 'G', 'U')):
                    common_type = 'DNA/RNA hybrid'
                elif poly_type == 'polydeoxyribonucleotide':
                    common_type = 'DNA'
                elif poly_type == 'polyribonucleotide':
                    common_type = 'RNA'
                else:
                    common_type = None
            elif entity_type == 'branched':
                common_type = 'polysaccharide'
            else:
                common_type = None
            ent_sf.add_tag('Polymer_common_type', common_type)

            if entity_type == 'polymer':
                poly_type = item['entity_poly_type']
                if poly_type.startswith('polypeptide'):
                    _poly_type = poly_type

                    if self.__reg.cR.hasCategory('struct_conn'):
                        auth_asym_ids = item['auth_asym_id'].split(',')

                        bonds = self.__reg.cR.getDictList('struct_conn')

                        for bond in bonds:

                            try:

                                auth_asym_id_1 = bond['ptnr1_auth_asym_id']
                                auth_seq_id_1 = int(bond['ptnr1_auth_seq_id'])
                                atom_id_1 = bond['ptnr1_label_atom_id']
                                auth_asym_id_2 = bond['ptnr2_auth_asym_id']
                                auth_seq_id_2 = int(bond['ptnr2_auth_seq_id'])
                                atom_id_2 = bond['ptnr2_label_atom_id']

                                if auth_asym_id_1 == auth_asym_id_2 and auth_asym_id_1 in auth_asym_ids\
                                   and {atom_id_1, atom_id_2} == {'C', 'N'} and abs(auth_seq_id_1 - auth_seq_id_2) > 1:
                                    _poly_type = 'cyclic-pseudo-peptide'

                            except ValueError:
                                continue

                elif any(True for comp_id in item['comp_id_set'] if comp_id in ('DA', 'DC', 'DG', 'DT'))\
                        and any(True for comp_id in item['comp_id_set'] if comp_id in ('A', 'C', 'G', 'U')):
                    _poly_type = 'polydeoxyribonucleotide/polyribonucleotide hybrid'
                else:
                    _poly_type = poly_type
            elif entity_type == 'branched':
                _poly_type = item['entity_poly_type']
            else:
                _poly_type = None

            ent_sf.add_tag('Polymer_type', _poly_type)
            ent_sf.add_tag('Polymer_type_details', None)

            auth_asym_ids = []
            for _item in entity_assembly:
                if _item['entity_id'] != entity_id:
                    continue
                if _item['auth_asym_id'] in auth_asym_ids:
                    continue
                auth_asym_ids.append(_item['auth_asym_id'])
            auth_asym_id_list = ','.join(auth_asym_ids)
            if len(auth_asym_id_list) > 12 and ',' in auth_asym_id_list:
                last_asym_id = ',..,' + auth_asym_id_list.rsplit(',', maxsplit=1)[-1]
                max_len = 11 - len(last_asym_id)
                while True:
                    if auth_asym_id_list[max_len] == ',':
                        break
                    max_len -= 1
                auth_asym_id_list = auth_asym_id_list[:max_len] + last_asym_id
            ent_sf.add_tag('Polymer_strand_ID', auth_asym_id_list)

            one_letter_code_can = one_letter_code = None
            nmr_ext_monomers = 0
            nmr_ext_fw = 0.0
            if entity_type == 'polymer':
                one_letter_code_can = item['one_letter_code_can']
                one_letter_code = item['one_letter_code']
                if self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                   and any(True for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] in auth_asym_ids):
                    ps = next(ps for ps in cif_poly_seq if ps['auth_chain_id'] in auth_asym_ids)
                    auth_seq_ids = list(filter(None, ps['auth_seq_id']))
                    min_auth_seq_id = min(auth_seq_ids)
                    max_auth_seq_id = max(auth_seq_ids)
                    comp_ids = []
                    for d in self.__reg.nmr_ext_poly_seq:
                        if d['auth_chain_id'] in auth_asym_ids:
                            if d['auth_seq_id'] < min_auth_seq_id:
                                comp_ids.append(d['auth_comp_id'])
                                nmr_ext_monomers += 1
                                nmr_ext_fw += self.__reg.ccU.getEffectiveFormulaWeight(d['auth_comp_id'])
                    comp_ids.extend(ps['comp_id'])
                    for d in self.__reg.nmr_ext_poly_seq:
                        if d['auth_chain_id'] in auth_asym_ids:
                            if d['auth_seq_id'] > max_auth_seq_id:
                                comp_ids.append(d['auth_comp_id'])
                                nmr_ext_monomers += 1
                                nmr_ext_fw += self.__reg.ccU.getEffectiveFormulaWeight(d['auth_comp_id'])
                    one_letter_code_can = getOneLetterCodeCanSequence(comp_ids)
                    one_letter_code = getOneLetterCodeSequence(comp_ids)

            ent_sf.add_tag('Polymer_seq_one_letter_code_can', None if entity_type != 'polymer' else one_letter_code_can)
            ent_sf.add_tag('Polymer_seq_one_letter_code', None if entity_type != 'polymer' else one_letter_code)
            ent_sf.add_tag('Target_identifier', None if entity_type != 'polymer' else item['target_identifier'])
            ent_sf.add_tag('Polymer_author_defined_seq', None)
            ent_sf.add_tag('Polymer_author_seq_details', None)
            ent_sf.add_tag('Ambiguous_conformational_states', None)
            ent_sf.add_tag('Ambiguous_chem_comp_sites', None)
            ent_sf.add_tag('Nstd_monomer', None if entity_type != 'polymer' else item['nstd_monomer'])
            ent_sf.add_tag('Nstd_chirality', None if entity_type != 'polymer' else item['nstd_chirality'])
            ent_sf.add_tag('Nstd_linkage', None if entity_type != 'polymer' else item['nstd_linkage'])
            ent_sf.add_tag('Nonpolymer_comp_ID', None if entity_type not in ('non-polymer', 'water') else item['comp_id'])
            ent_sf.add_tag('Nonpolymer_comp_label', None if entity_type != 'non-polymer' else f"$chem_comp_{item['comp_id']}")
            ent_sf.add_tag('Number_of_monomers',
                           None if entity_type in ('non-polymer', 'water') else item['num_of_monomers'] + nmr_ext_monomers)
            ent_sf.add_tag('Number_of_nonpolymer_components', None if entity_type not in ('non-polymer', 'water') else 1)
            ent_sf.add_tag('Paramagnetic',
                           'no' if not self.__paramag or entity_type not in ('non-polymer', 'water')
                           or item['comp_id'] not in PARAMAGNETIC_ELEMENTS else 'yes')

            _label_asym_id = 'label_asym_id' if 'fixed_label_asym_id' not in item else 'fixed_label_asym_id'

            cys_total = 0
            label_asym_ids = set(item[_label_asym_id].split(','))
            for chain_id in label_asym_ids:
                if entity_type == 'polymer':
                    ps = next(ps for ps in cif_poly_seq if ps['chain_id'] == chain_id)
                    cys_total += ps['comp_id'].count('CYS') + ps['comp_id'].count('DCY')

            if cys_total > 0:
                disul_cys = other_cys = 0
                if self.__reg.cR.hasCategory('struct_conn'):
                    bonds = self.__reg.cR.getDictList('struct_conn')
                    for bond in bonds:
                        label_asym_id_1 = bond['ptnr1_label_asym_id']
                        auth_comp_id_1 = bond['ptnr1_auth_comp_id']
                        label_asym_id_2 = bond['ptnr2_label_asym_id']
                        atom_id_1 = bond['ptnr1_label_atom_id']
                        auth_comp_id_2 = bond['ptnr2_auth_comp_id']
                        atom_id_2 = bond['ptnr2_label_atom_id']

                        if label_asym_id_1 in label_asym_ids and auth_comp_id_1 in ('CYS', 'DCY') and atom_id_1 == 'SG':
                            if auth_comp_id_2 in ('CYS', 'DCY') and atom_id_2 == 'SG':
                                disul_cys += 1
                            else:
                                other_cys += 1

                        if label_asym_id_2 in label_asym_ids and auth_comp_id_2 in ('CYS', 'DCY') and atom_id_2 == 'SG':
                            if auth_comp_id_1 in ('CYS', 'DCY') and atom_id_1 == 'SG':
                                disul_cys += 1
                            else:
                                other_cys += 1

                free_cys = cys_total - disul_cys - other_cys

                if free_cys > 0:
                    if free_cys == cys_total:
                        thiol_state = 'all free'
                    elif disul_cys > 0 and other_cys > 0:
                        thiol_state = 'free disulfide and other bound'
                    elif other_cys == 0:
                        thiol_state = 'free and disulfide bound'
                    else:
                        thiol_state = 'free and other bound'
                else:
                    if disul_cys > 0 and other_cys > 0:
                        thiol_state = 'disulfide and other bound'
                    elif other_cys == 0:
                        thiol_state = 'all disulfide bound'
                    else:
                        thiol_state = 'all other bound'
            else:
                thiol_state = 'not present'
            ent_sf.add_tag('Thiol_state', thiol_state)
            ent_sf.add_tag('Src_method', item['entity_src_method'])
            ent_sf.add_tag('Parent_entity_ID', None if entity_type != 'polymer' else item['entity_parent'])
            ent_sf.add_tag('Fragment', None if entity_type != 'polymer' else item['entity_fragment'])
            ent_sf.add_tag('Mutation', None if entity_type != 'polymer' else item['entity_mutation'])
            ent_sf.add_tag('EC_number', None if entity_type != 'polymer' else item['entity_ec'])
            ent_sf.add_tag('Calc_isoelectric_point', None)
            ent_sf.add_tag('Formula_weight', item['entity_fw'] if nmr_ext_monomers == 0 else round(item['entity_fw'] + nmr_ext_fw, 3))
            ent_sf.add_tag('Formula_weight_exptl', None)
            ent_sf.add_tag('Formula_weight_exptl_meth', None)
            ent_sf.add_tag('Details', item['entity_details'])
            ent_sf.add_tag('DB_query_date', None)
            ent_sf.add_tag('DB_query_revised_last_date', None)

            # refresh _Entity_common_name loop

            if self.__reg.cR.hasCategory('entity_name_com'):
                lp_category = '_Entity_common_name'
                ecn_loop = pynmrstar.Loop.from_scratch(lp_category)

                ecn_key_items = [{'name': 'Name', 'type': 'str'},
                                 {'name': 'Type', 'type': 'enum',
                                  'enum': ('common', 'abbreviation', 'synonym')}
                                 ]
                ecn_data_items = [{'name': 'Entity_ID', 'type': 'pointer-index', 'mandatory': True,
                                   'default': '1', 'default-from': 'parent'},
                                  {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                                  ]

                tags = [lp_category + '.' + _item['name'] for _item in ecn_key_items]
                tags.extend([lp_category + '.' + _item['name'] for _item in ecn_data_items])

                ecn_loop.add_tag(tags)

                ent_name_coms = self.__reg.cR.getDictList('entity_name_com')
                for ent_name_com in ent_name_coms:
                    if int(ent_name_com['entity_id']) == entity_id:
                        row = [None] * len(tags)

                        row[0], row[1], row[2], row[3] =\
                            ent_name_com['name'], 'common', entity_id, self.__reg.entry_id

                        ecn_loop.add_data(row)

                if not ecn_loop.empty:
                    ent_sf.add_loop(ecn_loop)

            # refresh _Entity_systematic_name loop

            if self.__reg.cR.hasCategory('entity_name_sys'):
                lp_category = '_Entity_systematic_name'
                esn_loop = pynmrstar.Loop.from_scratch(lp_category)

                esn_key_items = [{'name': 'Name', 'type': 'str'},
                                 {'name': 'Naming_system', 'type': 'enum',
                                  'enum': ('IUPAC', 'CAS name', 'CAS registry number', 'BMRB',
                                           'Three letter code', 'Pfam', 'Swiss-Prot', 'EC', 'NCBI')}
                                 ]
                esn_data_items = [{'name': 'Entity_ID', 'type': 'pointer-index', 'mandatory': True,
                                   'default': '1', 'default-from': 'parent'},
                                  {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                                  ]

                tags = [lp_category + '.' + _item['name'] for _item in esn_key_items]
                tags.extend([lp_category + '.' + _item['name'] for _item in esn_data_items])

                esn_loop.add_tag(tags)

                ent_name_syss = self.__reg.cR.getDictList('entity_name_sys')
                for ent_name_sys in ent_name_syss:
                    if int(ent_name_sys['entity_id']) == entity_id:
                        row = [None] * len(tags)

                        row[0], row[1], row[2], row[3] =\
                            ent_name_sys['name'], ent_name_sys.get('system'), entity_id, self.__reg.entry_id

                        esn_loop.add_data(row)

                if not esn_loop.empty:
                    ent_sf.add_loop(esn_loop)

            # refresh _Entity_keyword loop

            if self.__reg.cR.hasCategory('entity_keywords'):
                lp_category = '_Entity_keyword'
                ek_loop = pynmrstar.Loop.from_scratch(lp_category)

                ek_key_items = [{'name': 'Keyword', 'type': 'str'}
                                ]
                ek_data_items = [{'name': 'Entity_ID', 'type': 'pointer-index', 'mandatory': True,
                                  'default': '1', 'default-from': 'parent'},
                                 {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                                 ]

                tags = [lp_category + '.' + _item['name'] for _item in ek_key_items]
                tags.extend([lp_category + '.' + _item['name'] for _item in ek_data_items])

                ek_loop.add_tag(tags)

                ent_keys = self.__reg.cR.getDictList('entity_keywords')
                for ent_key in ent_keys:
                    if int(ent_key['entity_id']) == entity_id and 'text' in ent_key and ent_key['text'] not in EMPTY_VALUE:
                        row = [None] * len(tags)

                        row[0], row[1], row[2] =\
                            ent_key['text'], entity_id, self.__reg.entry_id

                        ek_loop.add_data(row)

                if not ek_loop.empty:
                    ent_sf.add_loop(ek_loop)

            # refresh _Entity_comp_index loop

            lp_category = '_Entity_comp_index'
            eci_loop = pynmrstar.Loop.from_scratch(lp_category)

            eci_key_items = [{'name': 'ID', 'type': 'positive-int'},
                             {'name': 'Auth_seq_ID', 'type': 'int'},
                             {'name': 'Comp_ID', 'type': 'str'}
                             ]
            eci_data_items = [{'name': 'Comp_label', 'type': 'str'},
                              {'name': 'Entity_ID', 'type': 'pointer-index', 'mandatory': True, 'default': '1', 'default-from': 'parent'},
                              {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                              ]

            tags = [lp_category + '.' + _item['name'] for _item in eci_key_items]
            tags.extend([lp_category + '.' + _item['name'] for _item in eci_data_items])

            eci_loop.add_tag(tags)

            index = 1

            label_asym_ids = []
            for chain_id in item['label_asym_id'].split(','):
                if chain_id not in label_asym_ids:
                    label_asym_ids.append(chain_id)

            min_auth_seq_id = max_auth_seq_id = max_seq_id = -1

            for chain_id in label_asym_ids:
                if entity_type == 'polymer':
                    ps = next(ps for ps in cif_poly_seq if ps['chain_id'] == chain_id)
                    auth_seq_ids = list(filter(None, ps['auth_seq_id']))
                    seq_ids = list(filter(None, ps['seq_id']))
                    min_auth_seq_id = min(auth_seq_ids)
                    max_auth_seq_id = max(auth_seq_ids)
                    max_seq_id = max(seq_ids)
                elif entity_type == 'branched':
                    ps = next(ps for ps in self.__reg.caC['branched'] if ps['chain_id'] == chain_id)
                else:
                    ps = next(ps for ps in self.__reg.caC['non_polymer'] if ps['chain_id'] == chain_id)

                seq_keys = set()

                for auth_seq_id, seq_id, comp_id in zip(ps['auth_seq_id'], ps['seq_id'],
                                                        ps['auth_comp_id'] if 'auth_comp_id' in ps else ps['comp_id']):
                    seq_key = (ps['auth_chain_id'], seq_id)

                    if seq_key in seq_keys:
                        continue

                    if entity_type in ('non-polymer', 'water'):
                        if comp_id != item['comp_id']:
                            continue
                        auth_seq_id = seq_id

                    if entity_type == 'polymer' and self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                       and any(True for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == ps['auth_chain_id']
                               and d['auth_seq_id'] < min_auth_seq_id):
                        for d in self.__reg.nmr_ext_poly_seq:
                            auth_asym_id = ps['auth_chain_id']
                            _auth_seq_id = ps['auth_seq_id'][ps['seq_id'].index(seq_id)]
                            if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] < _auth_seq_id:
                                _offset = seq_id - _auth_seq_id
                                _seq_id = d['auth_seq_id'] + _offset
                                _seq_key = (auth_asym_id, _seq_id)
                                if _seq_key in seq_keys:
                                    continue
                                seq_keys.add(_seq_key)
                                row = [None] * len(tags)
                                row[0], row[1], row[2] = _seq_id, d['auth_seq_id'], d['auth_comp_id']
                                if d['auth_comp_id'] not in STD_MON_DICT and d['auth_comp_id'] != 'HOH':
                                    row[3] = f"$chem_comp_{d['auth_comp_id']}"
                                row[4], row[5] = entity_id, self.__reg.entry_id

                                eci_loop.add_data(row)

                    row = [None] * len(tags)

                    seq_keys.add(seq_key)

                    row[0], row[1], row[2] = seq_id if entity_type == 'polymer' else index, auth_seq_id, comp_id

                    if comp_id not in STD_MON_DICT and comp_id != 'HOH':
                        row[3] = f"$chem_comp_{comp_id}"

                    row[4], row[5] = entity_id, self.__reg.entry_id

                    if comp_id not in EMPTY_VALUE:
                        eci_loop.add_data(row)

                    index += 1

            if entity_type == 'polymer' and self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
               and any(True for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == ps['auth_chain_id']
                       and d['auth_seq_id'] > max_auth_seq_id):
                _offset = max_seq_id - max_auth_seq_id
                for d in self.__reg.nmr_ext_poly_seq:
                    auth_asym_id = ps['auth_chain_id']
                    if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] > max_auth_seq_id:
                        _seq_id = d['auth_seq_id'] + _offset
                        row = [None] * len(tags)
                        row[0], row[1], row[2] = _seq_id, d['auth_seq_id'], d['auth_comp_id']
                        if d['auth_comp_id'] not in STD_MON_DICT and d['auth_comp_id'] != 'HOH':
                            row[3] = f"$chem_comp_{d['auth_comp_id']}"
                        row[4], row[5] = entity_id, self.__reg.entry_id

                        eci_loop.add_data(row)

            ent_sf.add_loop(eci_loop)

            # refresh _Entity_poly_seq loop

            if entity_type not in ('non-polymer', 'water'):
                lp_category = '_Entity_poly_seq'
                eps_loop = pynmrstar.Loop.from_scratch(lp_category)

                eps_key_items = [{'name': 'Hetero', 'type': 'str'},
                                 {'name': 'Mon_ID', 'type': 'str'},
                                 {'name': 'Num', 'type': 'int'},
                                 {'name': 'Comp_index_ID', 'type': 'int'}
                                 ]
                eps_data_items = [{'name': 'Entity_ID', 'type': 'pointer-index', 'mandatory': True,
                                   'default': '1', 'default-from': 'parent'},
                                  {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                                  ]

                tags = [lp_category + '.' + _item['name'] for _item in eps_key_items]
                tags.extend([lp_category + '.' + _item['name'] for _item in eps_data_items])

                eps_loop.add_tag(tags)

                seq_keys = set()

                label_asym_ids = list(set(item['label_asym_id'].split(',')))
                for chain_id in sorted(sorted(label_asym_ids), key=len):
                    if entity_type == 'polymer':
                        ps = next(ps for ps in cif_poly_seq if ps['chain_id'] == chain_id)
                        auth_seq_ids = list(filter(None, ps['auth_seq_id']))
                        seq_ids = list(filter(None, ps['seq_id']))
                        min_auth_seq_id = min(auth_seq_ids)
                        max_auth_seq_id = max(auth_seq_ids)
                        max_seq_id = max(seq_ids)
                    else:  # 'branched':
                        ps = next(ps for ps in self.__reg.caC['branched'] if ps['chain_id'] == chain_id)

                    for seq_id, comp_id in zip(ps['seq_id'], ps['auth_comp_id'] if 'auth_comp_id' in ps else ps['comp_id']):
                        seq_key = (ps['auth_chain_id'], seq_id)

                        if seq_key in seq_keys:
                            continue

                        if entity_type in ('non-polymer', 'water'):
                            if comp_id != item['comp_id']:
                                continue

                        if entity_type == 'polymer' and self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                           and any(True for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == ps['auth_chain_id']
                                   and d['auth_seq_id'] < min_auth_seq_id):
                            for d in self.__reg.nmr_ext_poly_seq:
                                auth_asym_id = ps['auth_chain_id']
                                auth_seq_id = ps['auth_seq_id'][ps['seq_id'].index(seq_id)]
                                if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] < auth_seq_id:
                                    _offset = seq_id - auth_seq_id
                                    _seq_id = d['auth_seq_id'] + _offset
                                    _seq_key = (auth_asym_id, _seq_id)
                                    if _seq_key in seq_keys:
                                        continue
                                    seq_keys.add(_seq_key)
                                    row = [None] * len(tags)
                                    row[1], row[2], row[3], row[4], row[5] =\
                                        d['auth_comp_id'], _seq_id, _seq_id, entity_id, self.__reg.entry_id

                                    eps_loop.add_data(row)

                        row = [None] * len(tags)

                        seq_keys.add(seq_key)

                        row[1], row[4], row[5] = comp_id, entity_id, self.__reg.entry_id
                        row[2] = row[3] = seq_id

                        if comp_id not in EMPTY_VALUE:
                            eps_loop.add_data(row)

                    if entity_type == 'polymer' and self.__reg.nmr_ext_poly_seq is not None and len(self.__reg.nmr_ext_poly_seq) > 0\
                       and any(True for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == ps['auth_chain_id']
                               and d['auth_seq_id'] > max_auth_seq_id):
                        _offset = max_seq_id - max_auth_seq_id
                        for d in self.__reg.nmr_ext_poly_seq:
                            auth_asym_id = ps['auth_chain_id']
                            if d['auth_chain_id'] == auth_asym_id and d['auth_seq_id'] > max_auth_seq_id:
                                _seq_id = d['auth_seq_id'] + _offset
                                row = [None] * len(tags)
                                row[1], row[2], row[3], row[4], row[5] =\
                                    d['auth_comp_id'], _seq_id, _seq_id, entity_id, self.__reg.entry_id

                                eps_loop.add_data(row)

                ent_sf.add_loop(eps_loop)

            master_entry.add_saveframe(ent_sf)

    def updateCompIdInCsLoop(self, file_list_id: int, cif_ps: dict, nmr_ps: dict) -> bool:
        """ Update residue name in CS loop to follow CCD replacement.
        """

        if len(cif_ps['seq_id']) != len(nmr_ps['seq_id']) or cif_ps['comp_id'] == nmr_ps['comp_id']:
            return False

        input_source = self.__reg.report.input_sources[file_list_id]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        if file_type == 'nef' or file_list_id >= len(self.__reg.star_data) or self.__reg.star_data[file_list_id] is None:
            return False

        if input_source_dic['content_subtype'] is None:
            return False

        content_subtype = 'chem_shift'

        if content_subtype not in input_source_dic['content_subtype']:
            return False

        has_poly_seq = has_key_value(input_source_dic, 'polymer_sequence')
        has_poly_seq_in_lp = has_key_value(input_source_dic, 'polymer_sequence_in_loop')

        if (not has_poly_seq) or (not has_poly_seq_in_lp):
            return False

        poly_seq_in_lp = input_source_dic['polymer_sequence_in_loop']

        if content_subtype not in poly_seq_in_lp:
            return False

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        _poly_seq_in_lp = poly_seq_in_lp[content_subtype]

        modified = False

        list_id = 1

        if self.__reg.star_data_type[file_list_id] == 'Loop':
            sf = self.__reg.star_data[file_list_id]

            try:
                poly_seq = next(poly_seq['polymer_sequence'] for poly_seq in _poly_seq_in_lp if poly_seq['list_id'] == list_id)
                next(ps for ps in poly_seq if ps['chain_id'] == nmr_ps['chain_id'])
            except StopIteration:
                return False

            allow_chain_id_mismatch = len(poly_seq) == 1

            modified |= self.__updateCompIdInCsLoop(file_list_id, sf, lp_category, cif_ps, nmr_ps, allow_chain_id_mismatch)

        elif self.__reg.star_data_type[file_list_id] == 'Saveframe':
            sf = self.__reg.star_data[file_list_id]

            try:
                poly_seq = next(poly_seq['polymer_sequence'] for poly_seq in _poly_seq_in_lp if poly_seq['list_id'] == list_id)
                next(ps for ps in poly_seq if ps['chain_id'] == nmr_ps['chain_id'])
            except StopIteration:
                return False

            allow_chain_id_mismatch = len(poly_seq) == 1

            modified |= self.__updateCompIdInCsLoop(file_list_id, sf, lp_category, cif_ps, nmr_ps, allow_chain_id_mismatch)

        else:

            for list_id, sf in enumerate(self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category), start=1):

                if not any(True for loop in sf.loops if loop.category == lp_category):
                    continue

                try:
                    poly_seq = next(poly_seq['polymer_sequence'] for poly_seq in _poly_seq_in_lp if poly_seq['list_id'] == list_id)
                    next(ps for ps in poly_seq if ps['chain_id'] == nmr_ps['chain_id'])
                except StopIteration:
                    continue

                allow_chain_id_mismatch = len(poly_seq) == 1

                modified |= self.__updateCompIdInCsLoop(file_list_id, sf, lp_category, cif_ps, nmr_ps, allow_chain_id_mismatch)

        return modified

    def __updateCompIdInCsLoop(self, file_list_id: int,
                               sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                               lp_category: str, cif_ps: dict, nmr_ps: dict, allow_chain_id_mismatch: bool) -> bool:
        """ Update residue name in CS loop to follow CCD replacement.
        """

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        chain_id_col = loop.tags.index('Entity_assembly_ID')
        seq_id_col = loop.tags.index('Comp_index_ID')
        comp_id_col = loop.tags.index('Comp_ID')
        auth_comp_id_col = loop.tags.index('Auth_comp_ID') if 'Auth_comp_ID' in loop.tags else -1

        nmr_chain_id = nmr_ps['chain_id']

        comp_id_map = {nmr_seq_id: cif_comp_id
                       for cif_comp_id, nmr_seq_id, nmr_comp_id
                       in zip(cif_ps['comp_id'], nmr_ps['seq_id'], nmr_ps['comp_id'])
                       if cif_comp_id != nmr_comp_id}

        modified = False

        for row in loop:
            if (not allow_chain_id_mismatch and row[chain_id_col] != nmr_chain_id) or row[seq_id_col] in EMPTY_VALUE:
                continue

            try:
                nmr_seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
            except ValueError:
                continue

            if nmr_seq_id not in comp_id_map:
                continue

            cif_comp_id = comp_id_map[nmr_seq_id]

            row[comp_id_col] = cif_comp_id

            if auth_comp_id_col != -1:
                row[auth_comp_id_col] = cif_comp_id

            modified = True

        return modified

    def resolveUnmappedAuthSequenceInCsLoop(self, file_list_id: int, cif_ps: dict, nmr_ps: dict) -> bool:
        """ Resolve unmapped author sequence in CS loop based on sequence alignment.
        """

        input_source = self.__reg.report.input_sources[file_list_id]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        if file_type == 'nef' or file_list_id >= len(self.__reg.star_data) or self.__reg.star_data[file_list_id] is None:
            return False

        if input_source_dic['content_subtype'] is None:
            return False

        content_subtype = 'chem_shift'

        if content_subtype not in input_source_dic['content_subtype']:
            return False

        has_poly_seq = has_key_value(input_source_dic, 'polymer_sequence')
        has_poly_seq_in_lp = has_key_value(input_source_dic, 'polymer_sequence_in_loop')

        if (not has_poly_seq) or (not has_poly_seq_in_lp):
            return False

        poly_seq_in_lp = input_source_dic['polymer_sequence_in_loop']

        if content_subtype not in poly_seq_in_lp:
            return False

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        _poly_seq_in_lp = poly_seq_in_lp[content_subtype]

        modified = False

        list_id = 1

        if self.__reg.star_data_type[file_list_id] == 'Loop':
            sf = self.__reg.star_data[file_list_id]

            try:
                poly_seq = next(poly_seq['polymer_sequence'] for poly_seq in _poly_seq_in_lp if poly_seq['list_id'] == list_id)
                next(ps for ps in poly_seq if ps['chain_id'] == nmr_ps['chain_id'])
            except StopIteration:
                return False

            allow_chain_id_mismatch = len(poly_seq) == 1

            modified |= self.__resolveUnmappedAuthSequenceInCsLoop(file_list_id,
                                                                   sf, lp_category, cif_ps, nmr_ps, allow_chain_id_mismatch)

        elif self.__reg.star_data_type[file_list_id] == 'Saveframe':
            sf = self.__reg.star_data[file_list_id]

            try:
                poly_seq = next(poly_seq['polymer_sequence'] for poly_seq in _poly_seq_in_lp if poly_seq['list_id'] == list_id)
                next(ps for ps in poly_seq if ps['chain_id'] == nmr_ps['chain_id'])
            except StopIteration:
                return False

            allow_chain_id_mismatch = len(poly_seq) == 1

            modified |= self.__resolveUnmappedAuthSequenceInCsLoop(file_list_id,
                                                                   sf, lp_category, cif_ps, nmr_ps, allow_chain_id_mismatch)

        else:

            for list_id, sf in enumerate(self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category), start=1):

                if not any(True for loop in sf.loops if loop.category == lp_category):
                    continue

                try:
                    poly_seq = next(poly_seq['polymer_sequence'] for poly_seq in _poly_seq_in_lp if poly_seq['list_id'] == list_id)
                    next(ps for ps in poly_seq if ps['chain_id'] == nmr_ps['chain_id'])
                except StopIteration:
                    continue

                allow_chain_id_mismatch = len(poly_seq) == 1

                modified |= self.__resolveUnmappedAuthSequenceInCsLoop(file_list_id,
                                                                       sf, lp_category, cif_ps, nmr_ps, allow_chain_id_mismatch)

        return modified

    def __resolveUnmappedAuthSequenceInCsLoop(self, file_list_id: int,
                                              sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                                              lp_category: str, cif_ps: dict, nmr_ps: dict, allow_chain_id_mismatch: bool) -> bool:
        """ Resolve unmapped author sequence in CS loop based on sequence alignment.
        """

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        chain_id_col = loop.tags.index('Entity_assembly_ID')
        seq_id_col = loop.tags.index('Comp_index_ID')
        auth_chain_id_col = loop.tags.index('Auth_asym_ID') if 'Auth_asym_ID' in loop.tags else -1
        auth_seq_id_col = loop.tags.index('Auth_seq_ID') if 'Auth_seq_ID' in loop.tags else -1

        if auth_chain_id_col == -1:
            return False

        chain_id = cif_ps['chain_id']

        self.__reg.pA.setReferenceSequence(cif_ps['comp_id'], 'REF' + chain_id)
        self.__reg.pA.addTestSequence(nmr_ps['comp_id'], chain_id)
        self.__reg.pA.doAlign()

        myAlign = self.__reg.pA.getAlignment(chain_id)

        length = len(myAlign)

        if length == 0:
            return False

        _matched, unmapped, conflict, offset_1, offset_2 = getScoreOfSeqAlign(myAlign)

        if length == unmapped + conflict or conflict > 0:
            return False

        _cif_ps = cif_ps if offset_1 == 0 else fillBlankCompIdWithOffset(cif_ps, offset_1)
        _nmr_ps = nmr_ps if offset_2 == 0 else fillBlankCompIdWithOffset(nmr_ps, offset_2)

        nmr_chain_id = nmr_ps['chain_id']

        modified = False

        for row in loop:
            if (not allow_chain_id_mismatch and row[chain_id_col] != nmr_chain_id) or row[seq_id_col] in EMPTY_VALUE:
                continue

            try:
                nmr_seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
            except ValueError:
                continue

            if nmr_seq_id not in nmr_ps['seq_id']:
                continue

            if row[auth_chain_id_col] in EMPTY_VALUE or row[auth_chain_id_col] == 'UNMAPPED':
                row[auth_chain_id_col] = cif_ps['auth_chain_id' if 'auth_chain_id' in cif_ps else 'chain_id']
                if auth_seq_id_col != -1:
                    try:
                        str(next(_cif_seq_id for _cif_seq_id, _nmr_seq_id
                                 in zip(_cif_ps['auth_seq_id' if 'auth_seq_id' in _cif_ps else 'seq_id'],
                                        _nmr_ps['seq_id'])
                                 if _nmr_seq_id == nmr_seq_id))
                    except StopIteration:  # D_1300044764
                        return False

        for row in loop:
            if (not allow_chain_id_mismatch and row[chain_id_col] != nmr_chain_id) or row[seq_id_col] in EMPTY_VALUE:
                continue

            try:
                nmr_seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
            except ValueError:
                continue

            if nmr_seq_id not in nmr_ps['seq_id']:
                continue

            if row[auth_chain_id_col] in EMPTY_VALUE or row[auth_chain_id_col] == 'UNMAPPED':
                row[auth_chain_id_col] = cif_ps['auth_chain_id' if 'auth_chain_id' in cif_ps else 'chain_id']
                if auth_seq_id_col != -1:
                    row[auth_seq_id_col] =\
                        str(next(_cif_seq_id for _cif_seq_id, _nmr_seq_id
                                 in zip(_cif_ps['auth_seq_id' if 'auth_seq_id' in _cif_ps else 'seq_id'],
                                        _nmr_ps['seq_id'])
                                 if _nmr_seq_id == nmr_seq_id))

                modified = True

        return modified

    def sortCsLoop(self) -> bool:
        """ Sort assigned chemical shift loop if required.
        """

        if not self.__reg.combined_mode:
            return True

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']
        file_type = input_source_dic['file_type']

        if input_source_dic['content_subtype'] is None:
            return False

        content_subtype = 'chem_shift'

        if content_subtype not in input_source_dic['content_subtype']:
            return False

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = LP_CATEGORIES[file_type][content_subtype]

        key_items = self.__reg.key_items[file_type][content_subtype]
        data_items = DATA_ITEMS[file_type][content_subtype]
        allowed_tags = ALLOWED_TAGS[file_type][content_subtype]

        item_names = ITEM_NAMES_IN_CS_LOOP[file_type]
        chain_id_name = item_names['chain_id']
        seq_id_name = item_names['seq_id']
        iso_number_name = item_names['isotope_number']
        atom_id_name = item_names['atom_id']
        idx_name = 'ID'

        # modified = False

        for sf in self.__reg.star_data[0].get_saveframes_by_category(sf_category):
            sf_framecode = get_first_sf_tag(sf, 'sf_framecode')

            if self.__reg.report.error.exists(file_name, sf_framecode):
                continue

            try:

                lp_data = next((lp['data'] for lp in self.__reg.lp_data[content_subtype]
                                if lp['file_name'] == file_name and lp['sf_framecode'] == sf_framecode), None)

                if lp_data is None:
                    lp_data = self.__reg.nefT.check_data(sf, lp_category, key_items, data_items, allowed_tags, None, None,
                                                         enforce_allowed_tags=(file_type == 'nmr-star'),
                                                         excl_missing_data=self.__reg.excl_missing_data)[0]

                    self.__reg.lp_data[content_subtype].append({'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                'category': lp_category, 'data': lp_data})

                _key_items = copy.copy(key_items)
                _key_items.append({'name': idx_name, 'type': 'positive-int'})

                _lp_data = self.__reg.nefT.check_data(sf, lp_category, _key_items, data_items, allowed_tags, None, None,
                                                      enforce_allowed_tags=(file_type == 'nmr-star'),
                                                      excl_missing_data=self.__reg.excl_missing_data)[0]

            except Exception:
                continue

            atoms = []

            chain_ids = set()

            for row in _lp_data:
                chain_ids.add(row[chain_id_name])

            min_seq_ids = {c: 0 for c in chain_ids}

            for row in _lp_data:
                chain_id = row[chain_id_name]
                seq_id = row[seq_id_name]

                if seq_id < min_seq_ids[chain_id]:
                    min_seq_ids[chain_id] = seq_id

            for row in _lp_data:
                chain_id = row[chain_id_name]
                seq_id = row[seq_id_name]
                iso_number = row[iso_number_name]
                atom_id = row[atom_id_name]
                idx = row[idx_name]

                atoms.append((chain_id if isinstance(chain_id, int)
                              else int(chain_id) if chain_id.isdigit()
                              else letterToDigit(chain_id),
                              seq_id - min_seq_ids[chain_id],
                              iso_number, atom_id, idx))

            sorted_atoms = sorted(atoms, key=itemgetter(0, 1, 2, 3))

            sorted_idx = [atom[4] for atom in sorted_atoms]

            if sorted_idx != list(range(1, len(_lp_data) + 1)):

                loop = sf.get_loop(lp_category)

                lp = pynmrstar.Loop.from_scratch(lp_category)

                lp.add_tag(loop.tags)

                dat = [int(idx) for idx in loop.get_tag([idx_name])]

                idx_col = lp.tags.index(idx_name)

                for new_idx, old_idx in enumerate(sorted_idx, start=1):
                    row = loop.data[dat.index(old_idx)]
                    row[idx_col] = new_idx

                    lp.add_data(row)

                del sf[loop]

                sf.add_loop(lp)

        return True

    def remediateCsLoop(self, file_list_id: int, file_type: str, content_subtype: str,
                        sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                        list_id: int, sf_framecode: str, lp_category: str) -> bool:
        """ Remediate assigned chemical shift loop based on coordinates.
        """

        has_coordinate = self.__reg.report.getInputSourceIdOfCoord() >= 0

        input_source = self.__reg.report.input_sources[file_list_id]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']

        has_poly_seq_in_lp = has_key_value(input_source_dic, 'polymer_sequence_in_loop')

        if not has_poly_seq_in_lp:
            return False

        try:

            if file_type == 'nmr-star':

                _lp_category = '_Systematic_chem_shift_offset'

                _loop = sf.get_loop(_lp_category)

                if 'Type' in _loop.tags:
                    type_col = _loop.tags.index('Type')
                    for _row in _loop:
                        if _row[type_col] in EMPTY_VALUE:
                            continue
                        text = _row[type_col].lower()
                        if 'sail' in text or 'stereo-array isotope labeling' in text:
                            self.__reg.sail_flag = True
                            break

                if 'sample' in self.__reg.sf_category_list\
                   and '_Sample_component' in self.__reg.lp_category_list:

                    _lp_category = '_Sample_component'

                    for _sf in self.__reg.star_data[file_list_id].get_saveframes_by_category('sample'):

                        _loop = _sf.get_loop(_lp_category)

                        if 'Isotopic_labeling' in _loop.tags:
                            isotopic_labeling_col = _loop.tags.index('Isotopic_labeling')
                            for _row in _loop:
                                if _row[isotopic_labeling_col] in EMPTY_VALUE:
                                    continue
                                text = _row[isotopic_labeling_col].lower()
                                if 'sail' in text or 'stereo-array isotope labeling' in text:
                                    self.__reg.sail_flag = True
                                    break

        except KeyError:
            pass

        poly_seq_in_lp = input_source_dic['polymer_sequence_in_loop']

        poly_seq_common = input_source_dic['polymer_sequence']

        poly_seq = seq_align = chain_assign = br_seq_align = br_chain_assign = np_seq_align = np_chain_assign = None

        if content_subtype in poly_seq_in_lp and self.__reg.caC is not None:
            _poly_seq_in_lp = next((_poly_seq_in_lp for _poly_seq_in_lp in poly_seq_in_lp[content_subtype]
                                    if _poly_seq_in_lp['sf_framecode'] == sf_framecode), None)

            if _poly_seq_in_lp is not None:
                list_id = _poly_seq_in_lp['list_id']
                poly_seq = _poly_seq_in_lp['polymer_sequence']

                seq_align, _ = alignPolymerSequence(self.__reg.pA, self.__reg.caC['polymer_sequence'], poly_seq, conservative=False)
                chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type, self.__reg.caC['polymer_sequence'],
                                                        poly_seq, seq_align)

                if self.__reg.caC['branched'] is not None:
                    br_seq_align, _ = alignPolymerSequence(self.__reg.pA, self.__reg.caC['branched'], poly_seq, conservative=False)
                    br_chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type, self.__reg.caC['branched'],
                                                               poly_seq, br_seq_align)

                if self.__reg.caC['non_polymer'] is not None:
                    np_seq_align, _ = alignPolymerSequence(self.__reg.pA, self.__reg.caC['non_polymer'], poly_seq, conservative=False)
                    np_chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type, self.__reg.caC['non_polymer'],
                                                               poly_seq, np_seq_align)

        @functools.lru_cache()
        def get_auth_seq_scheme(chain_id, seq_id):
            auth_asym_id = auth_seq_id = None

            if seq_id is not None:

                if chain_assign is not None:
                    auth_asym_id = next((ca['ref_chain_id'] for ca in chain_assign if ca['test_chain_id'] == chain_id), None)
                    if auth_asym_id is not None:
                        sa = next((sa for sa in seq_align
                                   if sa['ref_chain_id'] == auth_asym_id and sa['test_chain_id'] == chain_id and seq_id in sa['test_seq_id']
                                   and sa['sequence_coverage'] >= LOW_SEQ_COVERAGE), None)
                        if sa is not None:
                            _ref_seq_id_name = 'ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id'
                            auth_seq_id = next((ref_seq_id for ref_seq_id, test_seq_id in zip(sa[_ref_seq_id_name], sa['test_seq_id'])
                                                if test_seq_id == seq_id), None)

                if None in (auth_asym_id, auth_seq_id) and br_seq_align is not None:
                    auth_asym_id = next((ca['ref_chain_id'] for ca in br_chain_assign if ca['test_chain_id'] == chain_id), None)
                    if auth_asym_id is not None:
                        sa = next((sa for sa in br_seq_align
                                   if sa['ref_chain_id'] == auth_asym_id and sa['test_chain_id'] == chain_id and seq_id in sa['test_seq_id']
                                   and sa['sequence_coverage'] >= LOW_SEQ_COVERAGE), None)
                        if sa is not None:
                            _ref_seq_id_name = 'ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id'
                            auth_seq_id = next((ref_seq_id for ref_seq_id, test_seq_id in zip(sa[_ref_seq_id_name], sa['test_seq_id'])
                                                if test_seq_id == seq_id), None)

                if None in (auth_asym_id, auth_seq_id) and np_seq_align is not None:
                    auth_asym_id = next((ca['ref_chain_id'] for ca in np_chain_assign if ca['test_chain_id'] == chain_id), None)
                    if auth_asym_id is not None:
                        sa = next((sa for sa in np_seq_align
                                   if sa['ref_chain_id'] == auth_asym_id and sa['test_chain_id'] == chain_id and seq_id in sa['test_seq_id']
                                   and sa['sequence_coverage'] >= LOW_SEQ_COVERAGE), None)
                        if sa is not None:
                            _ref_seq_id_name = 'ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id'
                            auth_seq_id = next((ref_seq_id for ref_seq_id, test_seq_id in zip(sa[_ref_seq_id_name], sa['test_seq_id'])
                                                if test_seq_id == seq_id), None)

            return auth_asym_id, auth_seq_id

        @functools.lru_cache()
        def get_label_seq_scheme(chain_id, seq_id):
            auth_asym_id = auth_seq_id = label_seq_id = None

            if seq_id is not None:

                if chain_assign is not None:
                    auth_asym_id = next((ca['ref_chain_id'] for ca in chain_assign if ca['test_chain_id'] == chain_id), None)
                    if auth_asym_id is not None:
                        sa = next((sa for sa in seq_align
                                   if sa['ref_chain_id'] == auth_asym_id and sa['test_chain_id'] == chain_id
                                   and seq_id in sa['ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id']
                                   and sa['sequence_coverage'] >= LOW_SEQ_COVERAGE), None)
                        if sa is not None:
                            _ref_seq_id_name = 'ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id'
                            auth_seq_id, label_seq_id = next(((ref_seq_id, test_seq_id)
                                                              for ref_seq_id, test_seq_id
                                                              in zip(sa[_ref_seq_id_name], sa['test_seq_id'])
                                                              if ref_seq_id == seq_id), (None, None))

                if None in (auth_asym_id, auth_seq_id) and br_seq_align is not None:
                    auth_asym_id = next((ca['ref_chain_id'] for ca in br_chain_assign if ca['test_chain_id'] == chain_id), None)
                    if auth_asym_id is not None:
                        sa = next((sa for sa in br_seq_align
                                   if sa['ref_chain_id'] == auth_asym_id and sa['test_chain_id'] == chain_id
                                   and seq_id in sa['ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id']
                                   and sa['sequence_coverage'] >= LOW_SEQ_COVERAGE), None)
                        if sa is not None:
                            _ref_seq_id_name = 'ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id'
                            auth_seq_id, label_seq_id = next(((ref_seq_id, test_seq_id)
                                                              for ref_seq_id, test_seq_id
                                                              in zip(sa[_ref_seq_id_name], sa['test_seq_id'])
                                                              if ref_seq_id == seq_id), (None, None))

                if None in (auth_asym_id, auth_seq_id) and np_seq_align is not None:
                    auth_asym_id = next((ca['ref_chain_id'] for ca in np_chain_assign if ca['test_chain_id'] == chain_id), None)
                    if auth_asym_id is not None:
                        sa = next((sa for sa in np_seq_align
                                   if sa['ref_chain_id'] == auth_asym_id and sa['test_chain_id'] == chain_id
                                   and seq_id in sa['ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id']
                                   and sa['sequence_coverage'] >= LOW_SEQ_COVERAGE), None)
                        if sa is not None:
                            _ref_seq_id_name = 'ref_auth_seq_id' if 'ref_auth_seq_id' in sa else 'ref_seq_id'
                            auth_seq_id, label_seq_id = next(((ref_seq_id, test_seq_id)
                                                              for ref_seq_id, test_seq_id
                                                              in zip(sa[_ref_seq_id_name], sa['test_seq_id'])
                                                              if ref_seq_id == seq_id), (None, None))

            return auth_asym_id, auth_seq_id, label_seq_id

        has_ins_code = False

        if poly_seq is not None:

            for ps in poly_seq:

                if has_ins_code:
                    break

                auth_asym_id, _ = get_auth_seq_scheme(ps['chain_id'], ps['seq_id'][0])

                if self.__reg.caC['polymer_sequence'] is not None\
                   and any(True for cif_ps in self.__reg.caC['polymer_sequence']
                           if cif_ps['auth_chain_id'] == auth_asym_id and 'ins_code' in cif_ps):
                    has_ins_code = True

                if self.__reg.caC['branched'] is not None\
                   and any(True for cif_ps in self.__reg.caC['branched']
                           if cif_ps['auth_chain_id'] == auth_asym_id and 'ins_code' in cif_ps):
                    has_ins_code = True

                if self.__reg.caC['non_polymer'] is not None\
                   and any(True for cif_ps in self.__reg.caC['non_polymer']
                           if cif_ps['auth_chain_id'] == auth_asym_id and 'ins_code' in cif_ps):
                    has_ins_code = True

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        # cleanup unnecessary '?'
        item_names = [item['name'] for item in self.__reg.key_items[file_type][content_subtype]]
        item_names.extend([item['name'] for item in DATA_ITEMS[file_type][content_subtype]])
        first_row = loop.data[0]
        for item_name in set(loop.tags) - set(item_names):
            item_col = loop.tags.index(item_name)
            if first_row[item_col] == '?':
                for row in loop:
                    if row[item_col] == '?':
                        row[item_col] = None

        aux_lp = None

        aux_lp_category = AUX_LP_CATEGORIES[file_type][content_subtype][0] if file_type == 'nmr-star' else ''

        def delete_aux_loop():

            if file_type == 'nmr-star' and not isinstance(sf, pynmrstar.Loop):

                try:

                    aux_loop = sf.get_loop(aux_lp_category)

                    del sf[aux_loop]

                except KeyError:
                    pass

        if file_type == 'nef':

            items = ['chain_code', 'sequence_code', 'residue_name', 'atom_name', 'value', 'value_uncertainty', 'element', 'isotope_number']

            mandatory_items = [item['name'] for item in self.__reg.key_items[file_type][content_subtype]
                               if 'remove-bad-pattern' in item]

            if not all(tag in loop.tags for tag in mandatory_items):

                err = f"Assigned chemical shifts of {sf_framecode!r} saveframe was not parsed properly. Please fix problems reported."

                self.__reg.report.error.appendDescription('missing_mandatory_content',
                                                          {'file_name': file_name, 'description': err})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.remediateCsLoop() ++ Error  - {err}\n")

                return False

            mandatory_items = [item['name'] for item in self.__reg.key_items[file_type][content_subtype]]
            for item in DATA_ITEMS[file_type][content_subtype]:
                if item['mandatory']:
                    mandatory_items.append(item['name'])

            if not all(tag for tag in mandatory_items if tag in loop.tags):
                return False

            coord_atom_site = self.__reg.caC['coord_atom_site'] if self.__reg.caC is not None else {}

            chain_id_col = loop.tags.index('chain_code')
            seq_id_col = loop.tags.index('sequence_code')
            comp_id_col = loop.tags.index('residue_name')
            atom_id_col = loop.tags.index('atom_name')
            val_col = loop.tags.index('value')
            val_err_col = loop.tags.index('value_uncertainty') if 'value_uncertainty' in loop.tags else -1

            lp = pynmrstar.Loop.from_scratch(lp_category)

            tags = [lp_category + '.' + item for item in items]

            lp.add_tag(tags)

            for idx, row in enumerate(loop):

                _row = [None] * len(tags)

                try:
                    seq_key = (row[chain_id_col], int(row[seq_id_col]))
                except (ValueError, TypeError):
                    continue

                if seq_key in self.__reg.seq_id_map_for_remediation:
                    seq_key = self.__reg.seq_id_map_for_remediation[seq_key]

                _row[0], _row[1] = seq_key

                if seq_key in coord_atom_site:
                    _row[2] = coord_atom_site[seq_key]['comp_id']
                else:
                    _row[2] = row[comp_id_col].upper()

                _row[3] = row[atom_id_col]
                atom_id = row[atom_id_col].upper()

                _row[4] = row[val_col]

                try:
                    float(_row[4])
                except ValueError:
                    continue

                if val_err_col != -1:
                    val_err = row[val_err_col]
                    _row[5] = val_err

                    if val_err not in EMPTY_VALUE:
                        try:
                            _val_err = float(val_err)
                            if _val_err < 0.0:
                                _row[5] = abs(_val_err)
                        except ValueError:
                            pass

                _row[6] = 'H' if _row[3][0] in PROTON_BEGIN_CODE else atom_id[0]
                if _row[6] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                    _row[7] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[6]][0]

                lp.add_data(_row)

            key_items = self.__reg.key_items[file_type][content_subtype]

            conflict_id = self.__reg.nefT.get_conflict_id(lp, lp_category, key_items)[0]

            if len(conflict_id) > 0:
                conflict_id_set = self.__reg.nefT.get_conflict_id_set(lp, lp_category, key_items)[0]

                for _id in conflict_id:
                    _id_set = next(id_set for id_set in conflict_id_set if _id in id_set)

                    if len(set(str(lp.data[_id_]) for _id_ in _id_set)) == 1:
                        continue

                    msg = ' vs '.join([str(lp.data[_id_]).replace('None', '.').replace(',', '').replace("'", '') for _id_ in _id_set])

                    warn = f"Resolved redundancy of assigned chemical shifts ({msg}) by deletion of the latter one."

                    self.__reg.report.warning.appendDescription('redundant_data',
                                                                {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                 'category': lp_category, 'description': warn})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateCsLoop() ++ Warning  - {warn}\n")

                for _id in conflict_id:
                    del lp.data[_id]

        else:

            if 'original_file_name' in input_source_dic:
                tagNames = [t[0] for t in sf.tags]
                if 'Data_file_name' not in tagNames:
                    sf.add_tag('Data_file_name', input_source_dic['original_file_name'])

            items = ['ID', 'Entity_assembly_ID', 'Entity_ID', 'Comp_index_ID', 'Seq_ID',
                     'Comp_ID', 'Atom_ID', 'Atom_type', 'Atom_isotope_number',
                     'Val', 'Val_err', 'Assign_fig_of_merit', 'Ambiguity_code', 'Ambiguity_set_ID', 'Occupancy', 'Resonance_ID',
                     'Auth_asym_ID', 'Auth_seq_ID', 'Auth_comp_ID', 'Auth_atom_ID',
                     'Original_PDB_strand_ID', 'Original_PDB_residue_no', 'Original_PDB_residue_name', 'Original_PDB_atom_name',
                     'Details', 'Entry_ID', 'Assigned_chem_shift_list_ID']

            if has_ins_code:
                items.append('PDB_ins_code')

            mandatory_items = [item['name'] for item in self.__reg.key_items[file_type][content_subtype]
                               if 'remove-bad-pattern' in item]

            if not all(tag in loop.tags for tag in mandatory_items):

                err = f"Assigned chemical shifts of {sf_framecode!r} saveframe was not parsed properly. Please fix problems reported."

                self.__reg.report.error.appendDescription('missing_mandatory_content',
                                                          {'file_name': file_name, 'description': err})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.remediateCsLoop() ++ Error  - {err}\n")

                return False

            mandatory_items = [item['name'] for item in self.__reg.key_items[file_type][content_subtype]]
            for item in DATA_ITEMS[file_type][content_subtype]:
                if item['mandatory']:
                    mandatory_items.append(item['name'])

            if not all(tag for tag in mandatory_items if tag in loop.tags):
                return False

            auth_pdb_tags = ['Auth_asym_ID', 'Auth_seq_ID', 'Auth_comp_ID', 'Auth_atom_ID']
            orig_pdb_tags = ['Original_PDB_strand_ID', 'Original_PDB_residue_no', 'Original_PDB_residue_name', 'Original_PDB_atom_name']

            entity_assembly = self.__reg.caC['entity_assembly'] if self.__reg.caC is not None else []
            auth_to_entity_type = self.__reg.caC['auth_to_entity_type'] if self.__reg.caC is not None else {}
            auth_to_star_seq = self.__reg.caC['auth_to_star_seq'] if self.__reg.caC is not None else {}
            auth_to_orig_seq = self.__reg.caC['auth_to_orig_seq'] if self.__reg.caC is not None else {}
            auth_to_ins_code = self.__reg.caC['auth_to_ins_code'] if self.__reg.caC is not None else {}
            auth_to_star_seq_ann = self.__reg.caC['auth_to_star_seq_ann'] if self.__reg.caC is not None else {}
            coord_atom_site = self.__reg.caC['coord_atom_site'] if self.__reg.caC is not None else {}
            coord_unobs_res = self.__reg.caC['coord_unobs_res'] if self.__reg.caC is not None else {}
            auth_atom_name_to_id = self.__reg.caC['auth_atom_name_to_id'] if self.__reg.caC is not None else {}
            auth_atom_name_to_id_ext = self.__reg.caC['auth_atom_name_to_id_ext'] if self.__reg.caC is not None else {}
            mis_poly_link = self.__reg.caC['missing_polymer_linkage'] if self.__reg.caC is not None else []

            _auth_to_orig_seq = {}

            has_auth_seq = valid_auth_seq = has_auth_chain = False
            aux_auth_seq_id_col = aux_auth_comp_id_col = aux_auth_atom_id_col = -1
            auth_asym_id_col = loop.tags.index('Auth_asym_ID') if 'Auth_asym_ID' in loop.tags else -1
            auth_seq_id_col = loop.tags.index('Auth_seq_ID') if 'Auth_seq_ID' in loop.tags else -1
            auth_comp_id_col = loop.tags.index('Auth_comp_ID') if 'Auth_comp_ID' in loop.tags else -1
            auth_atom_id_col = loop.tags.index('Auth_atom_ID') if 'Auth_atom_ID' in loop.tags else -1

            # split concatenation of auth_seq_id and ins_code (DAOTHER-10418)
            if auth_to_ins_code is not None and len(auth_to_ins_code) > 0 and auth_seq_id_col != -1:
                auth_dat = loop.get_tag(['Auth_seq_ID'])

                if any(True for row in auth_dat if isinstance(row, str)):

                    ins_code_col = loop.tags.index('PDB_ins_code') if 'PDB_ins_code' in loop.tags else -1
                    if ins_code_col == -1:
                        loop.add_tag('PDB_ins_code', update_data=True)

                    for idx, row in enumerate(auth_dat):
                        if isinstance(row, str) and CONCAT_SEQ_ID_INS_CODE_PAT.match(row):
                            g = CONCAT_SEQ_ID_INS_CODE_PAT.search(row).groups()
                            loop.data[idx][auth_seq_id_col] = g[0]
                            if g[1] not in EMPTY_VALUE:
                                loop.data[idx][ins_code_col] = g[1]

                    if not has_ins_code:
                        items.append('PDB_ins_code')
                        has_ins_code = True

            valid_auth_seq_per_chain = []

            if set(auth_pdb_tags) & set(loop.tags) == set(auth_pdb_tags):
                auth_dat = loop.get_tag(auth_pdb_tags)
                if len(auth_dat) > 0:
                    has_auth_seq = valid_auth_seq = True
                    if not self.__reg.annotation_mode or len(coord_unobs_res) > 0:
                        for row in auth_dat:
                            try:
                                seq_key = (row[0], int(row[1]), row[2])
                                if seq_key not in auth_to_star_seq_ann:
                                    valid_auth_seq = False
                                    break
                            except (ValueError, TypeError):
                                has_auth_seq = valid_auth_seq = False
                                break

            # DAOTHER-9281
            elif auth_asym_id_col != -1:
                has_auth_chain = True
                _auth_pdb_tags = ['Auth_asym_ID']
                if 'Auth_seq_ID' in loop.tags:
                    _auth_pdb_tags.append('Auth_seq_ID')
                elif 'Comp_index_ID' in loop.tags:
                    _auth_pdb_tags.append('Comp_index_ID')
                elif 'Seq_ID' in loop.tags:
                    _auth_pdb_tags.append('Seq_ID')

                if 'Auth_comp_ID' in loop.tags:
                    _auth_pdb_tags.append('Auth_comp_ID')
                elif 'Comp_ID' in loop.tags:
                    _auth_pdb_tags.append('Comp_ID')

                if 'Auth_atom_ID' in loop.tags:
                    _auth_pdb_tags.append('Auth_atom_ID')
                elif 'Atom_ID' in loop.tags:
                    _auth_pdb_tags.append('Atom_ID')

                if len(_auth_pdb_tags) == 4:
                    auth_dat = loop.get_tag(_auth_pdb_tags)
                    if len(auth_dat) > 0:
                        aux_auth_seq_id_col = loop.tags.index(_auth_pdb_tags[1])
                        aux_auth_comp_id_col = loop.tags.index(_auth_pdb_tags[2])
                        aux_auth_atom_id_col = loop.tags.index(_auth_pdb_tags[3])

                        valid_auth_seq = True
                        if not self.__reg.annotation_mode or len(coord_unobs_res) > 0:
                            for row in auth_dat:
                                try:
                                    seq_key = (row[0], int(row[1]), row[2])
                                    if seq_key not in auth_to_star_seq_ann:
                                        valid_auth_seq = False
                                        break
                                except (ValueError, TypeError):
                                    valid_auth_seq = False
                                    break
                        if not valid_auth_seq:
                            for row in auth_dat:
                                if row[0] not in valid_auth_seq_per_chain:
                                    valid_auth_seq_per_chain.append(row[0])
                            if not self.__reg.annotation_mode or len(coord_unobs_res) > 0:
                                for row in auth_dat:
                                    try:
                                        seq_key = (row[0], int(row[1]), row[2])
                                        if seq_key not in auth_to_star_seq_ann:
                                            if row[0] in valid_auth_seq_per_chain:
                                                valid_auth_seq_per_chain.remove(row[0])
                                    except (ValueError, TypeError):
                                        if row[0] in valid_auth_seq_per_chain:
                                            valid_auth_seq_per_chain.remove(row[0])

            has_orig_seq = ch2_name_in_xplor = ch3_name_in_xplor = False

            if self.__reg.remediation_mode:
                if set(orig_pdb_tags) & set(loop.tags) == set(orig_pdb_tags):
                    orig_dat = loop.get_tag(orig_pdb_tags)
                    if len(orig_dat) > 0:
                        for row in orig_dat:
                            if all(d not in EMPTY_VALUE for d in row):
                                has_orig_seq = True
                                break
                        if has_orig_seq:
                            orig_pdb_tags.append('Comp_ID')
                            orig_pdb_tags.append('Atom_ID')
                            dat = loop.get_tag(orig_pdb_tags)
                            for row in dat:
                                if row[3] in EMPTY_VALUE:
                                    continue
                                orig_atom_id = row[3].upper()
                                comp_id = row[4]
                                atom_id = row[5]
                                if orig_atom_id == atom_id:
                                    continue
                                ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                                if ambig_code == 0 or atom_id[0] not in PROTON_BEGIN_CODE:
                                    continue
                                len_in_grp = len(self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id))
                                if len_in_grp == 2 and ambig_code == 2:
                                    ch2_name_in_xplor = any(True for r, o in zip(atom_id, orig_atom_id) if r == '3' and o == '1')
                                elif len_in_grp == 3 and atom_id[-1] == orig_atom_id[0]:
                                    ch3_name_in_xplor = True
            else:
                if set(orig_pdb_tags) & set(loop.tags) == set(orig_pdb_tags):
                    orig_dat = loop.get_tag(orig_pdb_tags)
                    if len(orig_dat) > 0:
                        for row in orig_dat:
                            if all(d not in EMPTY_VALUE for d in row):
                                has_orig_seq = True
                                break

            chain_id_col = loop.tags.index('Entity_assembly_ID')
            entity_id_col = loop.tags.index('Entity_ID') if 'Entity_ID' in loop.tags else -1
            seq_id_col = loop.tags.index('Comp_index_ID')
            comp_id_col = loop.tags.index('Comp_ID')
            atom_id_col = loop.tags.index('Atom_ID')
            val_col = loop.tags.index('Val') if 'Val' in loop.tags else loop.tags.index('Chem_shift_val')
            val_err_col = loop.tags.index('Val_err') if 'Val_err' in loop.tags\
                else loop.tags.index('Chem_shift_val_err') if 'Chem_shift_val_err' in loop.tags else -1
            fig_of_merit_col = loop.tags.index('Assign_fig_of_merit') if 'Assign_fig_of_merit' in loop.tags\
                else loop.tags.index('Chem_shift_assign_fig_of_merit') if 'Chem_shift_assign_fig_of_merit' in loop.tags else -1
            ambig_code_col = loop.tags.index('Ambiguity_code') if 'Ambiguity_code' in loop.tags\
                else loop.tags.index('Chem_shift_ambiguity_code') if 'Chem_shift_ambiguity_code' in loop.tags else -1
            ambig_set_id_col = loop.tags.index('Ambiguity_set_ID') if 'Ambiguity_set_ID' in loop.tags else -1
            occupancy_col = loop.tags.index('Occupancy') if 'Occupancy' in loop.tags else -1
            reson_id_col = loop.tags.index('Resonance_ID') if 'Resonance_ID' in loop.tags else -1
            details_col = loop.tags.index('Details') if 'Details' in loop.tags else -1

            if self.__reg.annotation_mode and details_col != -1:
                for row in loop:
                    if row[details_col] == 'UNMAPPED':
                        row[details_col] = None

            trial = 0

            incomplete_comp_id_annotation = []  # DAOTHER-9286
            truncated_loop_sequence = []  # DAOTHER-9644
            for mis in mis_poly_link:
                auth_chain_id = mis['auth_chain_id']
                auth_seq_id_1 = mis['auth_seq_id_1']
                auth_seq_id_2 = mis['auth_seq_id_2']

                cif_ps = next((cif_ps for cif_ps in self.__reg.caC['polymer_sequence'] if cif_ps['auth_chain_id'] == auth_chain_id), None)

                if cif_ps is not None and auth_seq_id_1 in cif_ps['auth_seq_id'] and auth_seq_id_2 in cif_ps['auth_seq_id']\
                   and auth_seq_id_1 < auth_seq_id_2:
                    for auth_seq_id in range(auth_seq_id_1 + 1, auth_seq_id_2):
                        _seq_key = (auth_chain_id, auth_seq_id)
                        truncated_loop_sequence.append(_seq_key)

            def fill_cs_row(lp, index, _row, prefer_auth_atom_name, coord_atom_site, _seq_key, comp_id, atom_id, src_lp, src_idx):
                reparse = False
                _src_idx = src_idx
                if src_idx > 0:
                    src_idx -= 1
                fill_auth_atom_id = self.__reg.annotation_mode or (_row[19] in EMPTY_VALUE and _row[18] not in EMPTY_VALUE)
                fill_orig_atom_id = _row[23] not in EMPTY_VALUE

                if _seq_key is not None:
                    if _seq_key in truncated_loop_sequence and _row[24] in EMPTY_VALUE:
                        _row[24] = 'UNMAPPED'
                    seq_key = (_seq_key[0], _seq_key[1], comp_id)
                    _seq_key = seq_key if seq_key in coord_atom_site else _seq_key
                if _seq_key in coord_atom_site\
                   and (coord_atom_site[_seq_key]['comp_id'] == comp_id
                        or (_seq_key not in coord_unobs_res and coord_atom_site[_seq_key]['comp_id'] not in STD_MON_DICT)
                        or (_seq_key in coord_unobs_res and coord_unobs_res[_seq_key]['comp_id'] != comp_id)):
                    # 8b9r: A:24:VAL (unobserved), A:24:CU
                    _coord_atom_site = coord_atom_site[_seq_key]
                    _atom_site_atom_id = _coord_atom_site['atom_id']
                    # DAOTHER-8817
                    if 'chain_id' in _coord_atom_site:
                        _row[16] = _coord_atom_site['chain_id']
                    _row[5] = _row[18] = comp_id = _coord_atom_site['comp_id']
                    valid = True
                    missing_ch3 = []
                    if not self.__reg.annotation_mode and atom_id in self.__reg.csStat.getMethylProtons(comp_id):
                        missing_ch3 = self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id, True)
                        valid = self.__reg.sail_flag
                        row_src = src_lp.data[src_idx]
                        if 0 <= src_idx < len(src_lp):
                            for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                if src_idx + offset < len(src_lp):
                                    row = src_lp.data[src_idx + offset]
                                    if (row[seq_id_col] == str(_row[3])
                                        or (_row[3] != row_src[3] and row[seq_id_col] == row_src[seq_id_col]))\
                                       and row[comp_id_col].upper() == comp_id\
                                       and row[atom_id_col] in missing_ch3:
                                        valid = True
                                        missing_ch3.remove(row[atom_id_col])
                                        if len(missing_ch3) == 0:
                                            break
                                if src_idx - offset >= 0:
                                    row = src_lp.data[src_idx - offset]
                                    if (row[seq_id_col] == str(_row[3])
                                        or (_row[3] != row_src[3] and row[seq_id_col] == row_src[seq_id_col]))\
                                       and row[comp_id_col].upper() == comp_id\
                                       and row[atom_id_col] in missing_ch3:
                                        valid = True
                                        missing_ch3.remove(row[atom_id_col])
                                        if len(missing_ch3) == 0:
                                            break
                    if atom_id in _atom_site_atom_id and valid and len(missing_ch3) == 0\
                       and (not self.__reg.annotation_mode or comp_id not in incomplete_comp_id_annotation):
                        _row[6] = atom_id
                        if fill_auth_atom_id or _row[6] != _row[19]:
                            _row[19] = _row[6]
                        _row[7] = _coord_atom_site['type_symbol'][_atom_site_atom_id.index(atom_id)]
                        if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                            _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                        # """ need to preserve Original_PDB_atom_name for atom name mapping history
                        # if fill_orig_atom_id and _row[6] != _row[23] and _row[23] in _atom_site_atom_id:
                        #     if _row[23] in self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id, True):
                        #         _row[23] = copy.copy(atom_id)
                        # """
                    else:
                        if atom_id in ('H1', 'HT1') and 'H' in _atom_site_atom_id\
                           and atom_id not in _atom_site_atom_id:
                            if self.__reg.ccU.updateChemCompDict(comp_id):
                                cca = next((cca for cca in self.__reg.ccU.lastAtomDictList
                                            if cca['atom_id'] == atom_id
                                            and cca['leaving_atom_flag'] == 'N'), None)
                                if cca is None:
                                    atom_id = 'H'
                                    if fill_auth_atom_id:
                                        _row[19] = atom_id
                            else:
                                atom_id = 'H'
                                if fill_auth_atom_id:
                                    _row[19] = atom_id
                        elif atom_id in ('H', 'HT1') and 'H1' in _atom_site_atom_id\
                                and atom_id not in _atom_site_atom_id:
                            if self.__reg.ccU.updateChemCompDict(comp_id):
                                cca = next((cca for cca in self.__reg.ccU.lastAtomDictList
                                            if cca['atom_id'] == atom_id
                                            and cca['leaving_atom_flag'] == 'N'), None)
                                if cca is None:
                                    atom_id = 'H1'
                                    if fill_auth_atom_id:
                                        _row[19] = atom_id
                            else:
                                atom_id = 'H1'
                                if fill_auth_atom_id:
                                    _row[19] = atom_id
                        elif atom_id in AMINO_PROTON_CODE and 'C' + atom_id[1:] in _atom_site_atom_id:
                            bonded = self.__reg.ccU.getBondedAtoms(comp_id, 'C' + atom_id[1:], onlyProton=True)
                            if len(bonded) == 1 and bonded[0] in _atom_site_atom_id:
                                atom_id = bonded[0]
                                if fill_auth_atom_id:
                                    _row[19] = atom_id
                        if len(missing_ch3) > 0 and (_row[9] in EMPTY_VALUE or float(_row[9]) >= 4.0):
                            heme = False
                            if _row[9] not in EMPTY_VALUE:
                                if self.__reg.ccU.updateChemCompDict(comp_id):
                                    heme = comp_id == 'HEM' or 'HEME' in self.__reg.ccU.lastChemCompDict['name']
                            if not heme:
                                missing_ch3 = []
                        _atom_id = atom_id
                        if not valid and len(missing_ch3) > 0 and atom_id not in _atom_site_atom_id:
                            atom_id = atom_id[:-1]
                            if _atom_id in self.__reg.csStat.getRepMethylProtons(comp_id):
                                atom_id = _atom_id
                        if (valid and atom_id in _atom_site_atom_id)\
                           or ((prefer_auth_atom_name or _row[24] == 'UNMAPPED') and atom_id[0] not in ('Q', 'M')):
                            atom_ids = [atom_id]
                            if self.__reg.annotation_mode and comp_id in incomplete_comp_id_annotation and trial > 0:  # DAOTHER-9286
                                atom_ids =\
                                    self.__reg.dpV.getAtomIdListInXplorForLigandRemap(comp_id,
                                                                                      _row[23] if fill_orig_atom_id else atom_id,
                                                                                      _coord_atom_site)
                        else:
                            atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id, atom_id)
                            if len(atom_ids) == 0 or atom_ids[0] not in _atom_site_atom_id:
                                atom_ids =\
                                    self.__reg.dpV.getAtomIdListInXplor(comp_id,
                                                                        translateToStdAtomName(atom_id, comp_id, _atom_site_atom_id,
                                                                                               ccU=self.__reg.ccU))
                                if len(atom_ids) == 1 and atom_ids[0] in _atom_site_atom_id and atom_id not in _atom_site_atom_id:
                                    atom_id = atom_ids[0]
                            if self.__reg.annotation_mode and (len(atom_ids) == 0 or atom_ids[0] not in _atom_site_atom_id):  # DAOTHER-9286
                                atom_ids = self.__reg.dpV.getAtomIdListInXplorForLigandRemap(comp_id, atom_id, _coord_atom_site)
                                if comp_id not in incomplete_comp_id_annotation:
                                    incomplete_comp_id_annotation.append(comp_id)
                        if valid and len(missing_ch3) > 0:
                            if not fill_orig_atom_id or not any(c in ('x', 'y', 'X', 'Y') for c in _row[23])\
                               and len(self.__reg.dpV.getAtomIdListInXplor(comp_id, _row[23])) > 1 and _row[24] != 'UNMAPPED':
                                atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id, _row[23])
                            else:
                                missing_ch3.clear()
                        if not valid and len(missing_ch3) > 0 and atom_id in _atom_site_atom_id:
                            atom_ids.extend(missing_ch3)
                        len_atom_ids = len(atom_ids)
                        if len_atom_ids == 0:
                            _row[6] = atom_id
                            if fill_auth_atom_id:
                                _row[19] = _row[6]
                            _row[7] = 'H' if atom_id[0] in PSE_PRO_BEGIN_CODE else atom_id[0]
                            if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                        else:
                            methyl_atoms = self.__reg.csStat.getMethylAtoms(comp_id)
                            atom_ids = sorted(atom_ids)
                            _row[6] = atom_ids[0]
                            _row[19] = None
                            fill_auth_atom_id = _row[18] not in EMPTY_VALUE
                            if self.__reg.ccU.updateChemCompDict(comp_id):
                                cca = next((cca for cca in self.__reg.ccU.lastAtomDictList if cca['atom_id'] == _row[6]), None)
                                if cca is not None:
                                    _row[7] = cca['type_symbol']
                                    if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                        _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                                else:
                                    _row[7] = 'H' if _row[6][0] in PROTON_BEGIN_CODE else atom_id[0]
                                    if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                        _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                            else:
                                _row[7] = 'H' if atom_id[0] in PSE_PRO_BEGIN_CODE else atom_id[0]
                                if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                    _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]

                            ambig_code = _row[12]
                            if ambig_code == 0:
                                _row[12] = None

                            elif ambig_code in (2, 3):
                                _ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, _row[6])
                                if _ambig_code not in (0, ambig_code):
                                    if _ambig_code != 1:
                                        _row[12] = _ambig_code
                                    else:
                                        _row[12] = ambig_code = 4
                                        if 0 <= _src_idx < len(src_lp):
                                            row_src = src_lp.data[_src_idx]
                                            chain_id_src = row_src[chain_id_col]
                                            seq_id_src = row_src[seq_id_col]
                                            atom_type = row_src[atom_id_col][0]
                                            val = float(row_src[val_col])
                                            sig = self.__reg.ccU.getBondSignature(comp_id, atom_id)
                                            for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                                if src_idx + offset < len(src_lp):
                                                    row = src_lp.data[src_idx + offset]
                                                    if row[chain_id_col] == chain_id_src\
                                                       and row[seq_id_col] == seq_id_src\
                                                       and row[comp_id_col] == comp_id\
                                                       and row[atom_id_col][0] == atom_type\
                                                       and abs(float(row[val_col]) - val) < 1.0\
                                                       and self.__reg.ccU.getBondSignature(comp_id, row[atom_id_col]) == sig:
                                                        src_lp.data[src_idx + offset][ambig_code_col] = '4'
                                                        reparse = True
                                                if src_idx - offset >= 0:
                                                    row = src_lp.data[src_idx - offset]
                                                    if row[chain_id_col] == chain_id_src\
                                                       and row[seq_id_col] == seq_id_src\
                                                       and row[comp_id_col] == comp_id\
                                                       and row[atom_id_col][0] == atom_type\
                                                       and abs(float(row[val_col]) - val) < 1.0\
                                                       and self.__reg.ccU.getBondSignature(comp_id, row[atom_id_col]) == sig:
                                                        src_lp.data[src_idx - offset][ambig_code_col] = '4'
                                                        reparse = True

                            elif ambig_code == 4:
                                if not self.__reg.annotation_mode and _row[24] != 'UNMAPPED':
                                    row_src = src_lp.data[_src_idx]
                                    chain_id_src = row_src[chain_id_col]
                                    atom_id_src = row_src[atom_id_col]
                                    atom_type = atom_id_src[0]
                                    ambig_code_src = row_src[ambig_code_col]
                                    atom_ids_in_group_src = self.__reg.ccU.getProtonsInSameGroup(comp_id, atom_id_src)\
                                        if atom_type in PROTON_BEGIN_CODE else []
                                    ambig_code_4_test = hetero_group_test = False
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if src_idx + offset < len(src_lp):
                                            row = src_lp.data[src_idx + offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    break
                                                _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                if _seq_id in (_row[3], _row[17]):
                                                    ambig_code_4_test = True
                                                    if row[atom_id_col] not in atom_ids_in_group_src:
                                                        hetero_group_test = True
                                                        break
                                        if src_idx - offset >= 0:
                                            row = src_lp.data[src_idx - offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    break
                                                _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                if _seq_id in (_row[3], _row[17]):
                                                    ambig_code_4_test = True
                                                    if row[atom_id_col] not in atom_ids_in_group_src:
                                                        hetero_group_test = True
                                                        break
                                    if not ambig_code_4_test:
                                        ambig_code_5_test = False
                                        for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                            if src_idx + offset < len(src_lp):
                                                row = src_lp.data[src_idx + offset]
                                                if row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and row[ambig_code_col] == str(_row[12])\
                                                   or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                    if not (row[chain_id_col] == str(_row[1])
                                                            or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                        break
                                                    _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                    if _seq_id in (_row[3], _row[17]):
                                                        break
                                                    _row[12] = ambig_code = 5
                                                    ambig_code_5_test = True
                                                    break
                                            if src_idx - offset >= 0:
                                                row = src_lp.data[src_idx - offset]
                                                if row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and row[ambig_code_col] == str(_row[12])\
                                                   or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                    if not (row[chain_id_col] == str(_row[1])
                                                            or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                        break
                                                    _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                    if _seq_id in (_row[3], _row[17]):
                                                        break
                                                    _row[12] = ambig_code = 5
                                                    ambig_code_5_test = True
                                                    break
                                        if not ambig_code_5_test:
                                            for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                                if src_idx + offset < len(src_lp):
                                                    row = src_lp.data[src_idx + offset]
                                                    if row[comp_id_col] == comp_id\
                                                       and row[atom_id_col][0] == atom_type\
                                                       and row[ambig_code_col] == str(_row[12])\
                                                       or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                        if not (row[chain_id_col] == str(_row[1])
                                                                or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                            _row[12] = ambig_code = 6
                                                            break
                                                if src_idx - offset >= 0:
                                                    row = src_lp.data[src_idx - offset]
                                                    if row[comp_id_col] == comp_id\
                                                       and row[atom_id_col][0] == atom_type\
                                                       and row[ambig_code_col] == str(_row[12])\
                                                       or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                        if not (row[chain_id_col] == str(_row[1])
                                                                or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                            _row[12] = ambig_code = 6
                                                            break
                                            if ambig_code == 4:
                                                _row[12] = ambig_code = 1
                                    elif not hetero_group_test:
                                        _row[12] = ambig_code = 1

                            elif ambig_code == 5:
                                if not self.__reg.annotation_mode and _row[24] != 'UNMAPPED':
                                    row_src = src_lp.data[_src_idx]
                                    chain_id_src = row_src[chain_id_col]
                                    atom_type = row_src[atom_id_col][0]
                                    ambig_code_src = row_src[ambig_code_col]
                                    ambig_code_5_test = False
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if src_idx + offset < len(src_lp):
                                            row = src_lp.data[src_idx + offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    break
                                                _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                if _seq_id in (_row[3], _row[17]):
                                                    break
                                                _row[12] = ambig_code = 5
                                                ambig_code_5_test = True
                                                break
                                        if src_idx - offset >= 0:
                                            row = src_lp.data[src_idx - offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    break
                                                _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                if _seq_id in (_row[3], _row[17]):
                                                    break
                                                _row[12] = ambig_code = 5
                                                ambig_code_5_test = True
                                                break
                                    if not ambig_code_5_test:
                                        for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                            if src_idx + offset < len(src_lp):
                                                row = src_lp.data[src_idx + offset]
                                                if row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and row[ambig_code_col] == str(_row[12])\
                                                   or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                    if not (row[chain_id_col] == str(_row[1])
                                                            or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                        _row[12] = ambig_code = 6
                                                        break
                                            if src_idx - offset >= 0:
                                                row = src_lp.data[src_idx - offset]
                                                if row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and row[ambig_code_col] == str(_row[12])\
                                                   or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                    if not (row[chain_id_col] == str(_row[1])
                                                            or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                        _row[12] = ambig_code = 6
                                                        break

                            elif ambig_code == 6:
                                if len([item for item in entity_assembly
                                        if item['entity_type'] not in ('non-polymer', 'water')]) == 1\
                                   and len(entity_assembly[0]['label_asym_id'].split(',')) == 1:
                                    _row[12] = ambig_code = 5

                            if ambig_code in (1, 2, 3):
                                if _row[13] is not None:
                                    _row[13] = None

                            if len_atom_ids > 1:
                                if _row[12] == 1 or _row[12] in EMPTY_VALUE:
                                    if _row[6] not in methyl_atoms\
                                       or (_row[6] in methyl_atoms
                                           and ((_row[7][0] == 'H' and len_atom_ids == 6)
                                                or (_row[7][0] == 'C' and len_atom_ids == 2))):
                                        _row[12] = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, _row[6], None)
                                __row = copy.copy(_row)
                                if fill_auth_atom_id:
                                    __row[19] = __row[6]

                                lp.add_data(__row)

                                for _atom_id in atom_ids[1:]:
                                    __row = copy.copy(_row)

                                    index += 1

                                    __row[0] = index
                                    __row[6] = _atom_id
                                    if fill_auth_atom_id:
                                        __row[19] = __row[6]
                                    if fill_orig_atom_id and len(missing_ch3) > 0 and __row[23] in EMPTY_VALUE:
                                        if _atom_id in methyl_atoms:
                                            if ch3_name_in_xplor and _atom_id[0] in PROTON_BEGIN_CODE:
                                                __row[23] = __row[6][-1] + __row[6][:-1]
                                            else:
                                                __row[23] = copy.copy(__row[6])

                                    lp.add_data(__row)

                                index += 1

                                _row[6] = atom_ids[-1]

                            if fill_auth_atom_id:
                                _row[19] = _row[6]
                            if fill_orig_atom_id and len(missing_ch3) > 0 and _row[23] in EMPTY_VALUE:
                                if _row[6] in methyl_atoms:
                                    if ch3_name_in_xplor and _row[6][0] in PROTON_BEGIN_CODE:
                                        _row[23] = _row[6][-1] + _row[6][:-1]
                                    else:
                                        _row[23] = copy.copy(_row[6])

                else:
                    _row[5] = comp_id
                    valid = True
                    missing_ch3 = []
                    if atom_id in self.__reg.csStat.getMethylProtons(comp_id):
                        missing_ch3 = self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id, True)
                        valid = self.__reg.sail_flag
                        if 0 <= src_idx < len(src_lp):
                            row_src = src_lp.data[src_idx]
                            for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                if src_idx + offset < len(src_lp):
                                    row = src_lp.data[src_idx + offset]
                                    if (row[seq_id_col] == str(_row[3])
                                        or (_row[3] != row_src[3] and row[seq_id_col] == row_src[seq_id_col])
                                        or (_row[24] == 'UNMAPPED' and row[seq_id_col] == str(_row[17])))\
                                       and row[comp_id_col].upper() == comp_id\
                                       and row[atom_id_col] in missing_ch3:
                                        valid = True
                                        missing_ch3.remove(row[atom_id_col])
                                        if len(missing_ch3) == 0:
                                            break
                                if src_idx - offset >= 0:
                                    row = src_lp.data[src_idx - offset]
                                    if (row[seq_id_col] == str(_row[3])
                                        or (_row[3] != row_src[3] and row[seq_id_col] == row_src[seq_id_col])
                                        or (_row[24] == 'UNMAPPED' and row[seq_id_col] == str(_row[17])))\
                                       and row[comp_id_col].upper() == comp_id\
                                       and row[atom_id_col] in missing_ch3:
                                        valid = True
                                        missing_ch3.remove(row[atom_id_col])
                                        if len(missing_ch3) == 0:
                                            break
                    if len(missing_ch3) > 0 and (_row[9] in EMPTY_VALUE or float(_row[9]) >= 4.0):
                        heme = False
                        if _row[9] not in EMPTY_VALUE:
                            if self.__reg.ccU.updateChemCompDict(comp_id):
                                heme = comp_id == 'HEM' or 'HEME' in self.__reg.ccU.lastChemCompDict['name']
                        if not heme:
                            missing_ch3 = []
                    _atom_id = atom_id
                    if not valid and len(missing_ch3) > 0:
                        atom_id = atom_id[:-1]
                        if _atom_id in self.__reg.csStat.getRepMethylProtons(comp_id):
                            atom_id = _atom_id
                    if (valid or prefer_auth_atom_name or _row[24] == 'UNMAPPED') and atom_id[0] not in ('Q', 'M'):
                        atom_ids = [atom_id]
                    else:
                        atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id, atom_id)
                        if len(atom_ids) == 0:
                            atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id,
                                                                           translateToStdAtomName(atom_id, comp_id,
                                                                                                  ccU=self.__reg.ccU))
                    if valid and len(missing_ch3) > 0:
                        if not fill_orig_atom_id or not any(c in ('x', 'y', 'X', 'Y') for c in _row[23])\
                           and len(self.__reg.dpV.getAtomIdListInXplor(comp_id, _row[23])) > 1 and _row[24] != 'UNMAPPED':
                            atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id, _row[23])
                        else:
                            missing_ch3.clear()
                    if not valid and len(missing_ch3) > 0:
                        atom_ids.extend(missing_ch3)
                    len_atom_ids = len(atom_ids)
                    if len_atom_ids == 0:
                        _row[6] = atom_id
                        if fill_auth_atom_id or _row[6] != _row[19]:
                            _row[19] = _row[6]
                        _row[7] = 'H' if atom_id[0] in PSE_PRO_BEGIN_CODE else atom_id[0]
                        if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                            _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                    else:
                        methyl_atoms = self.__reg.csStat.getMethylAtoms(comp_id)
                        atom_ids = sorted(atom_ids)
                        _row[6] = atom_ids[0]
                        _row[19] = None
                        fill_auth_atom_id = _row[18] not in EMPTY_VALUE
                        if self.__reg.ccU.updateChemCompDict(comp_id):
                            cca = next((cca for cca in self.__reg.ccU.lastAtomDictList if cca['atom_id'] == _row[6]), None)
                            if cca is not None:
                                _row[7] = cca['type_symbol']
                                if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                    _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                            else:
                                _row[7] = 'H' if _row[6][0] in PROTON_BEGIN_CODE else atom_id[0]
                                if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                    _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                        else:
                            _row[7] = 'H' if atom_id[0] in PSE_PRO_BEGIN_CODE else atom_id[0]
                            if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]

                        ambig_code = _row[12]
                        if ambig_code == 0:
                            _row[12] = None

                        elif ambig_code in (2, 3):
                            _ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, _row[6])
                            if _ambig_code not in (0, ambig_code):
                                if _ambig_code != 1:
                                    _row[12] = _ambig_code
                                else:
                                    _row[12] = ambig_code = 4
                                    if 0 <= _src_idx < len(src_lp):
                                        row_src = src_lp.data[_src_idx]
                                        chain_id_src = row_src[chain_id_col]
                                        seq_id_src = row_src[seq_id_col]
                                        atom_type = row_src[atom_id_col][0]
                                        val = float(row_src[val_col])
                                        sig = self.__reg.ccU.getBondSignature(comp_id, atom_id)
                                        for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                            if src_idx + offset < len(src_lp):
                                                row = src_lp.data[src_idx + offset]
                                                if row[chain_id_col] == chain_id_src\
                                                   and row[seq_id_col] == seq_id_src\
                                                   and row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and abs(float(row[val_col]) - val) < 1.0\
                                                   and self.__reg.ccU.getBondSignature(comp_id, row[atom_id_col]) == sig:
                                                    src_lp.data[src_idx + offset][ambig_code_col] = '4'
                                                    reparse = True
                                            if src_idx - offset >= 0:
                                                row = src_lp.data[src_idx - offset]
                                                if row[chain_id_col] == chain_id_src\
                                                   and row[seq_id_col] == seq_id_src\
                                                   and row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and abs(float(row[val_col]) - val) < 1.0\
                                                   and self.__reg.ccU.getBondSignature(comp_id, row[atom_id_col]) == sig:
                                                    src_lp.data[src_idx - offset][ambig_code_col] = '4'
                                                    reparse = True

                        elif ambig_code == 4:
                            if not self.__reg.annotation_mode and _row[24] != 'UNMAPPED':
                                row_src = src_lp.data[_src_idx]
                                chain_id_src = row_src[chain_id_col]
                                atom_id_src = row_src[atom_id_col]
                                atom_type = atom_id_src[0]
                                ambig_code_src = row_src[ambig_code_col]
                                atom_ids_in_group = self.__reg.ccU.getProtonsInSameGroup(comp_id, atom_id_src)\
                                    if atom_type in PROTON_BEGIN_CODE else []
                                ambig_code_4_test = hetero_group_test = False
                                for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                    if src_idx + offset < len(src_lp):
                                        row = src_lp.data[src_idx + offset]
                                        if row[comp_id_col] == comp_id\
                                           and row[atom_id_col][0] == atom_type\
                                           and row[ambig_code_col] == str(_row[12])\
                                           or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                            if not (row[chain_id_col] == str(_row[1])
                                                    or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                break
                                            _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                            if _seq_id in (_row[3], _row[17]):
                                                ambig_code_4_test = True
                                                if row[atom_id_col] not in atom_ids_in_group:
                                                    hetero_group_test = True
                                                    break
                                    if src_idx - offset >= 0:
                                        row = src_lp.data[src_idx - offset]
                                        if row[comp_id_col] == comp_id\
                                           and row[atom_id_col][0] == atom_type\
                                           and row[ambig_code_col] == str(_row[12])\
                                           or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                            if not (row[chain_id_col] == str(_row[1])
                                                    or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                break
                                            _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                            if _seq_id in (_row[3], _row[17]):
                                                ambig_code_4_test = True
                                                if row[atom_id_col] not in atom_ids_in_group:
                                                    hetero_group_test = True
                                                    break
                                if not ambig_code_4_test:
                                    ambig_code_5_test = False
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if src_idx + offset < len(src_lp):
                                            row = src_lp.data[src_idx + offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    break
                                                _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                if _seq_id in (_row[3], _row[17]):
                                                    break
                                                _row[12] = ambig_code = 5
                                                ambig_code_5_test = True
                                                break
                                        if src_idx - offset >= 0:
                                            row = src_lp.data[src_idx - offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    break
                                                _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                                if _seq_id in (_row[3], _row[17]):
                                                    break
                                                _row[12] = ambig_code = 5
                                                ambig_code_5_test = True
                                                break
                                    if not ambig_code_5_test:
                                        for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                            if src_idx + offset < len(src_lp):
                                                row = src_lp.data[src_idx + offset]
                                                if row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and row[ambig_code_col] == str(_row[12])\
                                                   or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                    if not (row[chain_id_col] == str(_row[1])
                                                            or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                        _row[12] = ambig_code = 6
                                                        break
                                            if src_idx - offset >= 0:
                                                row = src_lp.data[src_idx - offset]
                                                if row[comp_id_col] == comp_id\
                                                   and row[atom_id_col][0] == atom_type\
                                                   and row[ambig_code_col] == str(_row[12])\
                                                   or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                    if not (row[chain_id_col] == str(_row[1])
                                                            or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                        _row[12] = ambig_code = 6
                                                        break
                                        if ambig_code == 4:
                                            _row[12] = ambig_code = 1
                                elif not hetero_group_test:
                                    _row[12] = ambig_code = 1

                        elif ambig_code == 5:
                            if not self.__reg.annotation_mode and _row[24] != 'UNMAPPED':
                                row_src = src_lp.data[_src_idx]
                                chain_id_src = row_src[chain_id_col]
                                atom_type = row_src[atom_id_col][0]
                                ambig_code_src = row_src[ambig_code_col]
                                ambig_code_5_test = False
                                for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                    if src_idx + offset < len(src_lp):
                                        row = src_lp.data[src_idx + offset]
                                        if row[comp_id_col] == comp_id\
                                           and row[atom_id_col][0] == atom_type\
                                           and row[ambig_code_col] == str(_row[12])\
                                           or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                            if not (row[chain_id_col] == str(_row[1])
                                                    or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                break
                                            _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                            if _seq_id in (_row[3], _row[17]):
                                                break
                                            _row[12] = ambig_code = 5
                                            ambig_code_5_test = True
                                            break
                                    if src_idx - offset >= 0:
                                        row = src_lp.data[src_idx - offset]
                                        if row[comp_id_col] == comp_id\
                                           and row[atom_id_col][0] == atom_type\
                                           and row[ambig_code_col] == str(_row[12])\
                                           or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                            if not (row[chain_id_col] == str(_row[1])
                                                    or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                break
                                            _seq_id = row[seq_id_col] if isinstance(row[seq_id_col], int) else int(row[seq_id_col])
                                            if _seq_id in (_row[3], _row[17]):
                                                break
                                            _row[12] = ambig_code = 5
                                            ambig_code_5_test = True
                                            break
                                if not ambig_code_5_test:
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if src_idx + offset < len(src_lp):
                                            row = src_lp.data[src_idx + offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    _row[12] = ambig_code = 6
                                                    break
                                        if src_idx - offset >= 0:
                                            row = src_lp.data[src_idx - offset]
                                            if row[comp_id_col] == comp_id\
                                               and row[atom_id_col][0] == atom_type\
                                               and row[ambig_code_col] == str(_row[12])\
                                               or (_row[12] != row_src[12] and row[ambig_code_col] == ambig_code_src):
                                                if not (row[chain_id_col] == str(_row[1])
                                                        or (_row[1] != row_src[1] and row[chain_id_col] == chain_id_src)):
                                                    _row[12] = ambig_code = 6
                                                    break

                        elif ambig_code == 6:
                            if len([item for item in entity_assembly
                                    if item['entity_type'] not in ('non-polymer', 'water')]) == 1\
                               and len(entity_assembly[0]['label_asym_id'].split(',')) == 1:
                                _row[12] = ambig_code = 5

                        if ambig_code in (1, 2, 3):
                            if _row[13] is not None:
                                _row[13] = None

                        if len_atom_ids > 1:
                            if _row[12] == 1 or _row[12] in EMPTY_VALUE:
                                if _row[6] not in methyl_atoms\
                                   or (_row[6] in methyl_atoms
                                       and ((_row[7][0] == 'H' and len_atom_ids == 6)
                                            or (_row[7][0] == 'C' and len_atom_ids == 2))):
                                    _row[12] = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, _row[6], None)
                            __row = copy.copy(_row)
                            if fill_auth_atom_id:
                                __row[19] = __row[6]
                            lp.add_data(__row)

                            for _atom_id in atom_ids[1:]:
                                __row = copy.copy(_row)

                                index += 1

                                __row[0] = index
                                __row[6] = _atom_id
                                if fill_auth_atom_id:
                                    __row[19] = __row[6]
                                if fill_orig_atom_id and len(missing_ch3) > 0\
                                   and __row[23] in EMPTY_VALUE:
                                    if _atom_id in methyl_atoms:
                                        if ch3_name_in_xplor and _atom_id[0] in PROTON_BEGIN_CODE:
                                            __row[23] = __row[6][-1] + __row[6][:-1]
                                        else:
                                            __row[23] = copy.copy(__row[6])

                                lp.add_data(__row)

                            index += 1

                            _row[6] = atom_ids[-1]

                        if fill_auth_atom_id:
                            _row[19] = _row[6]
                        if fill_orig_atom_id and len(missing_ch3) > 0\
                           and _row[23] in EMPTY_VALUE:
                            if _row[6] in methyl_atoms:
                                if ch3_name_in_xplor and _row[6][0] in PROTON_BEGIN_CODE:
                                    _row[23] = _row[6][-1] + _row[6][:-1]
                                else:
                                    _row[23] = copy.copy(_row[6])

                return index, _row, reparse

            copied_auth_chain_ids = set()
            copied_chain_ids = set()

            if has_auth_seq:
                auth_asym_ids = [row[0] for row in auth_dat]

                common_auth_asym_ids = collections.Counter(auth_asym_ids).most_common()

                if len(common_auth_asym_ids) > 1:
                    auth_cs_tags = ['Auth_asym_ID', 'Auth_seq_ID', 'Auth_comp_ID', 'Auth_atom_ID', 'Val']

                    _common_auth_asym_ids = dict(common_auth_asym_ids)

                    for _auth_chain_id_1, _auth_chain_id_2 in itertools.combinations(_common_auth_asym_ids.keys(), 2):

                        if _common_auth_asym_ids[_auth_chain_id_1] != _common_auth_asym_ids[_auth_chain_id_2]:
                            continue

                        try:
                            _auth_seq_id_1 = next(int(row[1]) for row in auth_dat if row[0] == _auth_chain_id_1)
                            _auth_seq_id_2 = next(int(row[1]) for row in auth_dat if row[0] == _auth_chain_id_2)
                        except (ValueError, TypeError):
                            continue

                        _seq_key_1 = (_auth_chain_id_1, _auth_seq_id_1, row[2])
                        _seq_key_2 = (_auth_chain_id_2, _auth_seq_id_2, row[2])

                        if _seq_key_1 not in auth_to_entity_type or _seq_key_2 not in auth_to_entity_type:
                            continue

                        if auth_to_entity_type[_seq_key_1] != auth_to_entity_type[_seq_key_2]\
                           or auth_to_entity_type[_seq_key_1] in ('non-polymer', 'water'):
                            continue

                        _auth_cs_1 = [row[1:] for row in loop.get_tag(auth_cs_tags) if row[0] == _auth_chain_id_1]
                        _auth_cs_2 = [row[1:] for row in loop.get_tag(auth_cs_tags) if row[0] == _auth_chain_id_2]

                        _auth_cs_1 = sorted(_auth_cs_1, key=itemgetter(0, 2))
                        _auth_cs_2 = sorted(_auth_cs_2, key=itemgetter(0, 2))

                        if _auth_cs_1 == _auth_cs_2:
                            copied_auth_chain_ids.add(_auth_chain_id_2)

            else:

                tags = ['Entity_assembly_ID', 'Comp_index_ID', 'Comp_ID', 'Atom_ID']
                dat = loop.get_tag(tags)

                chain_ids = [row[0] for row in dat]

                common_chain_ids = collections.Counter(chain_ids).most_common()

                if len(common_chain_ids) > 1:
                    cs_tags = ['Entity_assembly_ID', 'Comp_index_ID', 'Comp_ID', 'Atom_ID', 'Val']

                    _common_chain_ids = dict(common_chain_ids)

                    for _chain_id_1, _chain_id_2 in itertools.combinations(_common_chain_ids, 2):

                        if _common_chain_ids[_chain_id_1] != _common_chain_ids[_chain_id_2]:
                            continue

                        _cs_1 = [row[1:] for row in loop.get_tag(cs_tags) if row[0] == _chain_id_1]
                        _cs_2 = [row[1:] for row in loop.get_tag(cs_tags) if row[0] == _chain_id_2]

                        _cs_1 = sorted(_cs_1, key=itemgetter(0, 2))
                        _cs_2 = sorted(_cs_2, key=itemgetter(0, 2))

                        if _cs_1 == _cs_2:
                            copied_chain_ids.add(_chain_id_2)

            if has_orig_seq:
                orig_asym_id_col = loop.tags.index('Original_PDB_strand_ID')
                orig_seq_id_col = loop.tags.index('Original_PDB_residue_no')
                orig_comp_id_col = loop.tags.index('Original_PDB_residue_name')
                orig_atom_id_col = loop.tags.index('Original_PDB_atom_name')

            lp = pynmrstar.Loop.from_scratch(lp_category)

            tags = [lp_category + '.' + item for item in items]

            lp.add_tag(tags)

            prefer_auth_atom_name = False

            if (self.__reg.annotation_mode or self.__reg.native_combined) and len(auth_atom_name_to_id) > 0:

                count_auth_name = count_auth_id = 0

                for row in loop:

                    auth_asym_id = row[auth_asym_id_col]
                    auth_seq_id = row[auth_seq_id_col]
                    auth_comp_id = row[auth_comp_id_col]
                    auth_atom_id = row[auth_atom_id_col]

                    if not auth_seq_id.isdigit():
                        continue

                    auth_seq_id_ = int(auth_seq_id)
                    seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                    try:
                        auth_to_star_seq[seq_key]  # pylint: disable=pointless-statement
                    except KeyError:
                        auth_asym_id = next((_auth_asym_id for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                             if _auth_seq_id == auth_seq_id_ and _auth_comp_id == auth_comp_id), auth_asym_id)
                        if (auth_asym_id, auth_seq_id_, auth_comp_id) not in auth_to_star_seq:
                            auth_comp_id = next((_auth_comp_id for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                 if _auth_asym_id == auth_asym_id and _auth_seq_id == auth_seq_id_), auth_comp_id)

                    if auth_comp_id in auth_atom_name_to_id:
                        if auth_atom_id in auth_atom_name_to_id[auth_comp_id]:
                            count_auth_name += 1
                        if auth_atom_id in auth_atom_name_to_id[auth_comp_id].values():
                            count_auth_id += 1

                if count_auth_name + count_auth_id == 0:

                    for row in loop:

                        auth_asym_id = row[auth_asym_id_col]
                        auth_seq_id = row[auth_seq_id_col]
                        auth_comp_id = row[auth_comp_id_col]
                        auth_atom_id = row[auth_atom_id_col]

                        if not auth_seq_id.isdigit():
                            continue

                        auth_seq_id_ = int(auth_seq_id)
                        seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                        try:
                            auth_to_star_seq_ann[seq_key]  # pylint: disable=pointless-statement
                            _seq_key = seq_key if seq_key in coord_atom_site else (seq_key[0], seq_key[1])
                            if _seq_key in coord_atom_site:  # DAOTHER-8817
                                auth_comp_id = coord_atom_site[_seq_key]['comp_id']
                        except KeyError:
                            continue

                        if auth_comp_id in auth_atom_name_to_id:
                            if auth_atom_id in auth_atom_name_to_id[auth_comp_id]:
                                count_auth_name += 1
                            if auth_atom_id in auth_atom_name_to_id[auth_comp_id].values():
                                count_auth_id += 1

                prefer_auth_atom_name = count_auth_name > count_auth_id

            has_genuine_ambig_code = False

            can_auth_asym_id_mapping = {}  # DAOTHER-8751
            seq_id_offset_for_unmapped = {}  # DAOTHER-9065
            label_seq_id_offset_for_extended = {}  # D_1300044764

            while True:

                reparse_request = can_auth_asym_id_mapping_failed = False  # DAOTHER-9065, DAOTHER-9158

                lp.clear_data()

                index = 1

                for idx, row in enumerate(loop):

                    _row = [None] * len(tags)

                    comp_id = _orig_comp_id = row[comp_id_col].upper()
                    _orig_atom_id = row[atom_id_col]
                    atom_id = _orig_atom_id.upper()

                    _row[9] = row[val_col]

                    try:
                        float(_row[9])
                    except ValueError:
                        continue

                    if val_err_col != -1:
                        val_err = row[val_err_col]
                        _row[10] = val_err

                        if val_err not in EMPTY_VALUE:
                            try:
                                _val_err = float(val_err)
                                if _val_err < 0.0:
                                    _row[10] = abs(_val_err)
                            except ValueError:
                                pass

                    if fig_of_merit_col != -1:
                        _row[11] = row[fig_of_merit_col]

                    if ambig_code_col != -1:
                        ambig_code = row[ambig_code_col]
                        if ambig_code not in EMPTY_VALUE:
                            try:
                                ambig_code = int(ambig_code) if isinstance(ambig_code, str) else ambig_code
                                if ambig_code in ALLOWED_AMBIGUITY_CODES:
                                    _row[12] = ambig_code
                                else:
                                    _row[12] = None
                            except ValueError:
                                _row[12] = None

                    if ambig_set_id_col != -1:
                        ambig_set_id = row[ambig_set_id_col]
                        if ambig_set_id not in EMPTY_VALUE:
                            try:
                                ambig_set_id = int(ambig_set_id)
                                if ambig_set_id > 0:
                                    _row[13] = ambig_set_id
                            except ValueError:
                                _row[13] = None

                    if occupancy_col != -1:
                        try:
                            occupancy = row[occupancy_col]
                        except IndexError:
                            occupancy = '.'
                        if occupancy not in EMPTY_VALUE:
                            try:
                                occupancy = float(occupancy)
                                if occupancy >= 0.0:
                                    _row[14] = occupancy
                            except ValueError:
                                pass

                    if reson_id_col != -1:
                        reson_id = row[reson_id_col]
                        if reson_id not in EMPTY_VALUE:
                            try:
                                reson_id = int(reson_id)
                                if reson_id > 0:
                                    _row[15] = reson_id
                            except ValueError:
                                pass

                    if has_auth_seq:

                        if row[auth_asym_id_col] in copied_auth_chain_ids:
                            continue

                        _row[16], _row[17], _row[18], _row[19] =\
                            row[auth_asym_id_col], row[auth_seq_id_col], \
                            row[auth_comp_id_col], row[auth_atom_id_col]

                    if has_orig_seq:
                        _row[20], _row[21], _row[22], _row[23] =\
                            row[orig_asym_id_col], row[orig_seq_id_col], \
                            row[orig_comp_id_col], row[orig_atom_id_col]

                    if details_col != -1:
                        _row[24] = row[details_col]

                    _row[25], _row[26] = self.__reg.entry_id, list_id

                    resolved = True

                    if has_auth_seq and len(auth_to_star_seq) > 0:
                        auth_asym_id = row[auth_asym_id_col]
                        auth_seq_id = row[auth_seq_id_col]
                        auth_comp_id = row[auth_comp_id_col]

                        if valid_auth_seq:
                            auth_seq_id_ = int(auth_seq_id)
                            seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                            _seq_key = (seq_key[0], seq_key[1])
                            try:
                                entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                if atom_id != _row[19]:
                                    if _seq_key in coord_atom_site:
                                        _coord_atom_site = coord_atom_site[_seq_key]
                                        if atom_id in _coord_atom_site['atom_id']:
                                            _row[19] = atom_id
                            except KeyError:
                                if self.__reg.annotation_mode or self.__reg.native_combined:
                                    auth_asym_id = next((_auth_asym_id for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                         if _auth_seq_id == auth_seq_id_ and _auth_comp_id == auth_comp_id), auth_asym_id)
                                    seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                                    if seq_key in auth_to_star_seq:
                                        _row[16] = row[auth_asym_id_col] = auth_asym_id
                                        _row[20] = row[orig_asym_id_col] = auth_asym_id
                                        _seq_key = (seq_key[0], seq_key[1])
                                        entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                    else:
                                        auth_asym_id, auth_comp_id =\
                                            next(((_auth_asym_id, _auth_comp_id)
                                                  for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                  if _auth_seq_id == auth_seq_id_), (auth_asym_id, auth_comp_id))
                                        seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                                        if seq_key in auth_to_star_seq:
                                            _row[16] = row[auth_asym_id_col] = auth_asym_id
                                            _row[20] = row[orig_asym_id_col] = auth_asym_id
                                            _row[5] = row[comp_id_col] = auth_comp_id
                                            _row[18] = row[auth_comp_id_col] = auth_comp_id
                                            comp_id = auth_comp_id
                                            _seq_key = (seq_key[0], seq_key[1])
                                            entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                if seq_key not in auth_to_star_seq:
                                    auth_comp_id = next((_auth_comp_id for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                         if _auth_asym_id == auth_asym_id and _auth_seq_id == auth_seq_id_), auth_comp_id)
                                    comp_id = _row[18] = auth_comp_id
                                    seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                                    if seq_key in auth_to_star_seq:
                                        entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                    elif seq_key in auth_to_star_seq_ann:
                                        entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq_ann[seq_key]

                            self.__reg.ent_asym_id_with_exptl_data.add(entity_assembly_id)
                            _row[1], _row[2] = entity_assembly_id, entity_id
                            _row[3] = _row[4] = seq_id

                            if prefer_auth_atom_name:
                                if has_orig_seq:
                                    orig_atom_id = _row[23]
                                _atom_id = atom_id
                                _seq_key = seq_key if seq_key in coord_atom_site else (seq_key[0], seq_key[1])
                                if _seq_key in coord_atom_site:
                                    _coord_atom_site = coord_atom_site[_seq_key]
                                    if comp_id in auth_atom_name_to_id and comp_id == _coord_atom_site['comp_id']:
                                        if _atom_id in auth_atom_name_to_id[comp_id]:
                                            if auth_atom_name_to_id[comp_id][_atom_id] in _coord_atom_site['atom_id']:
                                                _row[19] = atom_id = auth_atom_name_to_id[comp_id][_atom_id]
                                            elif 'split_comp_id' not in _coord_atom_site and has_orig_seq\
                                                    and orig_atom_id in auth_atom_name_to_id[comp_id]:
                                                _row[19] = atom_id = auth_atom_name_to_id[comp_id][orig_atom_id]
                                    if 'alt_atom_id' in _coord_atom_site and _atom_id in _coord_atom_site['alt_atom_id']\
                                       and comp_id == _coord_atom_site['comp_id']:
                                        _row[19] = atom_id = _coord_atom_site['atom_id'][_coord_atom_site['alt_atom_id'].index(_atom_id)]
                                    # DAOTHER-8751, 8817 (D_1300043061)
                                    elif 'alt_comp_id' in _coord_atom_site and 'alt_atom_id' in _coord_atom_site\
                                         and _atom_id in _coord_atom_site['alt_atom_id']\
                                         and comp_id == _coord_atom_site['alt_comp_id'][_coord_atom_site['alt_atom_id'].index(_atom_id)]:
                                        _row[18] = comp_id
                                        # Entity_assembly_ID, Entity_ID, Comp_index_ID, Seq_ID, Comp_ID, Auth_asym_ID, Auth_seq_ID
                                        cca_row = next((cca_row for cca_row in self.__reg.chem_comp_asm_dat
                                                        if cca_row[4] == comp_id and cca_row[5] == _seq_key[0]
                                                        and cca_row[6] == _seq_key[1]), None)
                                        if cca_row is not None:
                                            _row[1], _row[2], _row[3], _row[4] = cca_row[0], cca_row[1], cca_row[2], cca_row[3]
                                        if comp_id in auth_atom_name_to_id_ext and _atom_id in auth_atom_name_to_id_ext[comp_id]\
                                           and len(set(_coord_atom_site['alt_comp_id'])) > 1:
                                            _row[19] = atom_id = auth_atom_name_to_id_ext[comp_id][_atom_id]
                                        else:
                                            _row[19] = atom_id =\
                                                _coord_atom_site['atom_id'][_coord_atom_site['alt_atom_id'].index(_atom_id)]
                                    elif 'split_comp_id' in _coord_atom_site:
                                        for _comp_id in _coord_atom_site['split_comp_id']:
                                            if _comp_id == comp_id:
                                                continue
                                            __seq_key = (_seq_key[0], _seq_key[1], _comp_id)
                                            __coord_atom_site = coord_atom_site[__seq_key]
                                            if __coord_atom_site is None:
                                                continue
                                            if 'alt_comp_id' in __coord_atom_site and 'alt_atom_id' in __coord_atom_site\
                                               and _atom_id in __coord_atom_site['alt_atom_id']:
                                                comp_id = _comp_id
                                                _row[18] = comp_id
                                                # Entity_assembly_ID, Entity_ID, Comp_index_ID, Seq_ID, Comp_ID, Auth_asym_ID, Auth_seq_ID
                                                cca_row = next((cca_row for cca_row in self.__reg.chem_comp_asm_dat
                                                                if cca_row[4] == comp_id and cca_row[5] == _seq_key[0]
                                                                and cca_row[6] == _seq_key[1]), None)
                                                if cca_row is not None:
                                                    _row[1], _row[2], _row[3], _row[4] = cca_row[0], cca_row[1], cca_row[2], cca_row[3]
                                                row[19] = atom_id =\
                                                    __coord_atom_site['atom_id'][__coord_atom_site['alt_atom_id'].index(_atom_id)]
                                                _seq_key = __seq_key
                                                break
                                            if _atom_id in __coord_atom_site['atom_id']:
                                                comp_id = _comp_id
                                                _row[18] = comp_id
                                                # Entity_assembly_ID, Entity_ID, Comp_index_ID, Seq_ID, Comp_ID, Auth_asym_ID, Auth_seq_ID
                                                cca_row = next((cca_row for cca_row in self.__reg.chem_comp_asm_dat
                                                                if cca_row[4] == comp_id and cca_row[5] == _seq_key[0]
                                                                and cca_row[6] == _seq_key[1]), None)
                                                if cca_row is not None:
                                                    _row[1], _row[2], _row[3], _row[4] = cca_row[0], cca_row[1], cca_row[2], cca_row[3]
                                                _seq_key = __seq_key
                                                break

                            if has_ins_code and seq_key in auth_to_ins_code:
                                _row[27] = auth_to_ins_code[seq_key]

                            if seq_key in auth_to_orig_seq:
                                if _row[20] not in EMPTY_VALUE and seq_key not in _auth_to_orig_seq:
                                    orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                    __seq_key = (_seq_key[0], orig_seq_id, comp_id)
                                    if self.__reg.csStat.getTypeOfCompId(comp_id)[2]\
                                       and seq_key not in coord_atom_site and __seq_key in auth_to_star_seq:
                                        _seq_key = __seq_key
                                        if _row[21] in EMPTY_VALUE or _row[22] in EMPTY_VALUE:
                                            _row[21], _row[22] = orig_seq_id, orig_comp_id
                                    else:
                                        _auth_to_orig_seq[seq_key] = (_row[20], orig_seq_id, orig_comp_id)
                                if not has_orig_seq:
                                    orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                    if orig_seq_id in EMPTY_VALUE:
                                        orig_seq_id = auth_seq_id
                                    if orig_comp_id in EMPTY_VALUE:
                                        orig_comp_id = comp_id
                                    _row[20], _row[21], _row[22], _row[23] =\
                                        auth_asym_id, orig_seq_id, orig_comp_id, _orig_atom_id
                                elif any(True for d in orig_dat[idx] if d in EMPTY_VALUE):
                                    if seq_key in _auth_to_orig_seq:
                                        _row[20], _row[21], _row[22] = _auth_to_orig_seq[seq_key]
                                    elif comp_id != auth_comp_id and translateToStdResName(comp_id, ccU=self.__reg.ccU) == auth_comp_id:
                                        _row[20], _row[21], _row[22] = auth_asym_id, auth_seq_id, comp_id
                                        _row[5] = comp_id = auth_comp_id
                                    if _row[23] in EMPTY_VALUE:
                                        _row[23] = atom_id
                                    ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                                    if ambig_code > 0:
                                        orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                        if orig_seq_id in EMPTY_VALUE:
                                            orig_seq_id = auth_seq_id
                                        if orig_comp_id in EMPTY_VALUE:
                                            orig_comp_id = comp_id
                                        _row[20], _row[21], _row[22] =\
                                            auth_asym_id, orig_seq_id, orig_comp_id
                                        if atom_id[0] not in PROTON_BEGIN_CODE:
                                            _row[23] = atom_id
                                        else:
                                            len_in_grp = len(self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id))
                                            if len_in_grp == 2:
                                                _row[23] = (atom_id[0:-1] + '1')\
                                                    if ambig_code == 2 and ch2_name_in_xplor and atom_id[-1] == '3' else atom_id
                                            elif len_in_grp == 3:
                                                _row[23] = (atom_id[-1] + atom_id[0:-1])\
                                                    if ch3_name_in_xplor and atom_id[0] == 'H'\
                                                    and atom_id[-1] in ('1', '2', '3')\
                                                    else atom_id
                                            elif _row[23] in EMPTY_VALUE:
                                                _row[23] = atom_id

                            else:
                                seq_key = next((k for k, v in auth_to_star_seq.items()
                                                if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                if seq_key is not None:
                                    _seq_key = (seq_key[0], seq_key[1])
                                    _row[16], _row[17], _row[18], _row[19] =\
                                        seq_key[0], seq_key[1], seq_key[2], atom_id

                                    if has_ins_code and seq_key in auth_to_ins_code:
                                        _row[27] = auth_to_ins_code[seq_key]

                                _row[20], _row[21], _row[22], _row[23] =\
                                    row[auth_asym_id_col], row[auth_seq_id_col], \
                                    row[auth_comp_id_col], row[auth_atom_id_col]

                            index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name, coord_atom_site, _seq_key,
                                                               comp_id, atom_id, loop, idx)
                            reparse_request |= reparse

                        elif auth_asym_id not in EMPTY_VALUE and auth_seq_id not in EMPTY_VALUE and auth_comp_id not in EMPTY_VALUE:

                            try:
                                _auth_seq_id = int(auth_seq_id)
                                seq_key = (auth_asym_id, _auth_seq_id, auth_comp_id)
                                _seq_key = (seq_key[0], seq_key[1])
                                if seq_key in auth_to_star_seq:
                                    entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                    self.__reg.ent_asym_id_with_exptl_data.add(entity_assembly_id)
                                    _row[1], _row[2] = entity_assembly_id, entity_id
                                    _row[3] = _row[4] = seq_id

                                    if has_ins_code and seq_key in auth_to_ins_code:
                                        _row[27] = auth_to_ins_code[seq_key]

                                    if seq_key in auth_to_orig_seq:
                                        if _row[20] not in EMPTY_VALUE and seq_key not in _auth_to_orig_seq:
                                            orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                            __seq_key = (_seq_key[0], orig_seq_id, comp_id)
                                            if self.__reg.csStat.getTypeOfCompId(comp_id)[2]\
                                               and seq_key not in coord_atom_site and __seq_key in auth_to_star_seq:
                                                _seq_key = __seq_key
                                                if _row[21] in EMPTY_VALUE or _row[22] in EMPTY_VALUE:
                                                    _row[21], _row[22] = orig_seq_id, orig_comp_id
                                            else:
                                                _auth_to_orig_seq[seq_key] = (_row[20], orig_seq_id, orig_comp_id)
                                        if not has_orig_seq:
                                            orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                            if orig_seq_id in EMPTY_VALUE:
                                                orig_seq_id = auth_seq_id
                                            if orig_comp_id in EMPTY_VALUE:
                                                orig_comp_id = comp_id
                                            _row[20], _row[21], _row[22], _row[23] =\
                                                auth_asym_id, orig_seq_id, orig_comp_id, _orig_atom_id
                                        elif any(True for d in orig_dat[idx] if d in EMPTY_VALUE):
                                            if seq_key in _auth_to_orig_seq:
                                                _row[20], _row[21], _row[22] = _auth_to_orig_seq[seq_key]
                                            if _row[23] in EMPTY_VALUE:
                                                _row[23] = atom_id
                                            ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                                            if ambig_code > 0:
                                                orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                                if orig_seq_id in EMPTY_VALUE:
                                                    orig_seq_id = auth_seq_id
                                                if orig_comp_id in EMPTY_VALUE:
                                                    orig_comp_id = comp_id
                                                _row[20], _row[21], _row[22] =\
                                                    auth_asym_id, orig_seq_id, orig_comp_id
                                                if atom_id[0] not in PROTON_BEGIN_CODE:
                                                    _row[23] = atom_id
                                                else:
                                                    len_in_grp = len(self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id))
                                                    if len_in_grp == 2:
                                                        _row[23] = (atom_id[0:-1] + '1')\
                                                            if ambig_code == 2 and ch2_name_in_xplor and atom_id[-1] == '3' else atom_id
                                                    elif len_in_grp == 3:
                                                        _row[23] = (atom_id[-1] + atom_id[0:-1])\
                                                            if ch3_name_in_xplor and atom_id[0] == 'H'\
                                                            and atom_id[-1] in ('1', '2', '3')\
                                                            else atom_id
                                                    elif _row[23] in EMPTY_VALUE:
                                                        _row[23] = atom_id

                                    else:
                                        seq_key = next((k for k, v in auth_to_star_seq.items()
                                                        if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                        if seq_key is not None:
                                            _seq_key = (seq_key[0], seq_key[1])
                                            _row[16], _row[17], _row[18], _row[19] =\
                                                seq_key[0], seq_key[1], seq_key[2], atom_id

                                            if has_ins_code and seq_key in auth_to_ins_code:
                                                _row[27] = auth_to_ins_code[seq_key]

                                        _row[20], _row[21], _row[22], _row[23] =\
                                            row[auth_asym_id_col], row[auth_seq_id_col], \
                                            row[auth_comp_id_col], row[auth_atom_id_col]

                                    index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                       coord_atom_site, _seq_key,
                                                                       comp_id, atom_id, loop, idx)
                                    reparse_request |= reparse

                                else:
                                    resolved = False

                            except ValueError:
                                resolved = False

                        else:
                            resolved = False

                    # DAOTHER-9281
                    elif has_auth_chain and (valid_auth_seq or row[auth_asym_id_col] in valid_auth_seq_per_chain):
                        auth_asym_id = row[auth_asym_id_col]
                        auth_seq_id = row[aux_auth_seq_id_col]
                        auth_comp_id = row[aux_auth_comp_id_col]

                        _row[17] = auth_seq_id

                        auth_seq_id_ = int(auth_seq_id)
                        seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                        _seq_key = (seq_key[0], seq_key[1])
                        try:
                            entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                            if atom_id != _row[19]:
                                if _seq_key in coord_atom_site:
                                    _coord_atom_site = coord_atom_site[_seq_key]
                                    if atom_id in _coord_atom_site['atom_id']:
                                        _row[19] = atom_id
                        except KeyError:
                            if self.__reg.annotation_mode or self.__reg.native_combined:
                                auth_asym_id = next((_auth_asym_id for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                     if _auth_seq_id == auth_seq_id_ and _auth_comp_id == auth_comp_id), auth_asym_id)
                                seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                                if seq_key in auth_to_star_seq:
                                    _row[16] = row[auth_asym_id_col] = auth_asym_id
                                    _row[20] = row[orig_asym_id_col] = auth_asym_id
                                    _seq_key = (seq_key[0], seq_key[1])
                                    entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                else:
                                    auth_asym_id, auth_comp_id = next(((_auth_asym_id, _auth_comp_id)
                                                                       for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                                       if _auth_seq_id == auth_seq_id_), (auth_asym_id, auth_comp_id))
                                    seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                                    if seq_key in auth_to_star_seq:
                                        _row[16] = row[auth_asym_id_col] = auth_asym_id
                                        _row[20] = row[orig_asym_id_col] = auth_asym_id
                                        _row[5] = row[comp_id_col] = auth_comp_id
                                        _row[18] = row[auth_comp_id_col] = auth_comp_id
                                        comp_id = auth_comp_id
                                        _seq_key = (seq_key[0], seq_key[1])
                                        entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                            if seq_key not in auth_to_star_seq:
                                auth_comp_id = next((_auth_comp_id for _auth_asym_id, _auth_seq_id, _auth_comp_id in auth_to_star_seq
                                                     if _auth_asym_id == auth_asym_id and _auth_seq_id == auth_seq_id_), auth_comp_id)
                                comp_id = _row[18] = auth_comp_id
                                seq_key = (auth_asym_id, auth_seq_id_, auth_comp_id)
                                if seq_key in auth_to_star_seq:
                                    entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                elif seq_key in auth_to_star_seq_ann:
                                    entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq_ann[seq_key]

                        self.__reg.ent_asym_id_with_exptl_data.add(entity_assembly_id)
                        _row[1], _row[2] = entity_assembly_id, entity_id
                        _row[3] = _row[4] = seq_id

                        if prefer_auth_atom_name:
                            if has_orig_seq:
                                orig_atom_id = _row[23]
                            _atom_id = atom_id
                            _seq_key = seq_key if seq_key in coord_atom_site else (seq_key[0], seq_key[1])
                            if _seq_key in coord_atom_site:
                                _coord_atom_site = coord_atom_site[_seq_key]
                                if comp_id in auth_atom_name_to_id and comp_id == _coord_atom_site['comp_id']:
                                    if _atom_id in auth_atom_name_to_id[comp_id]:
                                        if auth_atom_name_to_id[comp_id][_atom_id] in _coord_atom_site['atom_id']:
                                            _row[19] = atom_id = auth_atom_name_to_id[comp_id][_atom_id]
                                        elif 'split_comp_id' not in _coord_atom_site and has_orig_seq\
                                                and orig_atom_id in auth_atom_name_to_id[comp_id]:
                                            _row[19] = atom_id = auth_atom_name_to_id[comp_id][orig_atom_id]
                                if 'alt_atom_id' in _coord_atom_site and _atom_id in _coord_atom_site['alt_atom_id']\
                                   and comp_id == _coord_atom_site['comp_id']:
                                    _row[19] = atom_id = _coord_atom_site['atom_id'][_coord_atom_site['alt_atom_id'].index(_atom_id)]
                                # DAOTHER-8751, 8817 (D_1300043061)
                                elif 'alt_comp_id' in _coord_atom_site and 'alt_atom_id' in _coord_atom_site\
                                     and _atom_id in _coord_atom_site['alt_atom_id']\
                                     and comp_id == _coord_atom_site['alt_comp_id'][_coord_atom_site['alt_atom_id'].index(_atom_id)]:
                                    _row[18] = comp_id
                                    # Entity_assembly_ID, Entity_ID, Comp_index_ID, Seq_ID, Comp_ID, Auth_asym_ID, Auth_seq_ID
                                    cca_row = next((cca_row for cca_row in self.__reg.chem_comp_asm_dat
                                                    if cca_row[4] == comp_id and cca_row[5] == _seq_key[0]
                                                    and cca_row[6] == _seq_key[1]), None)
                                    if cca_row is not None:
                                        _row[1], _row[2], _row[3], _row[4] = cca_row[0], cca_row[1], cca_row[2], cca_row[3]
                                    if comp_id in auth_atom_name_to_id_ext and _atom_id in auth_atom_name_to_id_ext[comp_id]\
                                       and len(set(_coord_atom_site['alt_comp_id'])) > 1:
                                        _row[19] = atom_id = auth_atom_name_to_id_ext[comp_id][_atom_id]
                                    else:
                                        _row[19] = atom_id = _coord_atom_site['atom_id'][_coord_atom_site['alt_atom_id'].index(_atom_id)]
                                elif 'split_comp_id' in _coord_atom_site:
                                    for _comp_id in _coord_atom_site['split_comp_id']:
                                        if _comp_id == comp_id:
                                            continue
                                        __seq_key = (_seq_key[0], _seq_key[1], _comp_id)
                                        __coord_atom_site = coord_atom_site[__seq_key]
                                        if __coord_atom_site is None:
                                            continue
                                        if 'alt_comp_id' in __coord_atom_site and 'alt_atom_id' in __coord_atom_site\
                                           and _atom_id in __coord_atom_site['alt_atom_id']:
                                            comp_id = _comp_id
                                            _row[18] = comp_id
                                            # Entity_assembly_ID, Entity_ID, Comp_index_ID, Seq_ID, Comp_ID, Auth_asym_ID, Auth_seq_ID
                                            cca_row = next((cca_row for cca_row in self.__reg.chem_comp_asm_dat
                                                            if cca_row[4] == comp_id and cca_row[5] == _seq_key[0]
                                                            and cca_row[6] == _seq_key[1]), None)
                                            if cca_row is not None:
                                                _row[1], _row[2], _row[3], _row[4] = cca_row[0], cca_row[1], cca_row[2], cca_row[3]
                                            row[19] = atom_id =\
                                                __coord_atom_site['atom_id'][__coord_atom_site['alt_atom_id'].index(_atom_id)]
                                            _seq_key = __seq_key
                                            break
                                        if _atom_id in __coord_atom_site['atom_id']:
                                            comp_id = _comp_id
                                            _row[18] = comp_id
                                            # Entity_assembly_ID, Entity_ID, Comp_index_ID, Seq_ID, Comp_ID, Auth_asym_ID, Auth_seq_ID
                                            cca_row = next((cca_row for cca_row in self.__reg.chem_comp_asm_dat
                                                            if cca_row[4] == comp_id and cca_row[5] == _seq_key[0]
                                                            and cca_row[6] == _seq_key[1]), None)
                                            if cca_row is not None:
                                                _row[1], _row[2], _row[3], _row[4] = cca_row[0], cca_row[1], cca_row[2], cca_row[3]
                                            _seq_key = __seq_key
                                            break

                        if has_ins_code and seq_key in auth_to_ins_code:
                            _row[27] = auth_to_ins_code[seq_key]

                        if seq_key in auth_to_orig_seq:
                            if _row[20] not in EMPTY_VALUE and seq_key not in _auth_to_orig_seq:
                                orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                __seq_key = (_seq_key[0], orig_seq_id, comp_id)
                                if self.__reg.csStat.getTypeOfCompId(comp_id)[2]\
                                   and seq_key not in coord_atom_site and __seq_key in auth_to_star_seq:
                                    _seq_key = __seq_key
                                    if _row[21] in EMPTY_VALUE or _row[22] in EMPTY_VALUE:
                                        _row[21], _row[22] = orig_seq_id, orig_comp_id
                                else:
                                    _auth_to_orig_seq[seq_key] = (_row[20], orig_seq_id, orig_comp_id)
                            if not has_orig_seq:
                                orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                if orig_seq_id in EMPTY_VALUE:
                                    orig_seq_id = auth_seq_id
                                if orig_comp_id in EMPTY_VALUE:
                                    orig_comp_id = comp_id
                                _row[20], _row[21], _row[22], _row[23] =\
                                    auth_asym_id, orig_seq_id, orig_comp_id, _orig_atom_id
                            elif any(True for d in orig_dat[idx] if d in EMPTY_VALUE):
                                if seq_key in _auth_to_orig_seq:
                                    _row[20], _row[21], _row[22] = _auth_to_orig_seq[seq_key]
                                elif comp_id != auth_comp_id and translateToStdResName(comp_id, ccU=self.__reg.ccU) == auth_comp_id:
                                    _row[20], _row[21], _row[22] = auth_asym_id, auth_seq_id, comp_id
                                    _row[5] = comp_id = auth_comp_id
                                if _row[23] in EMPTY_VALUE:
                                    _row[23] = atom_id
                                ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                                if ambig_code > 0:
                                    orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                    if orig_seq_id in EMPTY_VALUE:
                                        orig_seq_id = auth_seq_id
                                    if orig_comp_id in EMPTY_VALUE:
                                        orig_comp_id = comp_id
                                    _row[20], _row[21], _row[22] =\
                                        auth_asym_id, orig_seq_id, orig_comp_id
                                    if atom_id[0] not in PROTON_BEGIN_CODE:
                                        _row[23] = atom_id
                                    else:
                                        len_in_grp = len(self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id))
                                        if len_in_grp == 2:
                                            _row[23] = (atom_id[0:-1] + '1')\
                                                if ambig_code == 2 and ch2_name_in_xplor and atom_id[-1] == '3' else atom_id
                                        elif len_in_grp == 3:
                                            _row[23] = (atom_id[-1] + atom_id[0:-1])\
                                                if ch3_name_in_xplor and atom_id[0] == 'H'\
                                                and atom_id[-1] in ('1', '2', '3')\
                                                else atom_id
                                        elif _row[23] in EMPTY_VALUE:
                                            _row[23] = atom_id

                        else:
                            seq_key = next((k for k, v in auth_to_star_seq.items()
                                            if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                            if seq_key is not None:
                                _seq_key = (seq_key[0], seq_key[1])
                                _row[16], _row[17], _row[18], _row[19] =\
                                    seq_key[0], seq_key[1], seq_key[2], atom_id

                                if has_ins_code and seq_key in auth_to_ins_code:
                                    _row[27] = auth_to_ins_code[seq_key]

                            _row[20], _row[21], _row[22], _row[23] =\
                                row[auth_asym_id_col], row[aux_auth_seq_id_col], \
                                row[aux_auth_comp_id_col], row[aux_auth_atom_id_col]

                        index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name, coord_atom_site, _seq_key,
                                                           comp_id, atom_id, loop, idx)
                        reparse_request |= reparse

                    else:
                        resolved = False

                    if not resolved:

                        chain_id = row[chain_id_col]
                        if chain_id in EMPTY_VALUE:
                            chain_id = REPRESENTATIVE_ASYM_ID

                        if chain_id in copied_chain_ids:
                            continue

                        try:
                            seq_id = int(row[seq_id_col])
                        except (ValueError, TypeError):
                            seq_id = None

                        if auth_asym_id_col != -1 and row[auth_asym_id_col] == 'UNMAPPED':
                            _row[24] = 'UNMAPPED'

                        auth_asym_id, auth_seq_id = get_auth_seq_scheme(chain_id, seq_id)

                        resolved = True

                        if None not in (auth_asym_id, auth_seq_id):
                            seq_key = (auth_asym_id, auth_seq_id, _orig_comp_id)
                            _seq_key = (seq_key[0], seq_key[1])
                            if seq_key in auth_to_star_seq:
                                entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                comp_id = next((_v[1] for _k, _v in auth_to_orig_seq.items() if _k == seq_key), _orig_comp_id)
                                self.__reg.ent_asym_id_with_exptl_data.add(entity_assembly_id)
                                _row[1], _row[2] = entity_assembly_id, entity_id
                                _row[3] = _row[4] = seq_id

                                _row[16], _row[17], _row[18], _row[19] =\
                                    auth_asym_id, auth_seq_id, comp_id, atom_id
                                if has_ins_code and seq_key in auth_to_ins_code:
                                    _row[27] = auth_to_ins_code[seq_key]

                                if seq_key in auth_to_orig_seq:
                                    if _row[20] not in EMPTY_VALUE and seq_key not in _auth_to_orig_seq:
                                        orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                        __seq_key = (_seq_key[0], orig_seq_id, comp_id)
                                        if self.__reg.csStat.getTypeOfCompId(comp_id)[2]\
                                           and seq_key not in coord_atom_site and __seq_key in auth_to_star_seq:
                                            _seq_key = __seq_key
                                            if _row[21] in EMPTY_VALUE or _row[22] in EMPTY_VALUE:
                                                _row[21], _row[22] = orig_seq_id, orig_comp_id
                                        else:
                                            _auth_to_orig_seq[seq_key] = (_row[20], orig_seq_id, orig_comp_id)
                                    if not has_orig_seq:
                                        orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                        if orig_seq_id in EMPTY_VALUE:
                                            orig_seq_id = auth_seq_id
                                        if orig_comp_id in EMPTY_VALUE:
                                            orig_comp_id = comp_id
                                        _row[20], _row[21], _row[22], _row[23] =\
                                            auth_asym_id, orig_seq_id, orig_comp_id, _orig_atom_id
                                    elif any(True for d in orig_dat[idx] if d in EMPTY_VALUE):
                                        if seq_key in _auth_to_orig_seq:
                                            _row[20], _row[21], _row[22] = _auth_to_orig_seq[seq_key]
                                        if _row[23] in EMPTY_VALUE:
                                            _row[23] = atom_id
                                        ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                                        if ambig_code > 0:
                                            orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                            if orig_seq_id in EMPTY_VALUE:
                                                orig_seq_id = auth_seq_id
                                            if orig_comp_id in EMPTY_VALUE:
                                                orig_comp_id = comp_id
                                            _row[20], _row[21], _row[22] =\
                                                auth_asym_id, orig_seq_id, orig_comp_id
                                            if atom_id[0] not in PROTON_BEGIN_CODE:
                                                _row[23] = atom_id
                                            else:
                                                len_in_grp = len(self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id))
                                                if len_in_grp == 2:
                                                    _row[23] = (atom_id[0:-1] + '1')\
                                                        if ambig_code == 2 and ch2_name_in_xplor and atom_id[-1] == '3' else atom_id
                                                elif len_in_grp == 3:
                                                    _row[23] = (atom_id[-1] + atom_id[0:-1])\
                                                        if ch3_name_in_xplor and atom_id[0] == 'H'\
                                                        and atom_id[-1] in ('1', '2', '3')\
                                                        else atom_id
                                                elif _row[23] in EMPTY_VALUE:
                                                    _row[23] = atom_id

                                else:
                                    seq_key = next((k for k, v in auth_to_star_seq.items()
                                                    if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                    if seq_key is not None:
                                        _seq_key = (seq_key[0], seq_key[1])
                                        _row[16], _row[17], _row[18], _row[19] =\
                                            seq_key[0], seq_key[1], seq_key[2], atom_id
                                        if has_ins_code and seq_key in auth_to_ins_code:
                                            _row[27] = auth_to_ins_code[seq_key]

                                    if has_auth_seq:
                                        _row[20], _row[21], _row[22], _row[23] =\
                                            row[auth_asym_id_col], row[auth_seq_id_col], \
                                            row[auth_comp_id_col], row[auth_atom_id_col]

                                index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                   coord_atom_site, _seq_key,
                                                                   comp_id, atom_id, loop, idx)
                                reparse_request |= reparse

                                if chain_id not in can_auth_asym_id_mapping:
                                    can_auth_asym_id_mapping[chain_id] = {'auth_asym_id': auth_asym_id,
                                                                          'ref_auth_seq_id': auth_seq_id
                                                                          }

                            else:

                                item = next((item for item in entity_assembly if item['auth_asym_id'] == auth_asym_id), None)

                                if item is not None and poly_seq is not None\
                                   and any(True for _ps in poly_seq
                                           if _ps['chain_id'] == auth_asym_id and auth_seq_id in _ps['seq_id']):
                                    entity_assembly_id = item['entity_assembly_id']
                                    entity_id = item['entity_id']

                                    _row[1], _row[2] = entity_assembly_id, entity_id
                                    _row[3] = _row[4] = seq_id

                                    seq_key = next((k for k, v in auth_to_star_seq.items()
                                                    if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                    if seq_key is not None and (seq_id == seq_key[1] or comp_id == seq_key[2]):
                                        _seq_key = (seq_key[0], seq_key[1])
                                        _row[16], _row[17], _row[18], _row[19] =\
                                            seq_key[0], seq_key[1], seq_key[2], atom_id
                                        if has_ins_code and seq_key in auth_to_ins_code:
                                            _row[27] = auth_to_ins_code[seq_key]
                                    elif seq_key is not None:  # 5ydx
                                        offset = seq_id - seq_key[1]
                                        seq_id += offset
                                        _row[3] = _row[4] = seq_id
                                        _seq_key = None
                                        _row[24] = 'UNMAPPED'
                                    else:
                                        resolved = False

                                    if has_auth_seq:
                                        _row[20], _row[21], _row[22], _row[23] =\
                                            row[auth_asym_id_col], row[auth_seq_id_col], \
                                            row[auth_comp_id_col], row[auth_atom_id_col]

                                    if resolved:
                                        index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                           coord_atom_site, _seq_key,
                                                                           comp_id, atom_id, loop, idx)
                                        reparse_request |= reparse

                                    if chain_id not in can_auth_asym_id_mapping:
                                        can_auth_asym_id_mapping[chain_id] = {'auth_asym_id': auth_asym_id,
                                                                              'ref_auth_seq_id': auth_seq_id
                                                                              }

                                else:
                                    resolved = False

                        else:

                            if has_auth_seq:

                                try:

                                    auth_asym_id = row[auth_asym_id_col]
                                    auth_seq_id = int(row[auth_seq_id_col])

                                    item = next((item for item in entity_assembly if item['auth_asym_id'] == auth_asym_id), None)

                                    if item is not None and poly_seq is not None\
                                       and any(True for _ps in poly_seq
                                               if _ps['chain_id'] == auth_asym_id and auth_seq_id in _ps['seq_id']):
                                        entity_assembly_id = item['entity_assembly_id']
                                        entity_id = item['entity_id']

                                        _row[1], _row[2] = entity_assembly_id, entity_id
                                        _row[3] = _row[4] = seq_id

                                        seq_key = next((k for k, v in auth_to_star_seq.items()
                                                        if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                        if seq_key is not None:

                                            if comp_id != seq_key[2] and comp_id in STD_MON_DICT and seq_key[2] in STD_MON_DICT:
                                                resolved = False

                                            else:
                                                _seq_key = (seq_key[0], seq_key[1])
                                                _row[16], _row[17], _row[18], _row[19] =\
                                                    seq_key[0], seq_key[1], seq_key[2], atom_id
                                                if has_ins_code and seq_key in auth_to_ins_code:
                                                    _row[27] = auth_to_ins_code[seq_key]

                                        if resolved:
                                            _row[20], _row[21], _row[22], _row[23] =\
                                                row[auth_asym_id_col], row[auth_seq_id_col], \
                                                row[auth_comp_id_col], row[auth_atom_id_col]

                                            index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                               coord_atom_site, _seq_key,
                                                                               comp_id, atom_id, loop, idx)
                                            reparse_request |= reparse

                                    else:
                                        resolved = False

                                except (ValueError, TypeError):
                                    resolved = False

                            else:

                                def retrieve_label_comp_id(can_seq_id, can_comp_id):
                                    for _seq_key in auth_to_star_seq.keys():
                                        if _seq_key[1] == can_seq_id and _seq_key in auth_to_orig_seq:
                                            if can_comp_id == auth_to_orig_seq[_seq_key][1]:
                                                return _seq_key[2]
                                    return can_comp_id

                                can_auth_asym_id = [_auth_asym_id for _auth_asym_id, _auth_seq_id, _comp_id in auth_to_star_seq
                                                    if _auth_seq_id == seq_id and _comp_id in (_orig_comp_id, '.')]

                                if len(can_auth_asym_id) == 0:
                                    can_auth_asym_id = [_auth_asym_id for _auth_asym_id, _auth_seq_id, _comp_id in auth_to_star_seq
                                                        if _auth_seq_id == seq_id
                                                        and _comp_id == retrieve_label_comp_id(seq_id, _orig_comp_id)]
                                    if len(can_auth_asym_id) > 0:
                                        _orig_comp_id = retrieve_label_comp_id(seq_id, _orig_comp_id)

                                if len(can_auth_asym_id) != 1:
                                    resolved = False

                                else:
                                    auth_asym_id, auth_seq_id = can_auth_asym_id[0], seq_id

                                    seq_key = (auth_asym_id, auth_seq_id, _orig_comp_id)
                                    dummy_key = (auth_asym_id, auth_seq_id, '.')
                                    _seq_key = (seq_key[0], seq_key[1])
                                    if seq_key in auth_to_star_seq or (dummy_key in auth_to_star_seq and _orig_comp_id in STD_MON_DICT):
                                        try:
                                            entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[seq_key]
                                        except KeyError:  # DAOTHER-9644: map residue on truncated loop
                                            if _seq_key not in truncated_loop_sequence:
                                                truncated_loop_sequence.append(_seq_key)
                                            entity_assembly_id, seq_id, entity_id, _ = auth_to_star_seq[dummy_key]
                                            auth_to_star_seq[seq_key] = auth_to_star_seq[dummy_key]
                                            del auth_to_star_seq[dummy_key]
                                            auth_to_orig_seq[seq_key] = (auth_to_orig_seq[dummy_key][0], _orig_comp_id)
                                            del auth_to_orig_seq[dummy_key]
                                            if has_ins_code:
                                                auth_to_ins_code[seq_key] = auth_to_ins_code[dummy_key]
                                                del auth_to_ins_code[dummy_key]
                                            cif_ps = next((cif_ps for cif_ps in self.__reg.caC['polymer_sequence']
                                                           if cif_ps['auth_chain_id'] == auth_asym_id
                                                           and auth_seq_id in cif_ps['auth_seq_id']), None)
                                            if cif_ps is not None:
                                                _idx_ = cif_ps['auth_seq_id'].index(auth_seq_id)
                                                if cif_ps['comp_id'][_idx_] in EMPTY_VALUE:
                                                    cif_ps['comp_id'][_idx_] = cif_ps['auth_comp_id'][_idx_] = _orig_comp_id
                                                    if self.__reg.asmChkCachePath is not None:
                                                        write_as_pickle(self.__reg.caC, self.__reg.asmChkCachePath)
                                        comp_id = next((_v[1] for _k, _v in auth_to_orig_seq.items() if _k == seq_key), _orig_comp_id)
                                        self.__reg.ent_asym_id_with_exptl_data.add(entity_assembly_id)
                                        _row[1], _row[2] = entity_assembly_id, entity_id
                                        _row[3] = _row[4] = seq_id

                                        _row[16], _row[17], _row[18], _row[19] =\
                                            auth_asym_id, auth_seq_id, comp_id, atom_id
                                        if has_ins_code and seq_key in auth_to_ins_code:
                                            _row[27] = auth_to_ins_code[seq_key]

                                        if seq_key in auth_to_orig_seq:
                                            if _row[20] not in EMPTY_VALUE and seq_key not in _auth_to_orig_seq:
                                                orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                                __seq_key = (_seq_key[0], orig_seq_id, comp_id)
                                                if self.__reg.csStat.getTypeOfCompId(comp_id)[2]\
                                                   and seq_key not in coord_atom_site and __seq_key in auth_to_star_seq:
                                                    _seq_key = __seq_key
                                                    if _row[21] in EMPTY_VALUE or _row[22] in EMPTY_VALUE:
                                                        _row[21], _row[22] = orig_seq_id, orig_comp_id
                                                else:
                                                    _auth_to_orig_seq[seq_key] = (_row[20], orig_seq_id, orig_comp_id)
                                            if not has_orig_seq:
                                                orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                                if orig_seq_id in EMPTY_VALUE:
                                                    orig_seq_id = auth_seq_id
                                                if orig_comp_id in EMPTY_VALUE:
                                                    orig_comp_id = comp_id
                                                _row[20], _row[21], _row[22], _row[23] =\
                                                    auth_asym_id, orig_seq_id, orig_comp_id, _orig_atom_id
                                            elif any(True for d in orig_dat[idx] if d in EMPTY_VALUE):
                                                if seq_key in _auth_to_orig_seq:
                                                    _row[20], _row[21], _row[22] = _auth_to_orig_seq[seq_key]
                                                if _row[23] in EMPTY_VALUE:
                                                    _row[23] = atom_id
                                                ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                                                if ambig_code > 0:
                                                    orig_seq_id, orig_comp_id = auth_to_orig_seq[seq_key]
                                                    if orig_seq_id in EMPTY_VALUE:
                                                        orig_seq_id = auth_seq_id
                                                    if orig_comp_id in EMPTY_VALUE:
                                                        orig_comp_id = comp_id
                                                    _row[20], _row[21], _row[22] =\
                                                        auth_asym_id, orig_seq_id, orig_comp_id
                                                    if atom_id[0] not in PROTON_BEGIN_CODE:
                                                        _row[23] = atom_id
                                                    else:
                                                        len_in_grp = len(self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id))
                                                        if len_in_grp == 2:
                                                            _row[23] = (atom_id[0:-1] + '1')\
                                                                if ambig_code == 2 and ch2_name_in_xplor and atom_id[-1] == '3' else atom_id
                                                        elif len_in_grp == 3:
                                                            _row[23] = (atom_id[-1] + atom_id[0:-1])\
                                                                if ch3_name_in_xplor and atom_id[0] == 'H'\
                                                                and atom_id[-1] in ('1', '2', '3')\
                                                                else atom_id
                                                        elif _row[23] in EMPTY_VALUE:
                                                            _row[23] = atom_id

                                        else:
                                            seq_key = next((k for k, v in auth_to_star_seq.items()
                                                            if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                            if seq_key is not None:
                                                _seq_key = (seq_key[0], seq_key[1])
                                                _row[16], _row[17], _row[18], _row[19] =\
                                                    seq_key[0], seq_key[1], seq_key[2], atom_id
                                                if has_ins_code and seq_key in auth_to_ins_code:
                                                    _row[27] = auth_to_ins_code[seq_key]

                                            if has_auth_seq:
                                                _row[20], _row[21], _row[22], _row[23] =\
                                                    row[auth_asym_id_col], row[auth_seq_id_col], \
                                                    row[auth_comp_id_col], row[auth_atom_id_col]

                                        index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                           coord_atom_site, _seq_key,
                                                                           comp_id, atom_id, loop, idx)
                                        reparse_request |= reparse

                                        if chain_id not in can_auth_asym_id_mapping:
                                            can_auth_asym_id_mapping[chain_id] = {'auth_asym_id': auth_asym_id,
                                                                                  'ref_auth_seq_id': auth_seq_id
                                                                                  }

                                    else:

                                        item = next((item for item in entity_assembly if item['auth_asym_id'] == auth_asym_id), None)

                                        if item is not None and poly_seq is not None\
                                           and any(True for _ps in poly_seq
                                                   if _ps['chain_id'] == auth_asym_id and auth_seq_id in _ps['seq_id']):
                                            entity_assembly_id = item['entity_assembly_id']
                                            entity_id = item['entity_id']

                                            _row[1], _row[2] = entity_assembly_id, entity_id
                                            _row[3] = _row[4] = seq_id

                                            seq_key = next((k for k, v in auth_to_star_seq.items()
                                                            if v[0] == entity_assembly_id and v[1] == seq_id and v[2] == entity_id), None)
                                            if seq_key is not None:
                                                _seq_key = (seq_key[0], seq_key[1])
                                                _row[16], _row[17], _row[18], _row[19] =\
                                                    seq_key[0], seq_key[1], seq_key[2], atom_id
                                                if has_ins_code and seq_key in auth_to_ins_code:
                                                    _row[27] = auth_to_ins_code[seq_key]

                                            if has_auth_seq:
                                                _row[20], _row[21], _row[22], _row[23] =\
                                                    row[auth_asym_id_col], row[auth_seq_id_col], \
                                                    row[auth_comp_id_col], row[auth_atom_id_col]

                                            index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                               coord_atom_site, _seq_key,
                                                                               comp_id, atom_id, loop, idx)
                                            reparse_request |= reparse

                                            if chain_id not in can_auth_asym_id_mapping:
                                                can_auth_asym_id_mapping[chain_id] = {'auth_asym_id': auth_asym_id,
                                                                                      'ref_auth_seq_id': seq_key[1]
                                                                                      }

                                        else:
                                            resolved = False

                        is_valid, cc_name, _ = self.__reg.dpV.getChemCompNameAndStatusOf(comp_id)
                        comp_id_bmrb_only = not is_valid and cc_name is not None and 'processing site' in cc_name

                        if not resolved and has_auth_seq and not comp_id_bmrb_only:
                            try:
                                seq_id = int(row[auth_seq_id_col])
                            except (ValueError, TypeError):
                                seq_id = None

                        if not resolved and seq_id is not None and has_coordinate:

                            def test_seq_id_offset(lp, index, row, _row, _idx, chain_id, seq_id, comp_id, offset):
                                _found = _resolved = _reparse = False
                                _index = index

                                auth_asym_id, auth_seq_id = get_auth_seq_scheme(chain_id, seq_id + offset)
                                if None not in (auth_asym_id, auth_seq_id):
                                    _found = _resolved = True

                                    item = next((item for item in entity_assembly if item['auth_asym_id'] == auth_asym_id), None)

                                    if item is not None and poly_seq is not None and any(True for _ps in poly_seq_common
                                                                                         if _ps['chain_id'] == auth_asym_id
                                                                                         and auth_seq_id in _ps['seq_id']):
                                        entity_assembly_id = item['entity_assembly_id']
                                        entity_id = item['entity_id']

                                        _row[1], _row[2] = entity_assembly_id, entity_id
                                        _row[3] = _row[4] = seq_id

                                        seq_key = next((k for k, v in auth_to_star_seq.items()
                                                        if v[0] == entity_assembly_id and v[1] == seq_id + offset
                                                        and v[2] == entity_id), None)
                                        _seq_key = None
                                        if seq_key is not None and comp_id == seq_key[2]:
                                            _seq_key = (seq_key[0], seq_key[1])
                                            _row[16], _row[17], _row[18], _row[19] =\
                                                seq_key[0], seq_key[1] - offset, comp_id, atom_id
                                            if has_ins_code and seq_key in auth_to_ins_code:
                                                _row[27] = auth_to_ins_code[seq_key]
                                        else:
                                            if has_orig_seq:  # DAOTHER-8758
                                                try:
                                                    orig_asym_id = row[orig_asym_id_col]
                                                    orig_seq_id = int(row[orig_seq_id_col])
                                                    _item = next((item for item in entity_assembly
                                                                  if item['auth_asym_id'] == orig_asym_id), None)
                                                    if _item is not None:
                                                        _entity_assembly_id = _item['entity_assembly_id']
                                                        _entity_id = _item['entity_id']
                                                        __seq_key = next((k for k, v in auth_to_star_seq.items()
                                                                          if v[0] == _entity_assembly_id and v[1] in (seq_id, orig_seq_id)
                                                                          and v[2] == _entity_id), None)
                                                        if __seq_key is not None:
                                                            comp_id = __seq_key[2]
                                                            _row[1], _row[2], _row[3], _row[4] =\
                                                                _entity_assembly_id, _entity_id, __seq_key[1], __seq_key[1]
                                                            _seq_key = (__seq_key[0], __seq_key[1])
                                                            _row[16], _row[17], _row[18], _row[19] =\
                                                                __seq_key[0], __seq_key[1], comp_id, atom_id
                                                            if has_ins_code and __seq_key in auth_to_ins_code:
                                                                _row[27] = auth_to_ins_code[__seq_key]
                                                        else:
                                                            _seq_key = (auth_asym_id, auth_seq_id + offset)
                                                    else:
                                                        _seq_key = (auth_asym_id, auth_seq_id + offset)
                                                except ValueError:
                                                    _seq_key = (auth_asym_id, auth_seq_id + offset)
                                            else:
                                                _item = next((item for item in entity_assembly if item['auth_asym_id'] == chain_id), None)
                                                if _item is not None:
                                                    _entity_assembly_id = _item['entity_assembly_id']
                                                    _entity_id = _item['entity_id']
                                                    __seq_key = next((k for k, v in auth_to_star_seq.items()
                                                                      if v[0] == _entity_assembly_id and v[1] == seq_id + offset
                                                                      and v[2] == _entity_id), None)
                                                    if __seq_key is not None:
                                                        _offset = __seq_key[1] - (seq_id + offset)
                                                        _seq_id = seq_id - _offset
                                                        __seq_key = next((k for k, v in auth_to_star_seq.items()
                                                                          if v[0] == _entity_assembly_id and v[1] == _seq_id
                                                                          and v[2] == _entity_id), None)
                                                        if __seq_key is not None and comp_id == __seq_key[2]:
                                                            comp_id = __seq_key[2]
                                                            _row[1], _row[2], _row[3], _row[4] =\
                                                                _entity_assembly_id, _entity_id, _seq_id, _seq_id
                                                            _seq_key = (__seq_key[0], __seq_key[1])
                                                            _row[16], _row[17], _row[18], _row[19] =\
                                                                __seq_key[0], __seq_key[1], comp_id, atom_id
                                                            if has_ins_code and __seq_key in auth_to_ins_code:
                                                                _row[27] = auth_to_ins_code[__seq_key]
                                                        else:
                                                            _resolved = False
                                                    else:
                                                        _resolved = False
                                                else:
                                                    _resolved = False

                                        if has_auth_seq:
                                            _row[20], _row[21], _row[22], _row[23] =\
                                                row[auth_asym_id_col], row[auth_seq_id_col], \
                                                row[auth_comp_id_col], row[auth_atom_id_col]
                                        else:
                                            _row[20], _row[21], _row[22], _row[23] =\
                                                _row[16], _row[17], _row[18], _row[19]

                                        if _resolved:
                                            _index, _row, _reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                                 coord_atom_site, _seq_key,
                                                                                 comp_id, atom_id, loop, _idx)

                                    else:
                                        _resolved = False

                                return _found, _resolved, _reparse, _index, _row

                            found = False
                            for offset in range(1, GLOBAL_OFFSET_ATTEMPT):
                                found, resolved, reparse, _index, __row =\
                                    test_seq_id_offset(lp, index, row, _row, idx, chain_id, seq_id, comp_id, offset)

                                if found:
                                    if resolved:
                                        index, _row = _index, __row
                                        reparse_request |= reparse
                                    break

                                found, resolved, reparse, _index, __row =\
                                    test_seq_id_offset(lp, index, row, _row, idx, chain_id, seq_id, comp_id, -offset)

                                if found:
                                    if resolved:
                                        index, _row = _index, __row
                                        reparse_request |= reparse
                                    break

                            if not resolved and chain_id in can_auth_asym_id_mapping:  # DAOTHER-8751, 8755

                                if can_auth_asym_id_mapping_failed and trial == 0:  # DAOTHER-9158
                                    reparse_request = True

                                mapping = can_auth_asym_id_mapping[chain_id]

                                auth_asym_id = mapping['auth_asym_id']
                                ref_auth_seq_id = mapping['ref_auth_seq_id']

                                item = next((item for item in entity_assembly if item['auth_asym_id'] == auth_asym_id), None)

                                if item is not None and poly_seq is not None\
                                    and any(True for _ps in poly_seq_common
                                            if _ps['chain_id'] in (auth_asym_id, str(letterToDigit(auth_asym_id)))
                                            and ref_auth_seq_id in _ps['seq_id']):
                                    resolved = True
                                    found = False

                                    entity_assembly_id = item['entity_assembly_id']
                                    entity_id = item['entity_id']

                                    _row[1], _row[2] = entity_assembly_id, entity_id
                                    _row[3] = _row[4] = seq_id

                                    _row[16], _row[17], _row[18], _row[19] =\
                                        auth_asym_id, seq_id, comp_id, atom_id

                                    if has_auth_seq:
                                        _row[20], _row[21], _row[22], _row[23] =\
                                            row[auth_asym_id_col], row[auth_seq_id_col], \
                                            row[auth_comp_id_col], row[auth_atom_id_col]
                                    else:
                                        _row[20], _row[21], _row[22], _row[23] =\
                                            _row[16], _row[17], _row[18], _row[19]

                                    # DAOTHER-9281
                                    if isinstance(_row[1], int) and str(_row[1]) in seq_id_offset_for_unmapped:
                                        __offset = seq_id_offset_for_unmapped[str(_row[1])]
                                    elif isinstance(_row[1], str) and _row[1] in seq_id_offset_for_unmapped:
                                        __offset = seq_id_offset_for_unmapped[_row[1]]
                                    else:
                                        __offset = 0

                                    if comp_id not in STD_MON_DICT:
                                        for item in entity_assembly:
                                            if 'comp_id' in item and comp_id == item['comp_id']:
                                                _entity_assembly_id = item['entity_assembly_id']
                                                _entity_id = item['entity_id']

                                                __seq_key = next((k for k, v in auth_to_star_seq.items()
                                                                  if v[0] == _entity_assembly_id and v[1] == seq_id
                                                                  and v[2] == _entity_id), None)
                                                if __seq_key is not None:
                                                    found = True
                                                    comp_id = __seq_key[2]
                                                    _row[1], _row[2], _row[3], _row[4] =\
                                                        _entity_assembly_id, _entity_id, __seq_key[1], __seq_key[1]
                                                    _seq_key = (__seq_key[0], __seq_key[1])
                                                    _row[16], _row[17], _row[18], _row[19] =\
                                                        __seq_key[0], __seq_key[1], comp_id, atom_id
                                                    if has_ins_code and __seq_key in auth_to_ins_code:
                                                        _row[27] = auth_to_ins_code[__seq_key]
                                                    break

                                                if self.__reg.caC['non_polymer'] is not None:
                                                    ligands = 0
                                                    for np in self.__reg.caC['non_polymer']:
                                                        if comp_id == np['comp_id'][0]:
                                                            ligands += len(np['seq_id'])
                                                    if ligands == 1:  # DAOTHER-9063, 2nd case
                                                        __seq_key = next((k for k, v in auth_to_star_seq.items()
                                                                          if v[0] == _entity_assembly_id and v[2] == _entity_id), None)
                                                        if __seq_key is not None:
                                                            seq_id = auth_to_star_seq[__seq_key][1]
                                                            found = True
                                                            comp_id = __seq_key[2]
                                                            _row[1], _row[2] = _entity_assembly_id, _entity_id
                                                            _row[3] = _row[4] = seq_id
                                                            _seq_key = (__seq_key[0], __seq_key[1])
                                                            _row[16], _row[17], _row[18], _row[19] =\
                                                                __seq_key[0], __seq_key[1], comp_id, atom_id
                                                            if has_ins_code and __seq_key in auth_to_ins_code:
                                                                _row[27] = auth_to_ins_code[__seq_key]
                                                            break

                                    else:

                                        __seq_key = next((k for k, v in auth_to_star_seq.items()
                                                          if v[0] == entity_assembly_id
                                                          and v[1] == seq_id + __offset
                                                          and v[2] == entity_id), None)
                                        if __seq_key is not None:
                                            __comp_id = __seq_key[2]
                                            if self.__reg.ccU.updateChemCompDict(comp_id):
                                                cc_type = self.__reg.ccU.lastChemCompDict['type']
                                                if self.__reg.ccU.updateChemCompDict(__comp_id):
                                                    __cc_type = self.__reg.ccU.lastChemCompDict['type']
                                                    if cc_type == __cc_type:  # DAOTHER-9198
                                                        found = True
                                                        comp_id = __seq_key[2]
                                                        _row[1], _row[2], _row[3], _row[4] =\
                                                            entity_assembly_id, entity_id, __seq_key[1], __seq_key[1]
                                                        _seq_key = (__seq_key[0], __seq_key[1])
                                                        _row[16], _row[17], _row[18], _row[19] =\
                                                            __seq_key[0], __seq_key[1], comp_id, atom_id
                                                        if has_ins_code and __seq_key in auth_to_ins_code:
                                                            _row[27] = auth_to_ins_code[__seq_key]

                                    if not found:
                                        _row[24] = 'UNMAPPED'
                                        # DAOTHER-9065
                                        if __offset != 0:
                                            _row[3] += __offset
                                            _row[4] = _row[3]
                                        elif trial == 0:
                                            reparse_request = True

                                        _seq_key = (auth_asym_id, seq_id)

                                    _index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                        coord_atom_site, _seq_key,
                                                                        comp_id, atom_id, loop, idx)
                                    reparse_request |= reparse

                            if not resolved and seq_id is not None and has_coordinate:

                                can_auth_asym_id_mapping_failed = True  # DAOTHER-9158

                                def test_seq_id_offset_as_is(lp, index, _row, _idx, chain_id, seq_id, comp_id, offset):
                                    _resolved = _reparse = False
                                    _index, _seq_id = index, seq_id

                                    auth_asym_id, auth_seq_id, label_seq_id = get_label_seq_scheme(chain_id, seq_id + offset)
                                    if None not in (auth_asym_id, auth_seq_id):
                                        _resolved = True

                                        item = next((item for item in entity_assembly if item['auth_asym_id'] == auth_asym_id), None)

                                        if item is not None and poly_seq is not None and any(True for _ps in poly_seq_common
                                                                                             if _ps['chain_id'] == chain_id
                                                                                             and label_seq_id in _ps['seq_id']):
                                            entity_assembly_id = item['entity_assembly_id']
                                            entity_id = item['entity_id']

                                            seq_key = next((k for k, v in auth_to_star_seq.items()
                                                            if k[0] == auth_asym_id and k[1] == auth_seq_id
                                                            and v[0] == entity_assembly_id and v[2] == entity_id), None)

                                            if seq_key is not None:
                                                _, _label_seq_id, _, _ = auth_to_star_seq[seq_key]

                                                if entity_id not in label_seq_id_offset_for_extended\
                                                   or _label_seq_id - label_seq_id == label_seq_id_offset_for_extended[entity_id]:
                                                    seq_id += (label_seq_id - auth_seq_id)
                                                    seq_id += (_label_seq_id - label_seq_id)

                                                    if entity_id not in label_seq_id_offset_for_extended:
                                                        label_seq_id_offset_for_extended[entity_id] = _label_seq_id - label_seq_id

                                                    _row[1], _row[2] = entity_assembly_id, entity_id
                                                    _row[3] = _row[4] = seq_id

                                                    if _row[17] in EMPTY_VALUE:
                                                        _row[17] = _seq_id
                                                    if _row[18] in EMPTY_VALUE:
                                                        _row[18] = comp_id
                                                    if _row[19] in EMPTY_VALUE:
                                                        _row[19] = atom_id

                                                    _row[16] = _row[20] = auth_asym_id
                                                    if _row[21] in EMPTY_VALUE:
                                                        _row[21] = _row[17]
                                                    if _row[22] in EMPTY_VALUE:
                                                        _row[22] = _row[18]
                                                    if _row[23] in EMPTY_VALUE:
                                                        _row[23] = _row[19]
                                                    if _row[24] in EMPTY_VALUE:
                                                        _row[24] = 'UNMAPPED'

                                                    _index, _row, reparse = fill_cs_row(lp, index, _row, prefer_auth_atom_name,
                                                                                        coord_atom_site, None,
                                                                                        comp_id, atom_id, loop, _idx)
                                                    _reparse |= reparse

                                                else:
                                                    _resolved = False

                                            else:
                                                _resolved = False

                                        else:
                                            _resolved = False

                                    return _resolved, _reparse, _index, _row

                                found = False
                                for offset in range(1, GLOBAL_OFFSET_ATTEMPT):
                                    resolved, reparse, _index, __row =\
                                        test_seq_id_offset_as_is(lp, index, _row, idx, chain_id, seq_id, comp_id, offset)

                                    if resolved:
                                        index, _row = _index, __row
                                        reparse_request |= reparse
                                        break

                                    resolved, reparse, _index, __row =\
                                        test_seq_id_offset_as_is(lp, index, _row, idx, chain_id, seq_id, comp_id, -offset)

                                    if resolved:
                                        index, _row = _index, __row
                                        reparse_request |= reparse
                                        break

                        if not resolved:

                            entity_id = None
                            if (self.__reg.combined_mode or (self.__reg.bmrb_only and self.__reg.internal_mode)) and entity_id_col != -1:
                                try:
                                    entity_id = int(row[entity_id_col])
                                except (ValueError, TypeError):
                                    entity_id = None

                            if not has_coordinate:
                                seq_id = int(row[seq_id_col])

                            _row[1], _row[2], _row[5] = chain_id, entity_id, comp_id
                            _row[3] = _row[4] = seq_id

                            # DAOTHER-9065
                            if details_col != -1 and row[details_col] == 'UNMAPPED':
                                if isinstance(_row[1], int) and str(_row[1]) in seq_id_offset_for_unmapped:
                                    __offset = seq_id_offset_for_unmapped[str(_row[1])]
                                elif isinstance(_row[1], str) and _row[1] in seq_id_offset_for_unmapped:
                                    __offset = seq_id_offset_for_unmapped[_row[1]]
                                else:
                                    __offset = None

                                if __offset is not None:
                                    offset = None
                                    if isinstance(_row[17], int):
                                        offset = _row[3] - _row[17]
                                    elif isinstance(_row[17], str) and _row[17].isdigit():
                                        offset = _row[3] - int(_row[17])
                                    if offset is not None and offset != __offset:
                                        if isinstance(_row[17], int):
                                            _row[3] = _row[17] + __offset
                                            _row[4] = _row[3]
                                        else:
                                            _row[3] = int(_row[17]) + __offset
                                            _row[4] = _row[3]
                                elif trial == 0:
                                    reparse_request = True

                            atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id, atom_id)
                            if len(atom_ids) == 0 or atom_ids[0] not in self.__reg.csStat.getAllAtoms(comp_id):
                                atom_ids = self.__reg.dpV.getAtomIdListInXplor(comp_id,
                                                                               translateToStdAtomName(atom_id, comp_id,
                                                                                                      ccU=self.__reg.ccU))
                            len_atom_ids = len(atom_ids)
                            if len_atom_ids == 0 or comp_id_bmrb_only or _row[24] == 'UNMAPPED':
                                _row[6] = atom_id
                                _row[7] = 'H' if atom_id[0] in PSE_PRO_BEGIN_CODE else atom_id[0]
                                if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                    _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                            else:
                                _row[6] = atom_ids[0]
                                _row[19] = None
                                fill_auth_atom_id = _row[18] not in EMPTY_VALUE
                                if self.__reg.ccU.updateChemCompDict(comp_id):
                                    cca = next((cca for cca in self.__reg.ccU.lastAtomDictList
                                                if cca['atom_id'] == _row[6]), None)
                                    if cca is not None:
                                        _row[7] = cca['type_symbol']
                                        if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                            _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                                    else:
                                        _row[7] = 'H' if _row[6][0] in PROTON_BEGIN_CODE else atom_id[0]
                                        if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                            _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]
                                else:
                                    _row[7] = 'H' if atom_id[0] in PSE_PRO_BEGIN_CODE else atom_id[0]
                                    if _row[7] in ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS:
                                        _row[8] = ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[_row[7]][0]

                                if len_atom_ids > 1:
                                    __row = copy.copy(_row)
                                    lp.add_data(__row)

                                    for _atom_id in atom_ids[1:]:
                                        __row = copy.copy(_row)

                                        index += 1

                                        __row[0] = index
                                        __row[6] = _atom_id

                                        lp.add_data(__row)

                                    index += 1

                                    _row[6] = atom_ids[-1]

                                if fill_auth_atom_id:
                                    _row[19] = _row[6] if self.__reg.caC is not None or row[auth_atom_id_col] in EMPTY_VALUE\
                                        else row[auth_atom_id_col]

                    # DAOTHER-9065
                    if isinstance(_row[1], int) and str(_row[1]) not in seq_id_offset_for_unmapped and _row[24] in EMPTY_VALUE:
                        if isinstance(_row[3], int):
                            if isinstance(_row[17], int):
                                seq_id_offset_for_unmapped[str(_row[1])] = _row[3] - _row[17]
                            elif isinstance(_row[17], str) and _row[17].isdigit():
                                seq_id_offset_for_unmapped[str(_row[1])] = _row[3] - int(_row[17])
                    elif isinstance(_row[1], str) and _row[1] not in seq_id_offset_for_unmapped and _row[24] in EMPTY_VALUE:
                        if isinstance(_row[3], int):
                            if isinstance(_row[17], int):
                                seq_id_offset_for_unmapped[_row[1]] = _row[3] - _row[17]
                            elif isinstance(_row[17], str) and _row[17].isdigit():
                                seq_id_offset_for_unmapped[_row[1]] = _row[3] - int(_row[17])

                    if isinstance(_row[12], int):
                        comp_id = _row[5]
                        atom_id = _row[6]
                        ambig_code = _row[12]

                        if ambig_code == 0:
                            _row[12] = None

                        elif ambig_code in (2, 3):
                            _ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)
                            if _ambig_code not in (0, ambig_code):
                                if _ambig_code != 1:
                                    _row[12] = _ambig_code
                                else:
                                    ambig_code_4_test = False
                                    _chain_id = row[chain_id_col]
                                    _seq_id = row[seq_id_col]
                                    _atom_type = row[atom_id_col][0]
                                    _ambig_code = str(ambig_code)
                                    _idx = idx
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if _idx + offset < len(loop):
                                            row_ = loop.data[_idx + offset]
                                            if row_[comp_id_col] == comp_id\
                                               and row_[atom_id_col][0] == _atom_type\
                                               and str(row_[ambig_code_col]) == _ambig_code:
                                                if row_[chain_id_col] != _chain_id:
                                                    continue
                                                if row_[seq_id_col] == _seq_id:
                                                    ambig_code_4_test = True
                                                    break
                                        if _idx - offset >= 0:
                                            row_ = loop.data[_idx - offset]
                                            if row_[comp_id_col] == comp_id\
                                               and row_[atom_id_col][0] == _atom_type\
                                               and str(row_[ambig_code_col]) == _ambig_code:
                                                if row_[chain_id_col] != _chain_id:
                                                    continue
                                                if row_[seq_id_col] == _seq_id:
                                                    ambig_code_4_test = True
                                                    break
                                    if ambig_code_4_test:
                                        _row[12] = ambig_code = 4
                                        val = float(row[val_col])
                                        sig = self.__reg.ccU.getBondSignature(comp_id, atom_id)
                                        for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                            if _idx + offset < len(loop):
                                                row_ = loop.data[_idx + offset]
                                                if row_[chain_id_col] == _chain_id and row_[seq_id_col] == _seq_id\
                                                   and row_[comp_id_col] == comp_id and row_[atom_id_col][0] == _atom_type\
                                                   and abs(float(row_[val_col]) - val) < 1.0\
                                                   and self.__reg.ccU.getBondSignature(comp_id, row[atom_id_col]) == sig:
                                                    row[ambig_code_col] = 4
                                                    reparse_request = True
                                            if _idx - offset >= 0:
                                                row_ = loop.data[_idx - offset]
                                                if row_[chain_id_col] == _chain_id and row_[seq_id_col] == _seq_id\
                                                   and row_[comp_id_col] == comp_id and row_[atom_id_col][0] == _atom_type\
                                                   and abs(float(row_[val_col]) - val) < 1.0\
                                                   and self.__reg.ccU.getBondSignature(comp_id, row[atom_id_col]) == sig:
                                                    row[ambig_code_col] = 4
                                                    reparse_request = True
                                    else:
                                        _row[12] = ambig_code = 1

                        elif ambig_code == 4:
                            if not self.__reg.annotation_mode and _row[24] != 'UNMAPPED':
                                _chain_id = row[chain_id_col]
                                _seq_id = row[seq_id_col]
                                _atom_id = row[atom_id_col]
                                _atom_type = _atom_id[0]
                                _ambig_code = str(ambig_code)
                                _atom_ids_in_group = self.__reg.ccU.getProtonsInSameGroup(comp_id, _atom_id)\
                                    if _atom_type in PROTON_BEGIN_CODE else []
                                ambig_code_4_test = hetero_group_test = False
                                _idx = idx
                                for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                    if _idx + offset < len(loop):
                                        row_ = loop.data[_idx + offset]
                                        if row_[comp_id_col] == comp_id\
                                           and row_[atom_id_col][0] == _atom_type\
                                           and str(row_[ambig_code_col]) == _ambig_code:
                                            if row_[chain_id_col] != _chain_id:
                                                break
                                            if row_[seq_id_col] == _seq_id:
                                                ambig_code_4_test = True
                                                if row_[atom_id_col] not in _atom_ids_in_group:
                                                    hetero_group_test = True
                                                    break
                                    if _idx - offset >= 0:
                                        row_ = loop.data[_idx - offset]
                                        if row_[comp_id_col] == comp_id\
                                           and row_[atom_id_col][0] == _atom_type\
                                           and str(row_[ambig_code_col]) == _ambig_code:
                                            if row_[chain_id_col] != _chain_id:
                                                break
                                            if row_[seq_id_col] == _seq_id:
                                                ambig_code_4_test = True
                                                ambig_code_4_test = True
                                                if row_[atom_id_col] not in _atom_ids_in_group:
                                                    hetero_group_test = True
                                                    break
                                if not ambig_code_4_test:
                                    ambig_code_5_test = False
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if _idx + offset < len(loop):
                                            row_ = loop.data[_idx + offset]
                                            if row_[comp_id_col] == comp_id\
                                               and row_[atom_id_col][0] == _atom_type\
                                               and str(row_[ambig_code_col]) == _ambig_code:
                                                if row_[chain_id_col] != _chain_id:
                                                    break
                                                if row_[seq_id_col] == _seq_id:
                                                    break
                                                _row[12] = ambig_code = 5
                                                ambig_code_5_test = True
                                                break
                                        if _idx - offset >= 0:
                                            row_ = loop.data[_idx - offset]
                                            if row_[comp_id_col] == comp_id\
                                               and row_[atom_id_col][0] == _atom_type\
                                               and str(row_[ambig_code_col]) == _ambig_code:
                                                if row_[chain_id_col] != _chain_id:
                                                    break
                                                if row_[seq_id_col] == _seq_id:
                                                    break
                                                _row[12] = ambig_code = 5
                                                ambig_code_5_test = True
                                                break
                                    if not ambig_code_5_test:
                                        for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                            if _idx + offset < len(loop):
                                                row_ = loop.data[_idx + offset]
                                                if row_[comp_id_col] == comp_id\
                                                   and row_[atom_id_col][0] == _atom_type\
                                                   and str(row_[ambig_code_col]) == _ambig_code:
                                                    if row_[chain_id_col] != _chain_id:
                                                        _row[12] = ambig_code = 6
                                                        break
                                            if _idx - offset >= 0:
                                                row_ = loop.data[_idx - offset]
                                                if row_[comp_id_col] == comp_id\
                                                   and row_[atom_id_col][0] == _atom_type\
                                                   and str(row_[ambig_code_col]) == _ambig_code:
                                                    if row_[chain_id_col] != _chain_id:
                                                        _row[12] = ambig_code = 6
                                                        break
                                        if ambig_code == 4:
                                            _row[12] = ambig_code = 1
                                elif not hetero_group_test:
                                    _row[12] = ambig_code = 1

                        elif ambig_code == 5:
                            if not self.__reg.annotation_mode and _row[24] != 'UNMAPPED':
                                _chain_id = row[chain_id_col]
                                _seq_id = row[seq_id_col]
                                _atom_type = row[atom_id_col][0]
                                _ambig_code = str(ambig_code)
                                _idx = idx
                                ambig_code_5_test = False
                                for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                    if _idx + offset < len(loop):
                                        row_ = loop.data[_idx + offset]
                                        if row_[comp_id_col] == comp_id\
                                           and row_[atom_id_col][0] == _atom_type\
                                           and str(row_[ambig_code_col]) == _ambig_code:
                                            if row_[chain_id_col] != _chain_id:
                                                continue
                                            if row_[seq_id_col] == _seq_id:
                                                break
                                            ambig_code_5_test = True
                                            break
                                    if _idx - offset >= 0:
                                        row_ = loop.data[_idx - offset]
                                        if row_[comp_id_col] == comp_id\
                                           and row_[atom_id_col][0] == _atom_type\
                                           and str(row_[ambig_code_col]) == _ambig_code:
                                            if row_[chain_id_col] != _chain_id:
                                                continue
                                            if row_[seq_id_col] == _seq_id:
                                                break
                                            ambig_code_5_test = True
                                            break
                                if not ambig_code_5_test:
                                    for offset in range(1, PERIPH_OFFSET_ATTEMPT):
                                        if _idx + offset < len(loop):
                                            row_ = loop.data[_idx + offset]
                                            if row_[comp_id_col] == comp_id\
                                               and row_[atom_id_col][0] == _atom_type\
                                               and str(row_[ambig_code_col]) == _ambig_code:
                                                if row_[chain_id_col] != _chain_id:
                                                    _row[12] = ambig_code = 6
                                                    break
                                        if _idx - offset >= 0:
                                            row_ = loop.data[_idx - offset]
                                            if row_[comp_id_col] == comp_id\
                                               and row_[atom_id_col][0] == _atom_type\
                                               and str(row_[ambig_code_col]) == _ambig_code:
                                                if row_[chain_id_col] != _chain_id:
                                                    _row[12] = ambig_code = 6
                                                    break

                        elif ambig_code == 6:
                            if len([item for item in entity_assembly
                                    if item['entity_type'] not in ('non-polymer', 'water')]) == 1\
                               and len(entity_assembly[0]['label_asym_id'].split(',')) == 1:
                                _row[12] = ambig_code = 5

                        if ambig_code in (1, 2, 3):
                            if _row[13] is not None:
                                _row[13] = None

                        elif ambig_code in (4, 5, 6, 9):
                            has_genuine_ambig_code = True

                    if _row[8] not in EMPTY_VALUE:  # DAOTHER-9520: Atom_isotppe_number is mandatory
                        lp.add_data(_row)

                        index += 1

                if trial == 0 and len(incomplete_comp_id_annotation) > 0:  # DAOTHER-9286
                    reparse_request = True

                if not reparse_request or trial > 0:
                    break

                trial += 1

            key_items = self.__reg.key_items[file_type][content_subtype]

            conflict_id = self.__reg.nefT.get_conflict_id(lp, lp_category, key_items)[0]

            if len(conflict_id) > 0:
                conflict_id_set = self.__reg.nefT.get_conflict_id_set(lp, lp_category, key_items)[0]
                orig_atom_id_col = lp.tags.index('Original_PDB_atom_name') if 'Original_PDB_atom_name' in lp.tags else -1

                for _id in conflict_id:
                    _id_set = next(id_set for id_set in conflict_id_set if _id in id_set)

                    if len(set(str(lp.data[_id_]) for _id_ in _id_set)) == 1:
                        continue

                    # DAOTHER-9520: suppress known warnings
                    if orig_atom_id_col != -1\
                       and any(lp.data[_id1_][orig_atom_id_col] != lp.data[_id2_][orig_atom_id_col]
                               for (_id1_, _id2_) in itertools.combinations(_id_set, 2)):

                        msg = ' vs '.join([str(lp.data[_id_]).replace('None', '.').replace(',', '').replace("'", '') for _id_ in _id_set])

                        warn = f"Resolved redundancy of assigned chemical shifts ({msg}) by deletion of the latter one."

                        self.__reg.report.warning.appendDescription('redundant_data',
                                                                    {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                     'category': lp_category, 'description': warn})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateCsLoop() ++ Warning  - {warn}\n")

                for _id in conflict_id:
                    del lp.data[_id]

            if not any(True for _row in lp if _row[1] in EMPTY_VALUE or (isinstance(_row[1], str) and not _row[1].isdigit())):
                try:
                    lp.sort_rows(['Atom_ID', 'Atom_isotope_number', 'Comp_index_ID', 'Entity_assembly_ID'])
                except (TypeError, ValueError):
                    pass

            lp.renumber_rows('ID')

            if has_genuine_ambig_code:

                for _row in lp:

                    if _row[12] not in (4, 5):
                        continue

                    ambig_code = _row[12]

                    if _row[13] not in EMPTY_VALUE:
                        ambig_code = copy.copy(_row[12])
                        ambig_set_id = copy.copy(_row[13])
                        chain_id = _row[1]
                        seq_id = _row[3]
                        comp_id = _row[5]
                        atom_id = _row[6]
                        atom_type = _row[7]

                        if atom_type == 'H':
                            atom_in_same_group = self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id)

                            if not any(((ambig_code == 5 and (__row[1] != chain_id or __row[3] != seq_id))
                                        or (ambig_code == 4 and __row[6] not in atom_in_same_group))
                                       for __row in lp if __row[12] == ambig_code and __row[13] == ambig_set_id):

                                for __row in lp:
                                    if __row[12] == ambig_code and __row[13] == ambig_set_id:
                                        __row[12] = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id, None)
                                        __row[13] = None

                                if not isinstance(sf, pynmrstar.Loop)\
                                   and any(True for aux_loop in sf if aux_loop.category == aux_lp_category):

                                    aux_loop = sf.get_loop(aux_lp_category)

                                    if 'Ambiguous_shift_set_ID' in aux_loop.tags:
                                        ambig_set_id_col = aux_loop.tags.index('Ambiguous_shift_set_ID')

                                        del_row_idx = []

                                        for idx, __row in enumerate(aux_loop):
                                            if __row[ambig_set_id_col] == ambig_set_id:
                                                del_row_idx.append(idx)

                                        if len(del_row_idx) > 0:
                                            for idx in reversed(del_row_idx):
                                                del aux_loop.data[idx]

                                            if len(aux_loop) == 0:
                                                delete_aux_loop()

                has_genuine_ambig_code = False

                for _row in lp:

                    if _row[12] not in (4, 5, 6, 9):
                        continue

                    ambig_code = _row[12]
                    _ambig_code = self.__reg.csStat.getMaxAmbigCodeWoSetId(comp_id, atom_id)

                    chain_id = _row[1]
                    seq_id = _row[3]
                    comp_id = _row[5]
                    atom_id = _row[6]
                    atom_type = _row[7]

                    if ambig_code == 4:
                        _atom_id_set_w_same_ambig_code = set(_row_[6] for _row_ in lp
                                                             if _row != _row_ and _row_[1] == chain_id and _row_[3] == seq_id
                                                             and _row_[7] == atom_type and _row_[12] == ambig_code)

                        if atom_type == 'H':
                            atom_in_same_group = self.__reg.csStat.getProtonsInSameGroup(comp_id, atom_id, True)

                            if len(_atom_id_set_w_same_ambig_code - set(atom_in_same_group)) == 0:
                                if _ambig_code > 1:
                                    _row[12] = _ambig_code
                                    _row[13] = None

                        else:
                            geminal_atom = self.__reg.csStat.getGeminalAtom(comp_id, atom_id)

                            if geminal_atom is not None and len(_atom_id_set_w_same_ambig_code - set([geminal_atom])) == 0:
                                if _ambig_code > 1:
                                    _row[12] = _ambig_code
                                    _row[13] = None

                    elif ambig_code == 5:
                        _atom_id_set_w_same_ambig_code = set(_row_[6] for _row_ in lp
                                                             if _row != _row_ and _row_[1] == chain_id and _row_[3] != seq_id
                                                             and _row_[7] == atom_type and _row_[12] == ambig_code)

                        if len(_atom_id_set_w_same_ambig_code) == 0 and _ambig_code != 0:
                            _row[12] = _ambig_code
                            _row[13] = None

                    else:
                        _row[13] = None

                    if _row[12] in (4, 5):
                        has_genuine_ambig_code = True

                if has_genuine_ambig_code:

                    aux_lp = pynmrstar.Loop.from_scratch(aux_lp_category)

                    aux_items = ['Ambiguous_shift_set_ID', 'Atom_chem_shift_ID', 'Entry_ID', 'Assigned_chem_shift_list_ID']

                    aux_tags = [aux_lp_category + '.' + item for item in aux_items]

                    aux_lp.add_tag(aux_tags)

                    inter_residue_seq_id = {}

                    for _row in lp:

                        if _row[12] != 5:
                            continue

                        chain_id = _row[1]
                        seq_id = _row[3]

                        if chain_id not in inter_residue_seq_id:
                            inter_residue_seq_id[chain_id] = set()

                        inter_residue_seq_id[chain_id].add(seq_id)

                    if len(inter_residue_seq_id) > 0:

                        for k, v in inter_residue_seq_id.items():
                            if len(v) == 1:
                                chain_id = k
                                seq_id = list(v)[0]

                                for _row in lp:

                                    if _row[12] != 5:
                                        continue

                                    if _row[1] == chain_id and _row[3] == seq_id:
                                        _row[12] = 4

                    aux_index_id = 0
                    ambig_shift_set_id = {}

                    for _idx, _row in enumerate(lp):

                        if _row[12] not in (4, 5):
                            continue

                        ambig_code = _row[12]

                        chain_id = _row[1]
                        seq_id = _row[3]
                        atom_type = _row[7]

                        if ambig_code == 4:
                            key = (chain_id, str(seq_id), atom_type, ambig_code)
                        else:
                            key = (chain_id, str(inter_residue_seq_id[chain_id]), atom_type, ambig_code)

                        if key not in ambig_shift_set_id:
                            aux_index_id += 1
                            ambig_shift_set_id[key] = aux_index_id

                        lp.data[_idx][13] = ambig_shift_set_id[key]

                        _aux_row = [None] * 4
                        _aux_row[0], _aux_row[1], _aux_row[2], _aux_row[3] =\
                            ambig_shift_set_id[key], _row[0], self.__reg.entry_id, list_id

                        aux_lp.add_data(_aux_row)

                else:
                    delete_aux_loop()

            else:
                delete_aux_loop()

        del sf[loop]

        sf.add_loop(lp)

        if aux_lp is not None and len(aux_lp) > 0:
            delete_aux_loop()

            sf.add_loop(aux_lp)

        if file_type == 'nmr-star':
            val = get_first_sf_tag(sf, 'ID')
            if (isinstance(val, int) and val == list_id) or (isinstance(val, str) and val.isdigit() and int(val) == list_id):
                pass
            else:
                set_sf_tag(sf, 'ID', list_id)

        if not self.__reg.native_combined:
            self.__reg.dpV.testDataConsistencyInLoop(file_list_id, file_name, file_type, content_subtype,
                                                     sf, sf_framecode, lp_category, list_id)

        get_auth_seq_scheme.cache_clear()
        get_label_seq_scheme.cache_clear()

        return True

    def syncMrLoop(self) -> bool:
        """ Synchronize sequence scheme of restraint loop based on coordinates.
        """

        __errors = self.__reg.report.getTotalErrors()

        for fileListId in range(self.__reg.file_path_list_len):

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            if input_source_dic['content_subtype'] is None:
                continue

            for content_subtype in input_source_dic['content_subtype']:

                if content_subtype in ('entry_info', 'poly_seq', 'entity', 'chem_shift', 'chem_shift_ref'):
                    continue

                sf_category = SF_CATEGORIES[file_type][content_subtype]
                lp_category = LP_CATEGORIES[file_type][content_subtype]

                if file_type == 'nmr-star' and content_subtype == 'spectral_peak_alt':
                    lp_category = '_Assigned_peak_chem_shift'

                if self.__reg.star_data_type[fileListId] == 'Loop':
                    sf = self.__reg.star_data[fileListId]

                    self.__syncMrLoop(fileListId, file_type, content_subtype, sf, lp_category)

                elif self.__reg.star_data_type[fileListId] == 'Saveframe':
                    sf = self.__reg.star_data[fileListId]

                    self.__syncMrLoop(fileListId, file_type, content_subtype, sf, lp_category)

                else:

                    for sf in self.__reg.star_data[fileListId].get_saveframes_by_category(sf_category):

                        if not any(True for loop in sf.loops if loop.category == lp_category):
                            continue

                        self.__syncMrLoop(fileListId, file_type, content_subtype, sf, lp_category)

            return self.__reg.report.getTotalErrors() == __errors

    def __syncMrLoop(self, file_list_id: int, file_type: str, content_subtype: str,
                     sf: Union[pynmrstar.Saveframe, pynmrstar.Loop],
                     lp_category: str):
        """ Synchronize sequence scheme of restraint loop based on coordinates.
        """

        loop = sf if self.__reg.star_data_type[file_list_id] == 'Loop' else sf.get_loop(lp_category)

        if file_type == 'nef':

            chain_id_name = 'chain_code'
            seq_id_name = 'sequence_code'

            if chain_id_name in loop.tags:
                tags = [chain_id_name, seq_id_name]
                dat = loop.get_tag(tags)
                for row in dat:
                    try:
                        seq_key = (row[0], int(row[1]))
                        if seq_key in self.__reg.seq_id_map_for_remediation:
                            row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                    except (ValueError, TypeError):
                        if row[0] in self.__reg.chain_id_map_for_remediation:
                            row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

            else:
                for j in range(1, MAX_DIM_NUM_OF_SPECTRA):
                    chain_id_name = f'chain_code_{j}'
                    seq_id_name = f'sequence_code_{j}'
                    if chain_id_name not in loop.tags:
                        break
                    tags = [chain_id_name, seq_id_name]
                    dat = loop.get_tag(tags)
                    for row in dat:
                        try:
                            seq_key = (row[0], int(row[1]))
                            if seq_key in self.__reg.seq_id_map_for_remediation:
                                row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                        except (ValueError, TypeError):
                            if row[0] in self.__reg.chain_id_map_for_remediation:
                                row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

        else:

            if content_subtype == 'ccr_d_csa_restraint':
                for interaction in ['Dipole', 'CSA']:
                    for j in range(1, 3):
                        chain_id_name = f'{interaction}_entity_assembly_ID_{j}'
                        seq_id_name = f'{interaction}_comp_index_ID_{j}'
                        alt_seq_id_name = f'{interaction}_seq_ID_{j}'
                        if alt_seq_id_name in loop.tags:
                            tags = [chain_id_name, seq_id_name, alt_seq_id_name]
                            dat = loop.get_tag(tags)
                            for row in dat:
                                try:
                                    seq_key = (row[0], int(row[1]))
                                    if seq_key in self.__reg.seq_id_map_for_remediation:
                                        row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                        row[2] = row[1]
                                except (ValueError, TypeError):
                                    if row[0] in self.__reg.chain_id_map_for_remediation:
                                        row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

                        else:
                            tags = [chain_id_name, seq_id_name]
                            dat = loop.get_tag(tags)
                            for row in dat:
                                try:
                                    seq_key = (row[0], int(row[1]))
                                    if seq_key in self.__reg.seq_id_map_for_remediation:
                                        row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                except (ValueError, TypeError):
                                    if row[0] in self.__reg.chain_id_map_for_remediation:
                                        row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

            elif content_subtype == 'ccr_dd_restraint':
                for interaction in ['Dipole_1', 'Dipole_2']:
                    for j in range(1, 3):
                        chain_id_name = f'{interaction}_entity_assembly_ID_{j}'
                        seq_id_name = f'{interaction}_comp_index_ID_{j}'
                        alt_seq_id_name = f'{interaction}_seq_ID_{j}'
                        if alt_seq_id_name in loop.tags:
                            tags = [chain_id_name, seq_id_name, alt_seq_id_name]
                            dat = loop.get_tag(tags)
                            for row in dat:
                                try:
                                    seq_key = (row[0], int(row[1]))
                                    if seq_key in self.__reg.seq_id_map_for_remediation:
                                        row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                        row[2] = row[1]
                                except (ValueError, TypeError):
                                    if row[0] in self.__reg.chain_id_map_for_remediation:
                                        row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

                        else:
                            tags = [chain_id_name, seq_id_name]
                            dat = loop.get_tag(tags)
                            for row in dat:
                                try:
                                    seq_key = (row[0], int(row[1]))
                                    if seq_key in self.__reg.seq_id_map_for_remediation:
                                        row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                except (ValueError, TypeError):
                                    if row[0] in self.__reg.chain_id_map_for_remediation:
                                        row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

            else:
                chain_id_name = 'Entity_assembly_ID'
                seq_id_name = 'Comp_index_ID'
                alt_seq_id_name = 'Seq_ID'

                if chain_id_name in loop.tags:
                    if alt_seq_id_name in loop.tags:
                        tags = [chain_id_name, seq_id_name, alt_seq_id_name]
                        dat = loop.get_tag(tags)
                        for row in dat:
                            try:
                                seq_key = (row[0], int(row[1]))
                                if seq_key in self.__reg.seq_id_map_for_remediation:
                                    row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                    row[2] = row[1]
                            except (ValueError, TypeError):
                                if row[0] in self.__reg.chain_id_map_for_remediation:
                                    row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

                    else:
                        tags = [chain_id_name, seq_id_name]
                        dat = loop.get_tag(tags)
                        for row in dat:
                            try:
                                seq_key = (row[0], int(row[1]))
                                if seq_key in self.__reg.seq_id_map_for_remediation:
                                    row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                            except (ValueError, TypeError):
                                if row[0] in self.__reg.chain_id_map_for_remediation:
                                    row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

                else:
                    for j in range(1, MAX_DIM_NUM_OF_SPECTRA):
                        chain_id_name = f'Entity_assembly_ID_{j}'
                        seq_id_name = f'Comp_index_ID_{j}'
                        alt_seq_id_name = f'Seq_ID_{j}'
                        if chain_id_name not in loop.tags:
                            break
                        if alt_seq_id_name in loop.tags:
                            tags = [chain_id_name, seq_id_name, alt_seq_id_name]
                            dat = loop.get_tag(tags)
                            for row in dat:
                                try:
                                    seq_key = (row[0], int(row[1]))
                                    if seq_key in self.__reg.seq_id_map_for_remediation:
                                        row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                        row[2] = row[1]
                                except (ValueError, TypeError):
                                    if row[0] in self.__reg.chain_id_map_for_remediation:
                                        row[0] = self.__reg.chain_id_map_for_remediation[row[0]]
                        else:
                            tags = [chain_id_name, seq_id_name]
                            dat = loop.get_tag(tags)
                            for row in dat:
                                try:
                                    seq_key = (row[0], int(row[1]))
                                    if seq_key in self.__reg.seq_id_map_for_remediation:
                                        row[0], row[1] = self.__reg.seq_id_map_for_remediation[seq_key]
                                except (ValueError, TypeError):
                                    if row[0] in self.__reg.chain_id_map_for_remediation:
                                        row[0] = self.__reg.chain_id_map_for_remediation[row[0]]

    def remediateRawTextPk(self, src_sf: pynmrstar.Saveframe, file_type: str, data_file_name: str, text_data: str,
                           reserved_list_ids: List[int]) -> bool:
        """ Remediate raw text data in saveframe of spectral peak list (for NMR data remediation upgrade to Phase 2).
        """

        __errors = self.__reg.report.getTotalErrors()

        input_source = self.__reg.report.input_sources[0]

        content_subtype = 'spectral_peak'

        sf_framecode = get_first_sf_tag(src_sf, 'Sf_framecode')

        poly_seq_set = []

        if self.__reg.list_id_counter is None:
            self.__reg.list_id_counter = {}

        pk_sf_dict_holder = {}

        proc_nmr_ext_poly_seq = False

        if self.__reg.nmr_ext_poly_seq is None and not self.__reg.bmrb_only or not self.__reg.internal_mode:
            proc_nmr_ext_poly_seq = True

            self.__reg.nmr_ext_poly_seq = []

            input_source_dic = input_source.get()

            nmr_poly_seq = input_source_dic['polymer_sequence']
            cif_poly_seq = self.__reg.caC['polymer_sequence']

            seq_align, _ = alignPolymerSequence(self.__reg.pA, cif_poly_seq, nmr_poly_seq)
            chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, 'nmr-star', cif_poly_seq, nmr_poly_seq, seq_align)

            if chain_assign is not None:

                for ca in chain_assign:
                    ref_chain_id = ca['ref_chain_id']
                    test_chain_id = ca['test_chain_id']

                    sa = next(sa for sa in seq_align
                              if sa['ref_chain_id'] == ref_chain_id
                              and sa['test_chain_id'] == test_chain_id)

                    if sa['conflict'] > 0 or sa['unmapped'] == 0:
                        continue

                    ps1 = next(ps for ps in nmr_poly_seq if ps['chain_id'] == test_chain_id)
                    ps2 = next(ps for ps in cif_poly_seq if ps['auth_chain_id'] == ref_chain_id)

                    self.__reg.pA.setReferenceSequence(ps1['comp_id'], 'REF' + test_chain_id)
                    self.__reg.pA.addTestSequence(ps2['comp_id'], test_chain_id)
                    self.__reg.pA.doAlign()

                    myAlign = self.__reg.pA.getAlignment(test_chain_id)

                    length = len(myAlign)

                    _matched, unmapped, conflict, offset_1, offset_2 = getScoreOfSeqAlign(myAlign)

                    if conflict == 0 and unmapped > 0:

                        nmr_seq_ids, cif_auth_seq_ids = [], []

                        for i in range(length):
                            if str(myAlign[i][0]) != '.' and i < len(ps1['seq_id']):
                                nmr_seq_ids.append(ps1['seq_id'][i])
                            else:
                                nmr_seq_ids.append(None)

                        for i in range(length):
                            if str(myAlign[i][1]) != '.' and i < len(ps2['seq_id']):
                                cif_auth_seq_ids.append(ps2['auth_seq_id'][i])
                            else:
                                cif_auth_seq_ids.append(None)

                        for i in range(length):
                            nmr_comp_id, cif_comp_id = str(myAlign[i][0]), str(myAlign[i][1])

                            if nmr_comp_id == cif_comp_id:
                                continue

                            if cif_comp_id == '.' and nmr_comp_id != '.':
                                nmr_seq_id = nmr_seq_ids[i] - offset_1 if nmr_seq_ids[i] is not None else None
                                if nmr_seq_id is not None:
                                    offset = None
                                    for _offset in range(1, 20):
                                        if i + _offset < length:
                                            _myPr = myAlign[i + _offset]
                                            if _myPr[0] == _myPr[1]:
                                                offset = _offset
                                                break
                                        if i - _offset >= 0:
                                            _myPr = myAlign[i - _offset]
                                            if _myPr[0] == _myPr[1]:
                                                offset = -_offset
                                                break

                                    if offset is not None and cif_auth_seq_ids[i + offset] is not None:
                                        cif_auth_seq_id = cif_auth_seq_ids[i + offset] - offset - offset_2
                                        self.__reg.nmr_ext_poly_seq.append({'auth_chain_id': ps2['auth_chain_id'],
                                                                            'auth_seq_id': cif_auth_seq_id,
                                                                            'auth_comp_id': nmr_comp_id})

        suspended_errors_for_lazy_eval = []

        def consume_suspended_message():

            if len(suspended_errors_for_lazy_eval) > 0:
                for msg in suspended_errors_for_lazy_eval:
                    for k, v in msg.items():
                        self.__reg.report.error.appendDescription(k, v)
                suspended_errors_for_lazy_eval.clear()

        def deal_pea_warn_message(file_name, listener):

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'sf_framecode': sf_framecode, 'description': warn, 'inheritable': True}

                    if warn.startswith('[Concatenated sequence]'):
                        self.__reg.report.warning.appendDescription('concatenated_sequence', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch]'):
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {warn}\n")

                    elif warn.startswith('[Atom not found]'):
                        if not self.__reg.remediation_mode or 'Macromolecules page' not in warn:
                            consume_suspended_message()

                            self.__reg.report.warning.appendDescription('assigned_peak_atom_not_found', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")
                        else:
                            self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Hydrogen not instantiated]'):
                        if self.__reg.remediation_mode:
                            pass
                        else:
                            consume_suspended_message()

                        self.__reg.report.warning.appendDescription('hydrogen_not_instantiated', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Coordinate issue]'):
                        # consume_suspended_message()

                        self.__reg.report.warning.appendDescription('coordinate_issue', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Invalid atom nomenclature]'):
                        consume_suspended_message()

                        # DAOTHER-8905: change warning level from 'invalid_atom_nomenclature' error to 'atom_nomenclature_mismatch' warning
                        # because we accept atom nomenclature provided by depositor for peak list
                        self.__reg.report.warning.appendDescription('atom_nomenclature_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        # consume_suspended_message()

                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch warning]'):
                        self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                        if SEQ_MISMATCH_WARNING_PAT.match(warn):
                            g = SEQ_MISMATCH_WARNING_PAT.search(warn).groups()
                            d = {'auth_chain_id': g[2],
                                 'auth_seq_id': int(g[0]),
                                 'auth_comp_id': g[1]}
                            if d not in self.__reg.nmr_ext_poly_seq:
                                self.__reg.nmr_ext_poly_seq.append(d)

                    elif warn.startswith('[Inconsistent peak assignment]'):
                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Conflicted peak assignment]'):
                        self.__reg.report.warning.appendDescription('conflicted_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Missing data]'):
                        if (self.__reg.remediation_mode or self.__reg.internal_mode) and not self.__reg.conversion_server:
                            pass
                        else:
                            self.__reg.report.error.appendDescription('missing_mandatory_item', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {warn}\n")

                    elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('anomalous_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ ValueError  - {warn}\n")

                    elif warn.startswith('[Range value warning]')\
                            or (warn.startswith('[Range value error]') and self.__reg.remediation_mode):
                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Warning  - {warn}\n")

                    else:
                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.remediateRawTextPk() ++ KeyError  - " + warn)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ KeyError  - {warn}\n")

        def deal_pea_warn_message_for_lazy_eval(file_name, listener):

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'sf_framecode': sf_framecode, 'description': warn, 'inheritable': True}

                    if warn.startswith('[Sequence mismatch]'):
                        suspended_errors_for_lazy_eval.append({'sequence_mismatch': msg_dict})

                    # elif warn.startswith('[Atom not found]'):
                    #     if not self.__reg.remediation_mode or 'Macromolecules page' not in warn:
                    #         suspended_errors_for_lazy_eval.append({'atom_not_found': msg_dict})

                    # elif warn.startswith('[Hydrogen not instantiated]'):
                    #     if self.__reg.remediation_mode:
                    #         pass
                    #     else:
                    #         suspended_errors_for_lazy_eval.append({'hydrogen_not_instantiated': msg_dict})

                    # elif warn.startswith('[Coordinate issue]'):
                    #     suspended_errors_for_lazy_eval.append({'coordinate_issue': msg_dict})

                    # elif warn.startswith('[Invalid atom nomenclature]'):
                    #     suspended_errors_for_lazy_eval.append({'invalid_atom_nomenclature': msg_dict})

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        suspended_errors_for_lazy_eval.append({'invalid_data': msg_dict})

                    # elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                    #     suspended_errors_for_lazy_eval.append({'anomalous_data': msg_dict})

        if file_type == 'nm-pea-ari':
            reader = AriaPKReader(self.__reg.verbose, self.__reg.log,
                                  self.__reg.representative_model_id,
                                  self.__reg.representative_alt_id,
                                  self.__reg.mr_atom_name_mapping,
                                  self.__reg.cR, self.__reg.caC,
                                  self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = AriaPKReader(self.__reg.verbose, self.__reg.log,
                                          self.__reg.representative_model_id,
                                          self.__reg.representative_alt_id,
                                          self.__reg.mr_atom_name_mapping,
                                          self.__reg.cR, self.__reg.caC,
                                          self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                          reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (ARIA) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-bar':
            reader = BarePKReader(self.__reg.verbose, self.__reg.log,
                                  self.__reg.representative_model_id,
                                  self.__reg.representative_alt_id,
                                  self.__reg.mr_atom_name_mapping,
                                  self.__reg.cR, self.__reg.caC,
                                  self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = BarePKReader(self.__reg.verbose, self.__reg.log,
                                          self.__reg.representative_model_id,
                                          self.__reg.representative_alt_id,
                                          self.__reg.mr_atom_name_mapping,
                                          self.__reg.cR, self.__reg.caC,
                                          self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                          reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (Bare WSV/TSV) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-ccp':
            reader = CcpnPKReader(self.__reg.verbose, self.__reg.log,
                                  self.__reg.representative_model_id,
                                  self.__reg.representative_alt_id,
                                  self.__reg.mr_atom_name_mapping,
                                  self.__reg.cR, self.__reg.caC,
                                  self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = CcpnPKReader(self.__reg.verbose, self.__reg.log,
                                          self.__reg.representative_model_id,
                                          self.__reg.representative_alt_id,
                                          self.__reg.mr_atom_name_mapping,
                                          self.__reg.cR, self.__reg.caC,
                                          self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                          reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (CCPN) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-oli':
            reader = OliviaPKReader(self.__reg.verbose, self.__reg.log,
                                    self.__reg.representative_model_id,
                                    self.__reg.representative_alt_id,
                                    self.__reg.mr_atom_name_mapping,
                                    self.__reg.cR, self.__reg.caC,
                                    self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = OliviaPKReader(self.__reg.verbose, self.__reg.log,
                                            self.__reg.representative_model_id,
                                            self.__reg.representative_alt_id,
                                            self.__reg.mr_atom_name_mapping,
                                            self.__reg.cR, self.__reg.caC,
                                            self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                            reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (OLIVIA) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-pip':
            reader = NmrPipePKReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = NmrPipePKReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (NMRPIPE) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-pon':
            reader = PonderosaPKReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = PonderosaPKReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (PONDEROSA) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-spa':
            reader = SparkyPKReader(self.__reg.verbose, self.__reg.log,
                                    self.__reg.representative_model_id,
                                    self.__reg.representative_alt_id,
                                    self.__reg.mr_atom_name_mapping,
                                    self.__reg.cR, self.__reg.caC,
                                    self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = SparkyPKReader(self.__reg.verbose, self.__reg.log,
                                            self.__reg.representative_model_id,
                                            self.__reg.representative_alt_id,
                                            self.__reg.mr_atom_name_mapping,
                                            self.__reg.cR, self.__reg.caC,
                                            self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                            reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (SPARKY) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-sps':
            reader = SparkySPKReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = SparkySPKReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (SPARKY) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-top':
            reader = TopSpinPKReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id)

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = TopSpinPKReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id)

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (TOPSPIN) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-vie':
            reader = NmrViewPKReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = NmrViewPKReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (NMRVIEW) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-vnm':
            reader = VnmrPKReader(self.__reg.verbose, self.__reg.log,
                                  self.__reg.representative_model_id,
                                  self.__reg.representative_alt_id,
                                  self.__reg.mr_atom_name_mapping,
                                  self.__reg.cR, self.__reg.caC,
                                  self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = VnmrPKReader(self.__reg.verbose, self.__reg.log,
                                          self.__reg.representative_model_id,
                                          self.__reg.representative_alt_id,
                                          self.__reg.mr_atom_name_mapping,
                                          self.__reg.cR, self.__reg.caC,
                                          self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                          reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (VNMR) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-xea':
            reader = XeasyPKReader(self.__reg.verbose, self.__reg.log,
                                   self.__reg.representative_model_id,
                                   self.__reg.representative_alt_id,
                                   self.__reg.mr_atom_name_mapping,
                                   self.__reg.cR, self.__reg.caC,
                                   self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                   None)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id,
                                          csLoops=self.__reg.lp_data['chem_shift'])

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None and listener.warningMessage is not None and len(listener.warningMessage) > 0:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = XeasyPKReader(self.__reg.verbose, self.__reg.log,
                                           self.__reg.representative_model_id,
                                           self.__reg.representative_alt_id,
                                           self.__reg.mr_atom_name_mapping,
                                           self.__reg.cR, self.__reg.caC,
                                           self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                           None,
                                           reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id,
                                                  csLoops=self.__reg.lp_data['chem_shift'])

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (XEASY) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        elif file_type == 'nm-pea-xwi':
            reader = XwinNmrPKReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
            reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
            reader.setInternalMode(self.__reg.internal_mode)

            _list_id_counter = copy.copy(self.__reg.list_id_counter)

            listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                          createSfDict=True, originalFileName=data_file_name,
                                          listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                          entryId=self.__reg.entry_id)

            if listener is not None:
                reasons = listener.getReasonsForReparsing()

                if reasons is not None:
                    deal_pea_warn_message_for_lazy_eval(data_file_name, listener)

                    reader = XwinNmrPKReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    listener, _, _ = reader.parse(text_data, self.__reg.cifPath, isFilePath=False,
                                                  createSfDict=True, originalFileName=data_file_name,
                                                  listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                  entryId=self.__reg.entry_id)

                deal_pea_warn_message(data_file_name, listener)

                poly_seq = listener.getPolymerSequence()
                if poly_seq is not None:
                    input_source.setItemValue('polymer_sequence', poly_seq)
                    poly_seq_set.append(poly_seq)

                seq_align = listener.getSequenceAlignment()
                if seq_align is not None:
                    self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                if len(listener.getContentSubtype()) == 0:
                    err = f"Failed to validate spectral peak list file (XWINNMR) {data_file_name!r}."

                    self.__reg.report.error.appendDescription('internal_error',
                                                              f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - " + err)

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.remediateRawTextPk() ++ Error  - {err}\n")

                self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                if sf_dict is not None:
                    for k, v in sf_dict.items():
                        content_subtype = contentSubtypeOf(k[0])
                        if content_subtype not in pk_sf_dict_holder:
                            pk_sf_dict_holder[content_subtype] = []
                        for sf in v:
                            if sf not in pk_sf_dict_holder[content_subtype]:
                                pk_sf_dict_holder[content_subtype].append(sf)

        if content_subtype in pk_sf_dict_holder:

            master_entry = self.__reg.star_data[0]

            master_entry.remove_saveframe(sf_framecode)

            for sf in pk_sf_dict_holder[content_subtype]:

                cs_list = get_first_sf_tag(sf['saveframe'], 'Chemical_shift_list')

                if cs_list in EMPTY_VALUE:
                    sf_category = SF_CATEGORIES['nmr-star']['chem_shift']
                    cs_sf_list = master_entry.get_saveframes_by_category(sf_category)
                    if len(cs_sf_list) == 1:
                        set_sf_tag(sf['saveframe'], 'Chemical_shift_list', get_first_sf_tag(cs_sf_list[0], 'Sf_framecode'))

                master_entry.add_saveframe(sf['saveframe'])

        if len(poly_seq_set) > 1:

            poly_seq_rst = None
            for idx, poly_seq in enumerate(poly_seq_set):
                if idx == 0:
                    poly_seq_rst = poly_seq
                    continue
                for ps in poly_seq:
                    chain_id = ps['chain_id']
                    for seq_id, comp_id in zip(ps['seq_id'], ps['comp_id']):
                        updatePolySeqRst(poly_seq_rst, chain_id, seq_id, comp_id)

            poly_seq_model = self.__reg.caC['polymer_sequence']

            sortPolySeqRst(poly_seq_rst)

            file_type = 'nm-pea-any'

            seq_align, _ = alignPolymerSequence(self.__reg.pA, poly_seq_model, poly_seq_rst, conservative=False)
            chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type, poly_seq_model, poly_seq_rst, seq_align)

            if chain_assign is not None:

                if len(poly_seq_model) == len(poly_seq_rst):

                    chain_mapping = {}

                    for ca in chain_assign:
                        ref_chain_id = ca['ref_chain_id']
                        test_chain_id = ca['test_chain_id']

                        if ref_chain_id != test_chain_id:
                            chain_mapping[test_chain_id] = ref_chain_id

                    if len(chain_mapping) == len(poly_seq_model):

                        for ps in poly_seq_rst:
                            if ps['chain_id'] in chain_mapping:
                                ps['chain_id'] = chain_mapping[ps['chain_id']]

                        seq_align, _ = alignPolymerSequence(self.__reg.pA, poly_seq_model, poly_seq_rst, conservative=False)
                        chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type,
                                                                poly_seq_model, poly_seq_rst, seq_align)

                    trimSequenceAlignment(seq_align, chain_assign)

            input_source.setItemValue('polymer_sequence', poly_seq_rst)

            self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

        if proc_nmr_ext_poly_seq and len(self.__reg.nmr_ext_poly_seq) > 0:
            entity_assembly = self.__reg.caC['entity_assembly']
            auth_chain_ids = list(set(d['auth_chain_id'] for d in self.__reg.nmr_ext_poly_seq))
            for auth_chain_id in auth_chain_ids:
                item = next(item for item in entity_assembly if auth_chain_id in item['auth_asym_id'].split(','))
                if item['entity_type'] == 'polymer':
                    poly_type = item['entity_poly_type']
                    if poly_type.startswith('polypeptide'):
                        unknown_residue = 'UNK'
                    elif any(True for comp_id in item['comp_id_set'] if comp_id in ('DA', 'DC', 'DG', 'DT'))\
                            and any(True for comp_id in item['comp_id_set'] if comp_id in ('A', 'C', 'G', 'U')):
                        unknown_residue = 'DN'
                    elif poly_type == 'polydeoxyribonucleotide':
                        unknown_residue = 'DN'
                    elif poly_type == 'polyribonucleotide':
                        unknown_residue = 'N'
                    else:
                        continue
                    ps = next(ps for ps in self.__reg.caC['polymer_sequence'] if ps['auth_chain_id'] == auth_chain_id)
                    auth_seq_ids = [d['auth_seq_id'] for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == auth_chain_id]
                    auth_seq_ids.extend(list(filter(None, ps['auth_seq_id'])))
                    min_auth_seq_id = min(auth_seq_ids)
                    max_auth_seq_id = max(auth_seq_ids)
                    for auth_seq_id in range(min_auth_seq_id, max_auth_seq_id + 1):
                        if auth_seq_id not in ps['auth_seq_id']\
                           and not any(True for d in self.__reg.nmr_ext_poly_seq
                                       if d['auth_chain_id'] == auth_chain_id and d['auth_seq_id'] == auth_seq_id):
                            self.__reg.nmr_ext_poly_seq.append({'auth_chain_id': auth_chain_id,
                                                                'auth_seq_id': auth_seq_id,
                                                                'auth_comp_id': unknown_residue})

            self.__reg.nmr_ext_poly_seq = sorted(self.__reg.nmr_ext_poly_seq, key=itemgetter('auth_chain_id', 'auth_seq_id'))

        return self.__reg.report.getTotalErrors() == __errors

    def remediateSpectralPeakListSaveframe(self, star_data: pynmrstar.Entry):
        """ Remediate spectral peak list saveframe
        """

        if not self.__reg.bmrb_only:
            return

        sf_category = 'spectral_peak_list'

        sf_name_map = {}
        for idx, sf in enumerate(star_data.get_saveframes_by_category(sf_category), start=1):
            tagNames = [t[0] for t in sf.tags]
            if 'Text_data' in tagNames and get_first_sf_tag(sf, 'Text_data') in EMPTY_VALUE:
                # sf.remove_tag('Text_data')
                if 'Text_data_format' in tagNames:
                    set_sf_tag(sf, 'Text_data_format', '.')
                    # sf.remove_tag('Text_data_format')
            sf_id = get_first_sf_tag(sf, 'ID')
            if isinstance(sf_id, str):
                sf_id = int(sf_id) if len(sf_id) > 0 else idx
            sf_name_map[sf.name] = sf_id

        if not all(sf_name.split('_')[-1] == str(sf_id) for sf_name, sf_id in sf_name_map.items()):
            for sf in star_data.get_saveframes_by_category(sf_category):
                prefix_sf_name = '_'.join(sf.name.split('_')[:-1])
                sf.name = f'{prefix_sf_name}_{sf_name_map[sf.name]}'
                set_sf_tag(sf, 'Sf_framecode', sf.name)

        truncated = False
        for sf in star_data.get_saveframes_by_category(sf_category):

            lp_category = '_Peak_row_format'

            try:

                sf.get_loop(lp_category)
                continue

            except KeyError:

                lp_category = '_Peak_char'

                try:

                    sf.get_loop(lp_category)
                    continue

                except KeyError:
                    pass

            if get_first_sf_tag(sf, 'Text_data') in EMPTY_VALUE:
                star_data.remove_saveframe(sf.name)
                truncated = True

        if truncated:

            total_peak_lists = len(star_data.get_saveframes_by_category(sf_category))

            if total_peak_lists == 0:

                sf_category = 'entry_interview'

                if sf_category in self.__reg.sf_category_list:

                    int_sf = star_data.get_saveframes_by_category(sf_category)[0]

                    set_sf_tag(int_sf, 'Spectral_peak_lists', '.')

            sf_category = 'entry_information'

            if sf_category in self.__reg.sf_category_list:

                inf_sf = star_data.get_saveframes_by_category(sf_category)[0]

                lp_category = '_Data_set'

                try:

                    lp = inf_sf.get_loop(lp_category)

                    type_col = lp.tags.index('Type')
                    count_col = lp.tags.index('Count')

                    for idx, row in enumerate(lp):

                        if row[type_col] != 'spectral_peak_list':
                            continue

                        if total_peak_lists == 0:
                            del lp.data[idx]

                        else:
                            lp.data[idx][count_col] = total_peak_lists

                        break

                except KeyError:
                    pass

    def remediateRdcLoop(self, file_type: str, loop: pynmrstar.Loop) -> bool:  # pylint: disable=no-self-use
        """ Remediate RDC target value due to the known OneDep bug, if required.
        """

        modified = False

        item_names = ITEM_NAMES_IN_RDC_LOOP[file_type]

        tags = [item_names['lower_limit'], item_names['target_value'], item_names['upper_limit']]

        if set(tags) & set(loop.tags) == set(tags):
            val_col = loop.tags.index(item_names['target_value'])

            dat = loop.get_tag(tags)

            for idx, row in enumerate(dat):

                if any(True for col in row if col in EMPTY_VALUE):
                    continue

                lower_limit, target_value, upper_limit = float(row[0]), float(row[1]), float(row[2])

                if abs((lower_limit + upper_limit) / 2.0 + target_value) < 0.01:
                    loop.data[idx][val_col] = str(-target_value)
                    modified = True

        return modified

    def __mergeStrPk(self) -> bool:
        """ Merge spectral peak lists in NMR-STAR restraint files.
        """

        if self.__reg.combined_mode:
            return True

        if MR_FILE_PATH_LIST_KEY not in self.__reg.inputParamDict:
            return True

        src_id = self.__reg.report.getInputSourceIdOfCoord()

        if src_id < 0:
            return False

        if self.__reg.pk_sf_holder is None:
            self.__reg.pk_sf_holder = []

        list_id = len(self.__reg.pk_sf_holder) + 1

        master_entry = self.__reg.star_data[0]

        for fileListId in range(self.__reg.cs_file_path_list_len, self.__reg.file_path_list_len):

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']
            content_subtype = input_source_dic['content_subtype']

            if file_type != 'nmr-star':
                continue

            if input_source_dic['content_subtype'] is None:
                continue

            for content_subtype in PK_CONTENT_SUBTYPES:

                if content_subtype not in input_source_dic['content_subtype']:
                    continue

                sf_category = SF_CATEGORIES[file_type][content_subtype]

                if self.__reg.bmrb_only and self.__reg.internal_mode and self.__reg.nmr_cif_sf_category_list is not None:
                    if sf_category in self.__reg.nmr_cif_sf_category_list:
                        continue

                if self.__reg.star_data_type[fileListId] == 'Loop':
                    pass

                elif self.__reg.star_data_type[fileListId] == 'Saveframe':
                    sf = self.__reg.star_data[fileListId]

                    self.__reg.c2S.set_entry_id(sf, self.__reg.entry_id)
                    self.__reg.c2S.set_local_sf_id(sf, list_id)

                    master_entry.add_saveframe(sf)

                    self.__reg.pk_sf_holder.append({'file_type': 'nmr-star', 'saveframe': sf})

                    list_id += 1

                else:

                    for sf in self.__reg.star_data[fileListId].get_saveframes_by_category(sf_category):

                        self.__reg.c2S.set_entry_id(sf, self.__reg.entry_id)
                        self.__reg.c2S.set_local_sf_id(sf, list_id)

                        master_entry.add_saveframe(sf)

                        self.__reg.pk_sf_holder.append({'file_type': 'nmr-star', 'saveframe': sf})

                        list_id += 1

        return True

    def __mergeAnyPkAsIs(self) -> bool:
        """ Merge spectral peak list file(s) in any plain text format (file type: nm-pea-any) into a single NMR-STAR file as-is.
        """

        if self.__reg.combined_mode:
            return True

        if AR_FILE_PATH_LIST_KEY not in self.__reg.inputParamDict:
            return True

        if self.__reg.pk_sf_holder is None:
            self.__reg.pk_sf_holder = []

        fileListId = self.__reg.file_path_list_len

        list_id = len(self.__reg.pk_sf_holder) + 1

        master_entry = self.__reg.star_data[0]

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_name = input_source_dic['file_name']
            file_type = input_source_dic['file_type']

            fileListId += 1

            if file_type != 'nm-pea-any':
                continue

            original_file_name = None
            if 'original_file_name' in input_source_dic:
                if input_source_dic['original_file_name'] is not None:
                    original_file_name = os.path.basename(input_source_dic['original_file_name'])

            file_path = ar['file_name']

            try:

                with open(file_path, 'r', encoding='utf-8') as ifh:
                    ifh.read()

            except UnicodeDecodeError:  # catch exception due to binary format (DAOTHER-9425)
                continue

            if get_chem_shift_format(file_path) is not None:

                err = "The spectral peak list file includes assigned chemical shifts."

                self.__reg.report.error.appendDescription('content_mismatch',
                                                          {'file_name': file_name, 'description': err})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.__mergeAnyPkAsIs() ++ Error  - {err}\n")

                continue

            content_subtype = 'spectral_peak'

            sf_category = SF_CATEGORIES['nmr-star'][content_subtype]
            sf_framecode = f'spectral_peak_list_{list_id}'

            if self.__reg.bmrb_only and self.__reg.internal_mode and self.__reg.nmr_cif_sf_category_list is not None:
                if sf_category in self.__reg.nmr_cif_sf_category_list:
                    continue

            try:

                sf = master_entry.get_saveframe_by_name(sf_framecode)
                text_data = get_first_sf_tag(sf, 'Text_data')

                if any(True for loop in sf.loops if loop.category in ('_Peak_row_format', '_Peak_general_char'))\
                        or text_data not in EMPTY_VALUE:

                    list_id += 1

                    continue

                file_format = get_peak_list_format(file_path, False)
                dimensions = get_number_of_dimensions_of_peak_list(file_path, file_format)

                set_sf_tag(sf, 'Number_of_spectral_dimensions', dimensions)

                _sf_id = _sf_framecode = None
                _sf_category = SF_CATEGORIES['nmr-star']['chem_shift']
                if len(master_entry.get_saveframes_by_category(_sf_category)) == 1:
                    _sf = master_entry.get_saveframes_by_category(_sf_category)[0]
                    _sf_id = get_first_sf_tag(_sf, 'ID')
                    _sf_framecode = f"${get_first_sf_tag(_sf, 'Sf_framecode')}"

                set_sf_tag(sf, 'Assigned_chem_shift_list_ID', _sf_id)
                set_sf_tag(sf, 'Assigned_chem_shift_list_label', _sf_framecode)

                set_sf_tag(sf, 'Text_data_format', file_format if file_format is not None else 'unknown')

                with open(file_path, 'r', encoding='ascii', errors='ignore') as ifh:
                    set_sf_tag(sf, 'Text_data', ifh.read())

                list_id += 1

            except KeyError:

                sf = pynmrstar.Saveframe.from_scratch(sf_framecode, SF_TAG_PREFIXES['nmr-star'][content_subtype])
                sf.add_tag('Sf_category', sf_category)
                sf.add_tag('Sf_framecode', sf_framecode)
                sf.add_tag('Entry_ID', self.__reg.entry_id)
                sf.add_tag('ID', list_id)
                sf.add_tag('Data_file_name', original_file_name if original_file_name is not None else file_name)

                _sf_id = _sf_framecode = None
                _sf_category = 'sample'
                if len(master_entry.get_saveframes_by_category(_sf_category)) == 1:
                    _sf = master_entry.get_saveframes_by_category(_sf_category)[0]
                    _sf_id = get_first_sf_tag(_sf, 'ID')
                    _sf_framecode = f"${get_first_sf_tag(_sf, 'Sf_framecode')}"

                sf.add_tag('Sample_ID', _sf_id)
                sf.add_tag('Sample_label', _sf_framecode)

                _sf_id = _sf_framecode = None
                _sf_category = 'sample_conditions'
                if len(master_entry.get_saveframes_by_category(_sf_category)) == 1:
                    _sf = master_entry.get_saveframes_by_category(_sf_category)[0]
                    _sf_id = get_first_sf_tag(_sf, 'ID')
                    _sf_framecode = f"${get_first_sf_tag(_sf, 'Sf_framecode')}"

                sf.add_tag('Sample_condition_list_ID', _sf_id)
                sf.add_tag('Sample_condition_list_label', _sf_framecode)

                sf.add_tag('Experiment_ID', None)
                sf.add_tag('Experiment_name', None)
                sf.add_tag('Experiment_class', None)
                sf.add_tag('Experiment_type', None)

                file_format = get_peak_list_format(file_path, False)
                dimensions = get_number_of_dimensions_of_peak_list(file_path, file_format)

                sf.add_tag('Number_of_spectral_dimensions', dimensions)

                cs_list = get_first_sf_tag(sf, 'Chemical_shift_list')

                if cs_list in EMPTY_VALUE:
                    sf_category = SF_CATEGORIES['nmr-star']['chem_shift']
                    cs_sf_list = master_entry.get_saveframes_by_category(sf_category)
                    if len(cs_sf_list) == 1:
                        set_sf_tag(sf, 'Chemical_shift_list', get_first_sf_tag(cs_sf_list[0], 'Sf_framecode'))

                _sf_id = _sf_framecode = None
                _sf_category = SF_CATEGORIES['nmr-star']['chem_shift']
                if len(master_entry.get_saveframes_by_category(_sf_category)) == 1:
                    _sf = master_entry.get_saveframes_by_category(_sf_category)[0]
                    _sf_id = get_first_sf_tag(_sf, 'ID')
                    _sf_framecode = f"${get_first_sf_tag(_sf, 'Sf_framecode')}"

                sf.add_tag('Assigned_chem_shift_list_ID', _sf_id)
                sf.add_tag('Assigned_chem_shift_list_label', _sf_framecode)

                sf.add_tag('Details', None)
                sf.add_tag('Text_data_format', file_format if file_format is not None else 'unknown')

                with open(file_path, 'r', encoding='ascii', errors='ignore') as ifh:
                    sf.add_tag('Text_data', ifh.read())

                master_entry.add_saveframe(sf)

                self.__reg.pk_sf_holder.append({'file_type': file_type, 'saveframe': sf})

                list_id += 1

        return True

    def validateLegacyCs(self) -> bool:
        """ Validate data content of legacy NMR chemical shift files and merge them if possible.
        """

        if self.__reg.combined_mode or not self.__reg.conversion_server:
            return True

        if AC_FILE_PATH_LIST_KEY not in self.__reg.inputParamDict:
            return True

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        has_poly_seq = has_key_value(input_source_dic, 'polymer_sequence')

        if not has_poly_seq:
            return False

        nmr_poly_seq = input_source_dic['polymer_sequence']
        entity_assembly = None

        file_type = 'nmr-star'
        content_subtype = 'chem_shift'

        sf_category = SF_CATEGORIES[file_type][content_subtype]

        _rlist_ids = []
        if len(self.__reg.star_data) > 0 and isinstance(self.__reg.star_data[0], pynmrstar.Entry):
            for idx, sf in enumerate(self.__reg.star_data[0].get_saveframes_by_category(sf_category), start=1):
                list_id = get_first_sf_tag(sf, 'ID')
                _rlist_ids.append({'list_id': int(list_id) if list_id not in EMPTY_VALUE else idx,
                                   'data_file_name': get_first_sf_tag(sf, 'Data_file_name')})
            for sf in self.__reg.star_data[0].get_saveframes_by_category('assembly'):
                try:
                    lp = sf.get_loop('_Entity_assembly')
                    has_pdb_chain_id = 'PDB_chain_ID' in lp.tags
                    if has_pdb_chain_id:
                        tags = ['ID', 'Entity_ID', 'PDB_chain_ID']
                        data = lp.get_tag(tags)
                        for row in data:
                            entity_assembly_id = row[0] if isinstance(row[0], str) else str(row[0])
                            entity_id = row[1] if isinstance(row[1], int) else int(row[1]) if row[1].isdigit() else None
                            pdb_chain_id = row[2].split(',')[0]
                            if entity_assembly is None:
                                entity_assembly = {}
                            entity_assembly[entity_assembly_id] = {'entity_id': entity_id, 'auth_asym_id': pdb_chain_id}
                    else:
                        tags = ['ID', 'Entity_ID']
                        data = lp.get_tag(tags)
                        for row in data:
                            entity_assembly_id = row[0] if isinstance(row[0], str) else str(row[0])
                            entity_id = row[1] if isinstance(row[1], int) else int(row[1]) if row[1].isdigit() else None
                            if entity_assembly is None:
                                entity_assembly = {}
                            entity_assembly[entity_assembly_id] = {'entity_id': entity_id, 'auth_asym_id': None}
                except KeyError:
                    pass

        if self.__reg.caC is not None:
            nmr_poly_seq = deepcopy(self.__reg.caC['polymer_sequence'])
            if self.__reg.caC['branched'] is not None:
                nmr_poly_seq.extend(self.__reg.caC['branched'])
            if self.__reg.caC['non_polymer'] is not None:
                nmr_poly_seq.extend(self.__reg.caC['non_polymer'])
            entity_assembly = {}
            for item in self.__reg.caC['entity_assembly']:
                _auth_asym_id = 'auth_asym_id' if 'fixed_auth_asym_id' not in item else 'fixed_auth_asym_id'
                entity_assembly[str(item['entity_assembly_id'])] =\
                    {'entity_id': item['entity_id'],
                     'auth_asym_id': item[_auth_asym_id].split(',')[0]}

        create_sf_dict = True

        if self.__reg.list_id_counter is None:
            self.__reg.list_id_counter = {}

        cs_sf_dict_holder = {}

        suspended_errors_for_lazy_eval = []

        def deal_lexer_or_parser_error(a_cs_format_name, file_name, lexer_err_listener, parser_err_listener):
            _err = ''
            if lexer_err_listener is not None:
                messageList = lexer_err_listener.getMessageList()

                if messageList is not None:
                    for description in messageList:
                        _err = f"[Syntax error as {a_cs_format_name} file] "\
                               f"line {description['line_number']}:{description['column_position']} {description['message']}\n"
                        if 'input' in description:
                            enc = detect_encoding(description['input'])
                            is_not_ascii = False
                            if enc is not None and enc != 'ascii':
                                _err += f"{description['input']}\n".encode().decode('ascii', 'backslashreplace')
                                is_not_ascii = True
                            else:
                                _err += f"{description['input']}\n"
                            _err += f"{description['marker']}\n"
                            if is_not_ascii:
                                _err += f"[Unexpected text encoding] Encoding used in the above line is {enc!r} and must be 'ascii'.\n"

            if parser_err_listener is not None and len(_err) == 0:
                messageList = parser_err_listener.getMessageList()

                if messageList is not None:
                    for description in messageList:
                        _err += f"[Syntax error as {a_cs_format_name} file] "\
                                f"line {description['line_number']}:{description['column_position']} {description['message']}\n"
                        if 'input' in description:
                            _err += f"{description['input']}\n"
                            _err += f"{description['marker']}\n"

            if len(_err) == 0:
                return False

            err = f"The assigned chemical shift file {file_name!r} looks like {a_cs_format_name} file. "\
                "Please re-upload the assigned chemical shift file.\n"\
                "The following issues need to be fixed before re-upload.\n" + _err[:-1]

            self.__reg.report.error.appendDescription('format_issue',
                                                      {'file_name': file_name, 'description': err})

            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {file_name} {err}\n")

            return True

        def consume_suspended_message():

            if len(suspended_errors_for_lazy_eval) > 0:
                for msg in suspended_errors_for_lazy_eval:
                    for k, v in msg.items():
                        self.__reg.report.error.appendDescription(k, v)
                suspended_errors_for_lazy_eval.clear()

        def deal_shi_warn_message(file_name, listener, ignore_error):

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}
                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        if g not in EMPTY_VALUE:
                            msg_dict['sf_framecode'] = g[1]
                            msg_dict['description'] = warn.replace(f', {g[1]}', '')

                    if warn.startswith('[Concatenated sequence]'):
                        self.__reg.report.warning.appendDescription('concatenated_sequence', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch]'):
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {warn}\n")

                    elif warn.startswith('[Atom not found]'):
                        self.__reg.report.error.appendDescription('atom_not_found', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {warn}\n")

                    elif warn.startswith('[Invalid atom nomenclature]'):
                        consume_suspended_message()

                        self.__reg.report.error.appendDescription('invalid_atom_nomenclature', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {warn}\n")

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        consume_suspended_message()

                        self.__reg.report.error.appendDescription('invalid_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ ValueError  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch warning]'):
                        self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Warning  - {warn}\n")

                        if SEQ_MISMATCH_WARNING_PAT.match(warn):
                            g = SEQ_MISMATCH_WARNING_PAT.search(warn).groups()
                            d = {'auth_chain_id': g[2],
                                 'auth_seq_id': int(g[0]),
                                 'auth_comp_id': g[1]}
                            if d not in self.__reg.nmr_ext_poly_seq:
                                self.__reg.nmr_ext_poly_seq.append(d)

                    elif warn.startswith('[Missing data]'):
                        self.__reg.report.warning.appendDescription('missing_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                        # consume_suspended_message()

                        self.__reg.report.warning.appendDescription('anomalous_chemical_shift', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Range value warning]')\
                            or (warn.startswith('[Range value error]') and self.__reg.remediation_mode):
                        self.__reg.report.warning.appendDescription('unusual_chemical_shift', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Warning  - {warn}\n")

                    elif not ignore_error:
                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.validateLegacyCs() ++ KeyError  - " + warn)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ KeyError  - {warn}\n")

        def deal_shi_warn_message_for_lazy_eval(file_name, listener):

            if listener.warningMessage is not None:

                def_sf_framecode = ''
                for warn in listener.warningMessage:

                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        if g[1] not in EMPTY_VALUE:
                            def_sf_framecode = g[1]
                            break

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}
                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        msg_dict['sf_framecode'] = g[1] if g[1] not in EMPTY_VALUE else def_sf_framecode
                        msg_dict['description'] = warn.replace(f', {g[1]}', '')

                    if warn.startswith('[Sequence mismatch]'):
                        suspended_errors_for_lazy_eval.append({'sequence_mismatch': msg_dict})

                    elif warn.startswith('[Atom not found]'):
                        if not self.__reg.remediation_mode or 'Macromolecules page' not in warn:
                            suspended_errors_for_lazy_eval.append({'atom_not_found': msg_dict})

                    # elif warn.startswith('[Hydrogen not instantiated]'):
                    #     if self.__reg.remediation_mode:
                    #         pass
                    #     else:
                    #         suspended_errors_for_lazy_eval.append({'hydrogen_not_instantiated': msg_dict})

                    # elif warn.startswith('[Coordinate issue]'):
                    #     suspended_errors_for_lazy_eval.append({'coordinate_issue': msg_dict})

                    # elif warn.startswith('[Invalid atom nomenclature]'):
                    #     suspended_errors_for_lazy_eval.append({'invalid_atom_nomenclature': msg_dict})

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        suspended_errors_for_lazy_eval.append({'invalid_data': msg_dict})

                    # elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                    #     suspended_errors_for_lazy_eval.append({'anomalous_data': msg_dict})

        fileListId = self.__reg.file_path_list_len

        for acs in self.__reg.inputParamDict[AC_FILE_PATH_LIST_KEY]:
            file_path = acs['file_name']

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            ignore_error = False if 'ignore_error' not in input_source_dic else input_source_dic['ignore_error']

            fileListId += 1

            if file_type is None or (not file_type.startswith('nm-shi-') and file_type != 'nm-aux-xea'):
                continue

            if self.__reg.remediation_mode and os.path.exists(file_path + '-ignored'):
                continue

            if os.path.exists(file_path + '-corrected'):
                file_path = file_path + '-corrected'

            file_name = input_source_dic['file_name']

            original_file_name = None
            if 'original_file_name' in input_source_dic:
                if input_source_dic['original_file_name'] is not None:
                    original_file_name = os.path.basename(input_source_dic['original_file_name'])
            if original_file_name in EMPTY_VALUE:
                original_file_name = file_name

            reserved_list_ids = None
            if len(_rlist_ids) > 0:
                rlist_ids = [item['list_id'] for item in _rlist_ids if item['data_file_name'] != original_file_name]
                if len(rlist_ids) > 0:
                    reserved_list_ids = {content_subtype: rlist_ids}

            _cs_format_name = getChemShiftFormatName(file_type)
            cs_format_name = _cs_format_name.split()[0]
            a_cs_format_name = ('an ' if cs_format_name[0] in ('AINMX') else 'a ') + _cs_format_name

            suspended_errors_for_lazy_eval.clear()

            if file_type == 'nm-shi-ari':
                reader = AriaCSReader(self.__reg.verbose, self.__reg.log,
                                      nmr_poly_seq, entity_assembly,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = AriaCSReader(self.__reg.verbose, self.__reg.log,
                                              nmr_poly_seq, entity_assembly,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (ARIA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-bar':
                reader = BareCSReader(self.__reg.verbose, self.__reg.log,
                                      nmr_poly_seq, entity_assembly,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = BareCSReader(self.__reg.verbose, self.__reg.log,
                                              nmr_poly_seq, entity_assembly,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file "\
                                f"(Bare WSV/TSV/CSV or Sparky resonance list) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-gar':
                reader = GarretCSReader(self.__reg.verbose, self.__reg.log,
                                        nmr_poly_seq, entity_assembly,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = GarretCSReader(self.__reg.verbose, self.__reg.log,
                                                nmr_poly_seq, entity_assembly,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (GARRET) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-npi':
                reader = NmrPipeCSReader(self.__reg.verbose, self.__reg.log,
                                         nmr_poly_seq, entity_assembly,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = NmrPipeCSReader(self.__reg.verbose, self.__reg.log,
                                                 nmr_poly_seq, entity_assembly,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (NMRPIPE) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-oli':
                reader = OliviaCSReader(self.__reg.verbose, self.__reg.log,
                                        nmr_poly_seq, entity_assembly,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = OliviaCSReader(self.__reg.verbose, self.__reg.log,
                                                nmr_poly_seq, entity_assembly,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (OLIVIA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-pip':
                reader = PippCSReader(self.__reg.verbose, self.__reg.log,
                                      nmr_poly_seq, entity_assembly,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = PippCSReader(self.__reg.verbose, self.__reg.log,
                                              nmr_poly_seq, entity_assembly,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (PIPP) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-ppm':
                reader = PpmCSReader(self.__reg.verbose, self.__reg.log,
                                     nmr_poly_seq, entity_assembly,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = PpmCSReader(self.__reg.verbose, self.__reg.log,
                                             nmr_poly_seq, entity_assembly,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (PPM) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-shi-st2':
                reader = NmrStar2CSReader(self.__reg.verbose, self.__reg.log,
                                          nmr_poly_seq, entity_assembly,
                                          self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = NmrStar2CSReader(self.__reg.verbose, self.__reg.log,
                                                  nmr_poly_seq, entity_assembly,
                                                  self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                  reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (NMR-STAR V2.1) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

            elif file_type in ('nm-aux-xea', 'nm-shi-xea'):
                reader = XeasyCSReader(self.__reg.verbose, self.__reg.log,
                                       nmr_poly_seq, entity_assembly,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and parser_err_listener.getMessageList() is None:
                    if deal_lexer_or_parser_error(a_cs_format_name, file_name, None, parser_err_listener):
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_shi_warn_message_for_lazy_eval(file_name, listener)

                        reader = XeasyCSReader(self.__reg.verbose, self.__reg.log,
                                               nmr_poly_seq, entity_assembly,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               reasons)

                        listener, _, _ = reader.parse(file_path,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_shi_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate assigned chemical shift file (XEASY) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyCs() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyCs() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in cs_sf_dict_holder:
                                    cs_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in cs_sf_dict_holder[content_subtype]:
                                        cs_sf_dict_holder[content_subtype].append(sf)

        if content_subtype in cs_sf_dict_holder and len(self.__reg.star_data) > 0 and isinstance(self.__reg.star_data[0], pynmrstar.Entry):
            master_entry = self.__reg.star_data[0]

            for sf in cs_sf_dict_holder[content_subtype]:

                data_file_name = get_first_sf_tag(sf['saveframe'], 'Data_file_name')

                if data_file_name not in EMPTY_VALUE:

                    _sf_list = master_entry.get_saveframes_by_tag_and_value('Data_file_name', data_file_name)

                    if len(_sf_list) == 1:

                        _sf = _sf_list[0]

                        try:

                            _lp = _sf.get_loop('_Atom_chem_shift')

                            del _sf[_lp]

                        except KeyError:
                            pass

                        _sf.add_loop(sf['loop'])

                    continue

                master_entry.add_saveframe(sf['saveframe'])

        return not self.__reg.report.isError()

    def validateLegacyMr(self) -> bool:
        """ Validate data content of legacy restraint files.
        """

        if self.__reg.combined_mode and not self.__reg.bmrb_only:
            return True

        if AR_FILE_PATH_LIST_KEY not in self.__reg.inputParamDict:
            return True

        src_id = self.__reg.report.getInputSourceIdOfCoord()

        if src_id < 0:
            return False

        cif_input_source = self.__reg.report.input_sources[src_id]
        cif_input_source_dic = cif_input_source.get()

        has_poly_seq = has_key_value(cif_input_source_dic, 'polymer_sequence')

        if not has_poly_seq:
            return False

        nmr_vs_model = None
        chain_assign_dic = self.__reg.report.chain_assignment.get()
        if 'nmr_poly_seq_vs_model_poly_seq' in chain_assign_dic:
            nmr_vs_model = chain_assign_dic['nmr_poly_seq_vs_model_poly_seq']

        if self.__reg.versioned_atom_name_mapping is not None:
            for atom_map in self.__reg.versioned_atom_name_mapping:
                if atom_map not in self.__reg.mr_atom_name_mapping:
                    self.__reg.mr_atom_name_mapping.append(atom_map)

        if len(self.__reg.internal_atom_name_mapping) > 0:
            for ver in sorted(list(self.__reg.internal_atom_name_mapping), reverse=True):
                if self.__reg.internal_atom_name_mapping[ver] is None:
                    continue
                for atom_map in self.__reg.internal_atom_name_mapping[ver]:
                    if atom_map not in self.__reg.mr_atom_name_mapping:
                        self.__reg.mr_atom_name_mapping.append(atom_map)

        if self.__reg.mr_atom_name_mapping is not None and len(self.__reg.mr_atom_name_mapping) > 1:
            self.__reg.mr_atom_name_mapping = list(reversed(self.__reg.mr_atom_name_mapping))

        amberAtomNumberDict = charmmAtomNumberDict = gromacsAtomNumberDict = pdbAtomNumberDict = None
        _amberAtomNumberDict = {}

        has_aux_amb = has_aux_cha = has_aux_gro = False
        has_res_amb = has_res_cha = has_res_gro = has_res_sch = False

        cyanaUplDistRest = cyanaLolDistRest = 0

        def deal_aux_warn_message(file_name, listener, dry_run=False):

            valid = True

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}

                    if warn.startswith('[Concatenated sequence]'):
                        if not dry_run:
                            self.__reg.report.warning.appendDescription('concatenated_sequence', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch]'):
                        if not dry_run and not has_res_sch:
                            self.__reg.report.error.appendDescription('sequence_mismatch', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")

                            valid = False

                    elif warn.startswith('[Unknown atom name]'):
                        if not dry_run:
                            self.__reg.report.warning.appendDescription('inconsistent_mr_data', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Unknown residue name]'):
                        if not dry_run:
                            self.__reg.report.warning.appendDescription('inconsistent_mr_data', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    else:
                        if not dry_run:
                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ KeyError  - " + warn)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ KeyError  - {warn}\n")

                        valid = False

            else:
                valid = False

            return valid

        fileListId = self.__reg.file_path_list_len

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
            file_path = ar['file_name']

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            fileListId += 1

            if file_type == 'nm-aux-amb':
                has_aux_amb = True

            if file_type == 'nm-aux-cha':
                has_aux_cha = True

            if file_type == 'nm-aux-gro':
                has_aux_gro = True

            if file_type == 'nm-res-amb':
                has_res_amb = True

            if file_type == 'nm-res-cha':
                has_res_cha = True

            if file_type == 'nm-res-gro':
                has_res_gro = True

            if file_type == 'nm-res-sch':
                has_res_sch = True

        fileListId = self.__reg.file_path_list_len

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
            file_path = ar['file_name']

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']
            content_subtype = input_source_dic['content_subtype']

            fileListId += 1

            if file_type == 'nm-aux-amb' and content_subtype is not None and 'topology' in content_subtype:

                if 'is_valid' in ar and ar['is_valid']:

                    file_name = input_source_dic['file_name']

                    original_file_name = None
                    if 'original_file_name' in input_source_dic:
                        if input_source_dic['original_file_name'] is not None:
                            original_file_name = os.path.basename(input_source_dic['original_file_name'])
                        if file_name != original_file_name and original_file_name is not None:
                            file_name = f"{original_file_name} ({file_name})"

                    reader = AmberPTReader(self.__reg.verbose, self.__reg.log,
                                           self.__reg.representative_model_id,
                                           self.__reg.representative_alt_id,
                                           self.__reg.mr_atom_name_mapping,
                                           self.__reg.cR, self.__reg.caC,
                                           self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                    listener, _, _ = reader.parse(file_path, self.__reg.cifPath)

                    if listener is not None:

                        deal_aux_warn_message(file_name, listener)

                        amberAtomNumberDict = listener.getAtomNumberDict()

                        poly_seq = listener.getPolymerSequence()
                        if poly_seq is not None:
                            input_source.setItemValue('polymer_sequence', poly_seq)

                        seq_align = listener.getSequenceAlignment()
                        if seq_align is not None:
                            self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_topology', seq_align)

            elif file_type == 'nm-aux-cha' and content_subtype is not None and 'topology' in content_subtype:

                if 'is_valid' in ar and ar['is_valid']:

                    file_name = input_source_dic['file_name']

                    original_file_name = None
                    if 'original_file_name' in input_source_dic:
                        if input_source_dic['original_file_name'] is not None:
                            original_file_name = os.path.basename(input_source_dic['original_file_name'])
                        if file_name != original_file_name and original_file_name is not None:
                            file_name = f"{original_file_name} ({file_name})"

                    reader = CharmmCRDReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                    listener, _, _ = reader.parse(file_path, self.__reg.cifPath)

                    if listener is not None:

                        deal_aux_warn_message(file_name, listener)

                        charmmAtomNumberDict = listener.getAtomNumberDict()

                        poly_seq = listener.getPolymerSequence()
                        if poly_seq is not None:
                            input_source.setItemValue('polymer_sequence', poly_seq)

                        seq_align = listener.getSequenceAlignment()
                        if seq_align is not None:
                            self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_topology', seq_align)

            elif file_type == 'nm-aux-gro' and content_subtype is not None and 'topology' in content_subtype:

                if 'is_valid' in ar and ar['is_valid']:

                    file_name = input_source_dic['file_name']

                    original_file_name = None
                    if 'original_file_name' in input_source_dic:
                        if input_source_dic['original_file_name'] is not None:
                            original_file_name = os.path.basename(input_source_dic['original_file_name'])
                        if file_name != original_file_name and original_file_name is not None:
                            file_name = f"{original_file_name} ({file_name})"

                    reader = GromacsPTReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                    listener, _, _ = reader.parse(file_path, self.__reg.cifPath)

                    if listener is not None:

                        deal_aux_warn_message(file_name, listener)

                        gromacsAtomNumberDict = listener.getAtomNumberDict()

                        poly_seq = listener.getPolymerSequence()
                        if poly_seq is not None:
                            input_source.setItemValue('polymer_sequence', poly_seq)

                        seq_align = listener.getSequenceAlignment()
                        if seq_align is not None:
                            self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_topology', seq_align)

            elif file_type == 'nm-aux-pdb' and content_subtype is not None and 'topology' in content_subtype:

                if 'is_valid' in ar and ar['is_valid']:

                    if (has_res_amb and not has_aux_amb)\
                       or (has_res_cha and not has_aux_cha)\
                       or (has_res_gro and not has_aux_gro)\
                       or has_res_sch:

                        file_name = input_source_dic['file_name']

                        original_file_name = None
                        if 'original_file_name' in input_source_dic:
                            if input_source_dic['original_file_name'] is not None:
                                original_file_name = os.path.basename(input_source_dic['original_file_name'])
                            if file_name != original_file_name and original_file_name is not None:
                                file_name = f"{original_file_name} ({file_name})"

                        reader = BarePDBReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                        if os.path.exists(file_path + '-corrected'):
                            file_path = file_path + '-corrected'

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath)

                        if listener is not None:

                            valid = deal_aux_warn_message(file_name, listener, True)

                            if not valid:
                                continue

                            poly_seq = listener.getPolymerSequence()

                            if not has_res_sch and any(True for pdb_ps in poly_seq if len(pdb_ps['seq_id']) == 0):
                                continue

                            if poly_seq is not None:
                                input_source.setItemValue('polymer_sequence', poly_seq)

                            seq_align = listener.getSequenceAlignment()
                            if seq_align is not None:
                                self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_topology', seq_align)

                                if valid or not has_res_amb:

                                    for sa in seq_align:
                                        ref_chain_id = sa['ref_chain_id']
                                        test_chain_id = sa['test_chain_id']
                                        cif_ps = next((cif_ps for cif_ps in self.__reg.caC['polymer_sequence']
                                                       if cif_ps['auth_chain_id'] == ref_chain_id), None)
                                        pdb_ps = next(pdb_ps for pdb_ps in poly_seq if pdb_ps['chain_id'] == test_chain_id)

                                        if cif_ps is None:
                                            valid = False
                                            break

                                        unobs_res_count = 0
                                        for seq_id in cif_ps['seq_id']:
                                            seq_key = (ref_chain_id, seq_id)
                                            if seq_key in self.__reg.caC['coord_unobs_res']:
                                                unobs_res_count += 1

                                        if len(cif_ps['seq_id']) - unobs_res_count > len(pdb_ps['seq_id']):
                                            valid = False
                                            break

                                    if valid:
                                        _pdbAtomNumberDict = listener.getAtomNumberDict()

                                        if _pdbAtomNumberDict is not None:
                                            if pdbAtomNumberDict is None:
                                                pdbAtomNumberDict = _pdbAtomNumberDict
                                            else:
                                                for k, v in _pdbAtomNumberDict.items():
                                                    if k not in pdbAtomNumberDict:
                                                        pdbAtomNumberDict[k] = v

                                        deal_aux_warn_message(file_name, listener, True)

                            elif has_res_sch and pdbAtomNumberDict is None:
                                pdbAtomNumberDict = listener.getAtomNumberDict()

            elif file_type == 'nm-res-cya' and content_subtype is not None and 'dist_restraint' in content_subtype:
                if 'is_valid' in ar and ar['is_valid']:
                    if ar['dist_type'] in ('upl', 'both'):
                        cyanaUplDistRest += 1
                    if ar['dist_type'] in ('lol', 'both'):
                        cyanaLolDistRest += 1

        if ((has_res_amb and not has_aux_amb) or (has_res_cha and not has_aux_cha) or (has_res_gro and not has_aux_gro) or has_res_sch)\
           and pdbAtomNumberDict is None and self.__reg.internal_mode:
            cif_file_name = os.path.basename(self.__reg.cifPath)
            if re.match(r'^([Pp][Dd][Bb]_)?(\d{4})?\d\w{3}.cif$', cif_file_name):
                dep_id = cif_file_name[:-4]

                file_path = os.path.join(self.__reg.cR.getDirPath(), f'{dep_id}_model-upload_P1.pdb.V1')

                if os.path.exists(file_path):
                    reader = BarePDBReader(self.__reg.verbose, self.__reg.log,
                                           self.__reg.representative_model_id,
                                           self.__reg.representative_alt_id,
                                           self.__reg.mr_atom_name_mapping,
                                           self.__reg.cR, self.__reg.caC,
                                           self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                    listener, _, _ = reader.parse(file_path, self.__reg.cifPath)

                    if listener is not None:
                        pdbAtomNumberDict = listener.getAtomNumberDict()

        if has_res_sch and pdbAtomNumberDict is None and not self.__reg.internal_mode:
            cif_file_name = os.path.basename(self.__reg.cifPath)

            if WORK_MODEL_FILE_NAME_PAT.match(cif_file_name):
                dep_id = WORK_MODEL_FILE_NAME_PAT.search(cif_file_name).groups()[0]

                file_path = os.path.join(self.__reg.cR.getDirPath(), f'{dep_id}_model-upload_P1.pdb.V1')

                if os.path.exists(file_path):
                    reader = BarePDBReader(self.__reg.verbose, self.__reg.log,
                                           self.__reg.representative_model_id,
                                           self.__reg.representative_alt_id,
                                           self.__reg.mr_atom_name_mapping,
                                           self.__reg.cR, self.__reg.caC,
                                           self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                    listener, _, _ = reader.parse(file_path, self.__reg.cifPath)

                    if listener is not None:
                        pdbAtomNumberDict = listener.getAtomNumberDict()

        if pdbAtomNumberDict is not None:
            if has_res_amb and amberAtomNumberDict is None:
                amberAtomNumberDict = pdbAtomNumberDict
            if has_res_cha and charmmAtomNumberDict is None:
                charmmAtomNumberDict = pdbAtomNumberDict
            if has_res_gro and gromacsAtomNumberDict is None:
                gromacsAtomNumberDict = pdbAtomNumberDict

        fileListId = self.__reg.file_path_list_len

        # 6gbm, NOE restraint files must take precedence over other distance constraints such as hydrogen bonds
        ar_file_order, ar_file_any_dist, ar_file_wo_dist = [], [], []

        derived_from_public_mr = False

        hint_for_noe_dist = ['noe', 'roe', 'dist']
        hint_for_any_dist = ['bond', 'disul', 'not', 'seen', 'pre', 'paramag', 'cidnp', 'csp', 'perturb', 'mutat', 'protect', 'symm']

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
            file_path = ar['file_name']
            file_size = os.path.getsize(file_path)

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            if fileListId == self.__reg.file_path_list_len and file_type == 'nm-res-mr':
                derived_from_public_mr = True

            fileListId += 1

            if file_type in ('nm-aux-amb', 'nm-aux-cha', 'nm-aux-gro', 'nm-aux-pdb', 'nm-res-oth', 'nm-res-mr', 'nm-res-sax')\
               or file_type.startswith('nm-pea'):
                continue

            if self.__reg.remediation_mode and os.path.exists(file_path + '-ignored'):
                continue

            content_subtype = input_source_dic['content_subtype']

            if content_subtype is None or len(content_subtype) == 0:
                continue

            if 'is_valid' not in ar or not ar['is_valid']:
                continue

            file_name = input_source_dic['file_name']

            original_file_name = None
            if 'original_file_name' in input_source_dic:
                if input_source_dic['original_file_name'] is not None:
                    original_file_name = os.path.basename(input_source_dic['original_file_name'])
                if file_name != original_file_name and original_file_name is not None:
                    file_name = original_file_name

            file_name = file_name.lower()

            if content_subtype is not None and 'dist_restraint' in content_subtype.keys():
                if any(k in file_name for k in hint_for_noe_dist) and not any(k in file_name for k in hint_for_any_dist):
                    ar_file_order.append((input_source, ar, file_size))
                else:
                    ar_file_any_dist.append((input_source, ar, file_size))
            else:
                ar_file_wo_dist.append((input_source, ar, file_size))

        ar_file_order = sorted(ar_file_order, key=itemgetter(2), reverse=True)
        ar_file_order.extend(sorted(ar_file_any_dist, key=itemgetter(2), reverse=True))
        ar_file_order.extend(sorted(ar_file_wo_dist, key=itemgetter(2), reverse=True))

        poly_seq_set = []

        create_sf_dict = self.__reg.remediation_mode

        if self.__reg.list_id_counter is None:
            self.__reg.list_id_counter = {}
        if self.__reg.mr_sf_dict_holder is None:
            self.__reg.mr_sf_dict_holder = {}

        if self.__reg.nmr_ext_poly_seq is None:
            self.__reg.nmr_ext_poly_seq = []

        if not self.__reg.bmrb_only or not self.__reg.internal_mode:  # nmrPolySeq is None in __retrieveCoordAssemblyChecker()

            input_source = self.__reg.report.input_sources[0]
            input_source_dic = input_source.get()

            has_poly_seq = has_key_value(input_source_dic, 'polymer_sequence')

            nmr_poly_seq = input_source_dic['polymer_sequence']
            cif_poly_seq = self.__reg.caC['polymer_sequence']

            seq_align, _ = alignPolymerSequence(self.__reg.pA, cif_poly_seq, nmr_poly_seq)
            chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, 'nmr-star', cif_poly_seq, nmr_poly_seq, seq_align)

            if chain_assign is not None:

                for ca in chain_assign:
                    ref_chain_id = ca['ref_chain_id']
                    test_chain_id = ca['test_chain_id']

                    sa = next(sa for sa in seq_align
                              if sa['ref_chain_id'] == ref_chain_id
                              and sa['test_chain_id'] == test_chain_id)

                    if sa['conflict'] > 0 or sa['unmapped'] == 0:
                        continue

                    ps1 = next(ps for ps in nmr_poly_seq if ps['chain_id'] == test_chain_id)
                    ps2 = next(ps for ps in cif_poly_seq if ps['auth_chain_id'] == ref_chain_id)

                    self.__reg.pA.setReferenceSequence(ps1['comp_id'], 'REF' + test_chain_id)
                    self.__reg.pA.addTestSequence(ps2['comp_id'], test_chain_id)
                    self.__reg.pA.doAlign()

                    myAlign = self.__reg.pA.getAlignment(test_chain_id)

                    length = len(myAlign)

                    _matched, unmapped, conflict, offset_1, offset_2 = getScoreOfSeqAlign(myAlign)

                    if conflict == 0 and unmapped > 0:

                        nmr_seq_ids, cif_auth_seq_ids = [], []

                        for i in range(length):
                            if str(myAlign[i][0]) != '.' and i < len(ps1['seq_id']):
                                nmr_seq_ids.append(ps1['seq_id'][i])
                            else:
                                nmr_seq_ids.append(None)

                        for i in range(length):
                            if str(myAlign[i][1]) != '.' and i < len(ps2['seq_id']):
                                cif_auth_seq_ids.append(ps2['auth_seq_id'][i])
                            else:
                                cif_auth_seq_ids.append(None)

                        for i in range(length):
                            nmr_comp_id, cif_comp_id = str(myAlign[i][0]), str(myAlign[i][1])

                            if nmr_comp_id == cif_comp_id:
                                continue

                            if cif_comp_id == '.' and nmr_comp_id != '.':
                                nmr_seq_id = nmr_seq_ids[i] - offset_1 if nmr_seq_ids[i] is not None else None
                                if nmr_seq_id is not None:
                                    offset = None
                                    for _offset in range(1, 20):
                                        if i + _offset < length:
                                            _myPr = myAlign[i + _offset]
                                            if _myPr[0] == _myPr[1]:
                                                offset = _offset
                                                break
                                        if i - _offset >= 0:
                                            _myPr = myAlign[i - _offset]
                                            if _myPr[0] == _myPr[1]:
                                                offset = -_offset
                                                break

                                    if offset is not None and cif_auth_seq_ids[i + offset] is not None:
                                        cif_auth_seq_id = cif_auth_seq_ids[i + offset] - offset - offset_2
                                        self.__reg.nmr_ext_poly_seq.append({'auth_chain_id': ps2['auth_chain_id'],
                                                                            'auth_seq_id': cif_auth_seq_id,
                                                                            'auth_comp_id': nmr_comp_id})

        reasons_dict = {}

        suspended_errors_for_lazy_eval = []

        def consume_suspended_message():

            if len(suspended_errors_for_lazy_eval) > 0:
                for msg in suspended_errors_for_lazy_eval:
                    for k, v in msg.items():
                        self.__reg.report.error.appendDescription(k, v)
                suspended_errors_for_lazy_eval.clear()

        def deal_res_warn_message(file_name, listener, ignore_error):

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}
                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        if g not in EMPTY_VALUE:
                            msg_dict['sf_framecode'] = g[1]
                            msg_dict['description'] = warn.replace(f', {g[1]}', '')

                    if warn.startswith('[Concatenated sequence]'):
                        self.__reg.report.warning.appendDescription('concatenated_sequence', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch]'):
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")

                    elif warn.startswith('[Atom not found]'):

                        if not self.__reg.remediation_mode or 'Macromolecules page' not in warn or self.__reg.conversion_server:
                            consume_suspended_message()

                            self.__reg.report.error.appendDescription('atom_not_found', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")
                        else:
                            self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Hydrogen not instantiated]'):

                        if self.__reg.remediation_mode and not self.__reg.conversion_server:

                            self.__reg.report.warning.appendDescription('hydrogen_not_instantiated', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                        else:
                            consume_suspended_message()

                            self.__reg.report.error.appendDescription('hydrogen_not_instantiated', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")

                    elif warn.startswith('[Coordinate issue]'):
                        # consume_suspended_message()

                        if self.__reg.internal_mode and not self.__reg.conversion_server:

                            self.__reg.report.warning.appendDescription('coordinate_issue', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                        else:

                            self.__reg.report.error.appendDescription('coordinate_issue', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")

                    elif warn.startswith('[Invalid atom nomenclature]'):
                        consume_suspended_message()

                        self.__reg.report.error.appendDescription('invalid_atom_nomenclature', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        consume_suspended_message()

                        self.__reg.report.error.appendDescription('invalid_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ ValueError  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch warning]'):
                        self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                        if SEQ_MISMATCH_WARNING_PAT.match(warn):
                            g = SEQ_MISMATCH_WARNING_PAT.search(warn).groups()
                            d = {'auth_chain_id': g[2],
                                 'auth_seq_id': int(g[0]),
                                 'auth_comp_id': g[1]}
                            if d not in self.__reg.nmr_ext_poly_seq:
                                self.__reg.nmr_ext_poly_seq.append(d)

                    elif warn.startswith('[Missing data]'):
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('missing_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ ValueError  - {warn}\n")

                    elif warn.startswith('[Enum mismatch]'):
                        self.__reg.report.warning.appendDescription('enum_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Enum mismatch ignorable]'):
                        self.__reg.report.warning.appendDescription('enum_mismatch_ignorable', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Unmatched atom type]'):
                        self.__reg.report.warning.appendDescription('inconsistent_mr_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Inconsistent dihedral angle atoms]'):
                        self.__reg.report.warning.appendDescription('inconsistent_mr_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('anomalous_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ ValueError  - {warn}\n")

                    elif warn.startswith('[Range value warning]')\
                            or (warn.startswith('[Range value error]') and self.__reg.remediation_mode):
                        self.__reg.report.warning.appendDescription('inconsistent_mr_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Insufficient atom selection]') or warn.startswith('[Insufficient angle selection]'):

                        if self.__reg.conversion_server:
                            self.__reg.report.error.appendDescription('unparsed_data', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {warn}\n")

                        else:
                            self.__reg.report.warning.appendDescription('insufficient_mr_data', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Redundant data]'):
                        self.__reg.report.warning.appendDescription('redundant_mr_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Ambiguous dihedral angle]'):
                        self.__reg.report.warning.appendDescription('ambiguous_dihedral_angle', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Anomalous RDC vector]'):
                        self.__reg.report.warning.appendDescription('anomalous_rdc_vector', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Anomalous data]'):
                        self.__reg.report.warning.appendDescription('anomalous_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Unsupported data]'):
                        self.__reg.report.warning.appendDescription('unsupported_mr_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {warn}\n")

                    elif not ignore_error:
                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.validateLegacyMr() ++ KeyError  - " + warn)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ KeyError  - {warn}\n")

        def deal_res_warn_message_for_lazy_eval(file_name, listener):

            if listener.warningMessage is not None:

                def_sf_framecode = ''
                for warn in listener.warningMessage:

                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        if g[1] not in EMPTY_VALUE:
                            def_sf_framecode = g[1]
                            break

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}
                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        msg_dict['sf_framecode'] = g[1] if g[1] not in EMPTY_VALUE else def_sf_framecode
                        msg_dict['description'] = warn.replace(f', {g[1]}', '')

                    if warn.startswith('[Sequence mismatch]'):
                        suspended_errors_for_lazy_eval.append({'sequence_mismatch': msg_dict})

                    elif warn.startswith('[Atom not found]'):
                        if not self.__reg.remediation_mode or 'Macromolecules page' not in warn:
                            suspended_errors_for_lazy_eval.append({'atom_not_found': msg_dict})

                    elif warn.startswith('[Hydrogen not instantiated]'):
                        if self.__reg.remediation_mode:
                            pass
                        else:
                            suspended_errors_for_lazy_eval.append({'hydrogen_not_instantiated': msg_dict})

                    # elif warn.startswith('[Coordinate issue]'):
                    #     suspended_errors_for_lazy_eval.append({'coordinate_issue': msg_dict})

                    # elif warn.startswith('[Invalid atom nomenclature]'):
                    #     suspended_errors_for_lazy_eval.append({'invalid_atom_nomenclature': msg_dict})

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        suspended_errors_for_lazy_eval.append({'invalid_data': msg_dict})

                    # elif warn.startswith('[Missing data]'):
                    #     suspended_errors_for_lazy_eval.append({'missing_data': msg_dict})

                    # elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                    #     suspended_errors_for_lazy_eval.append({'anomalous_data': msg_dict})

        for input_source, ar, _ in ar_file_order:
            file_path = ar['file_name']

            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']
            content_subtype = input_source_dic['content_subtype']

            ignore_error = False if 'ignore_error' not in input_source_dic else input_source_dic['ignore_error']

            if file_type in ('nm-aux-amb', 'nm-aux-cha', 'nm-aux-gro', 'nm-aux-pdb', 'nm-res-oth', 'nm-res-mr', 'nm-res-sax')\
               or file_type.startswith('nm-pea'):
                continue

            if self.__reg.remediation_mode and os.path.exists(file_path + '-ignored'):
                continue

            file_name = input_source_dic['file_name']

            original_file_name = None
            if 'original_file_name' in input_source_dic:
                if input_source_dic['original_file_name'] is not None:
                    original_file_name = os.path.basename(input_source_dic['original_file_name'])
                if file_name != original_file_name and original_file_name is not None:
                    file_name = f"{original_file_name} ({file_name})"
            if original_file_name in EMPTY_VALUE and self.__reg.internal_mode:
                original_file_name = file_name

            if file_type == 'nm-res-amb' and amberAtomNumberDict is None and 'has_comments' in ar and not ar['has_comments']:

                err = f"To verify AMBER restraint file {file_name!r}, AMBER topology file must be uploaded "\
                    "or Sander comments should be included in the AMBER restraint file."

                if self.__reg.internal_mode:

                    self.__reg.report.warning.appendDescription('missing_content',
                                                                {'file_name': file_name, 'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {err}\n")

                else:

                    self.__reg.report.error.appendDescription('missing_mandatory_content',
                                                              {'file_name': file_name, 'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                    continue

            if file_type == 'nm-res-cha' and charmmAtomNumberDict is None and not has_aux_cha:

                err = f"CHARMM topology file (aka. CRD or CHARM CARD) must be uploaded to verify CHARMM restraint file {file_name!r}."

                if self.__reg.internal_mode:

                    self.__reg.report.warning.appendDescription('missing_content',
                                                                {'file_name': file_name, 'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {err}\n")

                else:

                    self.__reg.report.error.appendDescription('missing_mandatory_content',
                                                              {'file_name': file_name, 'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                    continue

            if file_type == 'nm-res-gro' and gromacsAtomNumberDict is None and not has_aux_gro:

                err = f"GROMACS topology file must be uploaded to verify GROMACS restraint file {file_name!r}."

                if self.__reg.internal_mode:

                    self.__reg.report.warning.appendDescription('missing_content',
                                                                {'file_name': file_name, 'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Warning  - {err}\n")

                else:

                    self.__reg.report.error.appendDescription('missing_mandatory_content',
                                                              {'file_name': file_name, 'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                    continue

            if content_subtype is None or len(content_subtype) == 0:
                continue

            if 'is_valid' not in ar or not ar['is_valid']:
                continue

            _reasons = reasons_dict.get(file_type)
            if _reasons is not None\
               and 'label_seq_scheme' not in _reasons\
               and 'global_auth_sequence_offset' not in _reasons\
               and 'chain_id_remap' not in _reasons\
               and file_type != 'nm-res-amb'\
               and 'dist_restraint' not in content_subtype:
                _reasons = None

            reasons = _reasons

            suspended_errors_for_lazy_eval.clear()

            if file_type == 'nm-res-amb':
                reader = AmberMRReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                       amberAtomNumberDict, _amberAtomNumberDict,
                                       reasons)
                reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = reader.getReasons()

                    if reasons is not None and _reasons is not None and listener.warningMessage is not None\
                       and len(listener.warningMessage) > 0:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        reader = AmberMRReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               amberAtomNumberDict, _amberAtomNumberDict,
                                               None)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = reader.getReasons()

                    if reasons is not None:

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                    deal_res_warn_message(file_name, listener, ignore_error)

                    cur_dict = listener.getAtomNumberDict()
                    if cur_dict is not None:
                        if len(_amberAtomNumberDict) == 0:
                            _amberAtomNumberDict = cur_dict
                        else:
                            for k, v in cur_dict.items():
                                if k not in _amberAtomNumberDict:
                                    _amberAtomNumberDict[k] = v

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (AMBER) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-ari':
                reader = AriaMRReader(self.__reg.verbose, self.__reg.log,
                                      self.__reg.representative_model_id,
                                      self.__reg.representative_alt_id,
                                      self.__reg.mr_atom_name_mapping,
                                      self.__reg.cR, self.__reg.caC,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = AriaMRReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (ARIA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-arx':
                reader = AriaMRXReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = AriaMRXReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (ARIA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-bar':
                reader = BareMRReader(self.__reg.verbose, self.__reg.log,
                                      self.__reg.representative_model_id,
                                      self.__reg.representative_alt_id,
                                      self.__reg.mr_atom_name_mapping,
                                      self.__reg.cR, self.__reg.caC,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = BareMRReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (Bare WSV/TSV/CSV) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-bio':
                reader = BiosymMRReader(self.__reg.verbose, self.__reg.log,
                                        self.__reg.representative_model_id,
                                        self.__reg.representative_alt_id,
                                        self.__reg.mr_atom_name_mapping,
                                        self.__reg.cR, self.__reg.caC,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = BiosymMRReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (BIOSYM) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-cha':
                reader = CharmmMRReader(self.__reg.verbose, self.__reg.log,
                                        self.__reg.representative_model_id,
                                        self.__reg.representative_alt_id,
                                        self.__reg.mr_atom_name_mapping,
                                        self.__reg.cR, self.__reg.caC,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                        charmmAtomNumberDict,
                                        reasons)
                reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                reader.setNmrVsModel(nmr_vs_model)
                if file_path in self.__reg.sll_pred_forced:
                    reader.setSllPredMode(True)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = CharmmMRReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                charmmAtomNumberDict,
                                                None)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)
                        if file_path in self.__reg.sll_pred_forced:
                            reader.setSllPredMode(True)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = CharmmMRReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                charmmAtomNumberDict,
                                                reasons)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)
                        if file_path in self.__reg.sll_pred_forced:
                            reader.setSllPredMode(True)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (CHARMM) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-cns':
                reader = CnsMRReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                     reasons)
                reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                reader.setNmrVsModel(nmr_vs_model)
                if file_path in self.__reg.sll_pred_forced:
                    reader.setSllPredMode(True)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = CnsMRReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             None)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)
                        if file_path in self.__reg.sll_pred_forced:
                            reader.setSllPredMode(True)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = CnsMRReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)
                        if file_path in self.__reg.sll_pred_forced:
                            reader.setSllPredMode(True)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (CNS) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-cya':
                has_dist_restraint = 'dist_restraint' in content_subtype

                upl_or_lol = None
                if has_dist_restraint:
                    dist_type = ar['dist_type']
                    if cyanaLolDistRest == 0 and dist_type == 'upl':
                        upl_or_lol = 'upl_only'
                    elif cyanaUplDistRest == 0 and dist_type == 'lol':
                        upl_or_lol = 'lol_only'
                    elif dist_type == 'upl':
                        upl_or_lol = 'upl_w_lol'
                    elif dist_type == 'lol':
                        upl_or_lol = 'lol_w_upl'
                    else:
                        upl_or_lol = None

                cya_file_ext = self.__reg.dpS.retrieveOriginalFileExtensionOfCyanaMrFile() if self.__reg.dpS is not None else None

                reader = CyanaMRReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                       reasons, upl_or_lol, cya_file_ext)
                reader.setRemediateMode(self.__reg.remediation_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = CyanaMRReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               None, upl_or_lol, cya_file_ext)
                        reader.setRemediateMode(self.__reg.remediation_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = CyanaMRReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               reasons, upl_or_lol, cya_file_ext)
                        reader.setRemediateMode(self.__reg.remediation_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    # support content subtype change during MR validation with the coordinates
                    input_source.setItemValue('content_subtype', listener.getContentSubtype())

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (CYANA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-dyn':
                reader = DynamoMRReader(self.__reg.verbose, self.__reg.log,
                                        self.__reg.representative_model_id,
                                        self.__reg.representative_alt_id,
                                        self.__reg.mr_atom_name_mapping,
                                        self.__reg.cR, self.__reg.caC,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = DynamoMRReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (DYNAMO/PALES/TALOS) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-isd':
                reader = IsdMRReader(self.__reg.verbose, self.__reg.log,
                                     self.__reg.representative_model_id,
                                     self.__reg.representative_alt_id,
                                     self.__reg.mr_atom_name_mapping,
                                     self.__reg.cR, self.__reg.caC,
                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = IsdMRReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (ISD) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-gro':
                reader = GromacsMRReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                         gromacsAtomNumberDict)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (GROMACS) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-noa':
                reader = CyanaNOAReader(self.__reg.verbose, self.__reg.log,
                                        self.__reg.representative_model_id,
                                        self.__reg.representative_alt_id,
                                        self.__reg.mr_atom_name_mapping,
                                        self.__reg.cR, self.__reg.caC,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                        reasons)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = CyanaNOAReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                None)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = CyanaNOAReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    # support content subtype change during MR validation with the coordinates
                    input_source.setItemValue('content_subtype', listener.getContentSubtype())

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (CYANA NOA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-ros':
                reader = RosettaMRReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                         reasons)
                reader.setRemediateMode(self.__reg.remediation_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = RosettaMRReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 None)
                        reader.setRemediateMode(self.__reg.remediation_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = RosettaMRReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 reasons)
                        reader.setRemediateMode(self.__reg.remediation_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (ROSETTA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-sch':
                reader = SchrodingerMRReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                             pdbAtomNumberDict, reasons)
                reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                reader.setNmrVsModel(nmr_vs_model)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = SchrodingerMRReader(self.__reg.verbose, self.__reg.log,
                                                     self.__reg.representative_model_id,
                                                     self.__reg.representative_alt_id,
                                                     self.__reg.mr_atom_name_mapping,
                                                     self.__reg.cR, self.__reg.caC,
                                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                     pdbAtomNumberDict, None)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = SchrodingerMRReader(self.__reg.verbose, self.__reg.log,
                                                     self.__reg.representative_model_id,
                                                     self.__reg.representative_alt_id,
                                                     self.__reg.mr_atom_name_mapping,
                                                     self.__reg.cR, self.__reg.caC,
                                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                     pdbAtomNumberDict, reasons)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (SCHRODINGER/ASL) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-syb':
                reader = SybylMRReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = SybylMRReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               reasons)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (SYBYL) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-res-xpl':
                reader = XplorMRReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                       reasons)
                reader.setRemediateMode(self.__reg.remediation_mode and derived_from_public_mr)
                reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                reader.setNmrVsModel(nmr_vs_model)
                if file_path in self.__reg.sll_pred_forced:
                    reader.setSllPredMode(True)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                              createSfDict=create_sf_dict, originalFileName=original_file_name,
                                              listIdCounter=self.__reg.list_id_counter,
                                              entryId=self.__reg.entry_id)

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if None not in (reasons, _reasons):

                        reader = XplorMRReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               None)
                        reader.setRemediateMode(self.__reg.remediation_mode and derived_from_public_mr)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)
                        if file_path in self.__reg.sll_pred_forced:
                            reader.setSllPredMode(True)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter,
                                                      entryId=self.__reg.entry_id)

                        if listener is not None:
                            reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_res_warn_message_for_lazy_eval(file_name, listener)

                        if 'dist_restraint' in content_subtype.keys():
                            reasons_dict[file_type] = reasons

                        if 'model_chain_id_ext' in reasons:
                            self.__reg.auth_asym_ids_with_chem_exch.update(reasons['model_chain_id_ext'])
                        if 'chain_id_clone' in reasons:
                            self.__reg.auth_seq_ids_with_chem_exch.update(reasons['chain_id_clone'])

                        reader = XplorMRReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               reasons)
                        reader.setRemediateMode(self.__reg.remediation_mode and derived_from_public_mr)
                        reader.setInternalMode(self.__reg.internal_mode and derived_from_public_mr)
                        reader.setNmrVsModel(nmr_vs_model)
                        if file_path in self.__reg.sll_pred_forced:
                            reader.setSllPredMode(True)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=__list_id_counter,
                                                      entryId=self.__reg.entry_id)

                    deal_res_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

                    # support content subtype change during MR validation with the coordinates
                    input_source.setItemValue('content_subtype', listener.getContentSubtype())

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate the restraint file (XPLOR-NIH) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyMr() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyMr() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in self.__reg.mr_sf_dict_holder:
                                    self.__reg.mr_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in self.__reg.mr_sf_dict_holder[content_subtype]:
                                        self.__reg.mr_sf_dict_holder[content_subtype].append(sf)

        if len(poly_seq_set) > 1:

            poly_seq_rst = None
            for idx, poly_seq in enumerate(poly_seq_set):
                if idx == 0:
                    poly_seq_rst = poly_seq
                    continue
                for ps in poly_seq:
                    chain_id = ps['chain_id']
                    for seq_id, comp_id in zip(ps['seq_id'], ps['comp_id']):
                        updatePolySeqRst(poly_seq_rst, chain_id, seq_id, comp_id)

            poly_seq_model = self.__reg.caC['polymer_sequence']

            sortPolySeqRst(poly_seq_rst)

            file_type = 'nm-res-mr'

            seq_align, _ = alignPolymerSequence(self.__reg.pA, poly_seq_model, poly_seq_rst, conservative=False)
            chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type, poly_seq_model, poly_seq_rst, seq_align)

            if chain_assign is not None:

                if len(poly_seq_model) == len(poly_seq_rst):

                    chain_mapping = {}

                    for ca in chain_assign:
                        ref_chain_id = ca['ref_chain_id']
                        test_chain_id = ca['test_chain_id']

                        if ref_chain_id != test_chain_id:
                            chain_mapping[test_chain_id] = ref_chain_id

                    if len(chain_mapping) == len(poly_seq_model):

                        for ps in poly_seq_rst:
                            if ps['chain_id'] in chain_mapping:
                                ps['chain_id'] = chain_mapping[ps['chain_id']]

                        seq_align, _ = alignPolymerSequence(self.__reg.pA, poly_seq_model, poly_seq_rst, conservative=False)
                        chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type,
                                                                poly_seq_model, poly_seq_rst, seq_align)

                    trimSequenceAlignment(seq_align, chain_assign)

            input_source.setItemValue('polymer_sequence', poly_seq_rst)

            self.__reg.report.sequence_alignment.setItemValue('model_poly_seq_vs_mr_restraint', seq_align)

        if len(self.__reg.nmr_ext_poly_seq) > 0:
            entity_assembly = self.__reg.caC['entity_assembly']
            auth_chain_ids = list(set(d['auth_chain_id'] for d in self.__reg.nmr_ext_poly_seq))
            for auth_chain_id in auth_chain_ids:
                item = next(item for item in entity_assembly if auth_chain_id in item['auth_asym_id'].split(','))
                if item['entity_type'] == 'polymer':
                    poly_type = item['entity_poly_type']
                    if poly_type.startswith('polypeptide'):
                        unknown_residue = 'UNK'
                    elif any(True for comp_id in item['comp_id_set'] if comp_id in ('DA', 'DC', 'DG', 'DT'))\
                            and any(True for comp_id in item['comp_id_set'] if comp_id in ('A', 'C', 'G', 'U')):
                        unknown_residue = 'DN'
                    elif poly_type == 'polydeoxyribonucleotide':
                        unknown_residue = 'DN'
                    elif poly_type == 'polyribonucleotide':
                        unknown_residue = 'N'
                    else:
                        continue
                    ps = next(ps for ps in self.__reg.caC['polymer_sequence'] if ps['auth_chain_id'] == auth_chain_id)
                    auth_seq_ids = [d['auth_seq_id'] for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == auth_chain_id]
                    auth_seq_ids.extend(list(filter(None, ps['auth_seq_id'])))
                    min_auth_seq_id = min(auth_seq_ids)
                    max_auth_seq_id = max(auth_seq_ids)
                    for auth_seq_id in range(min_auth_seq_id, max_auth_seq_id + 1):
                        if auth_seq_id not in ps['auth_seq_id']\
                           and not any(True for d in self.__reg.nmr_ext_poly_seq
                                       if d['auth_chain_id'] == auth_chain_id and d['auth_seq_id'] == auth_seq_id):
                            self.__reg.nmr_ext_poly_seq.append({'auth_chain_id': auth_chain_id,
                                                                'auth_seq_id': auth_seq_id,
                                                                'auth_comp_id': unknown_residue})

            self.__reg.nmr_ext_poly_seq = sorted(self.__reg.nmr_ext_poly_seq, key=itemgetter('auth_chain_id', 'auth_seq_id'))

        return not self.__reg.report.isError()

    def validateLegacyPk(self) -> bool:
        """ Validate data content of legacy spectral peak files and merge them if possible.
        """

        if self.__reg.combined_mode and not self.__reg.bmrb_only:
            return True

        if AR_FILE_PATH_LIST_KEY not in self.__reg.inputParamDict:
            return True

        src_id = self.__reg.report.getInputSourceIdOfCoord()

        if src_id < 0:
            return False

        cif_input_source = self.__reg.report.input_sources[src_id]
        cif_input_source_dic = cif_input_source.get()

        has_poly_seq = has_key_value(cif_input_source_dic, 'polymer_sequence')

        if not has_poly_seq:
            return False

        file_type = 'nmr-star'
        content_subtype = 'spectral_peak'

        sf_category = SF_CATEGORIES[file_type][content_subtype]

        rlist_ids = []
        if len(self.__reg.star_data) > 0 and isinstance(self.__reg.star_data[0], pynmrstar.Entry):
            for idx, sf in enumerate(self.__reg.star_data[0].get_saveframes_by_category(sf_category), start=1):
                list_id = get_first_sf_tag(sf, 'ID')
                rlist_ids.append(int(list_id) if list_id not in EMPTY_VALUE else idx)

        reserved_list_ids = {content_subtype: rlist_ids} if len(rlist_ids) > 0 else None

        xeasyAtomNumberDict = None

        has_aux_xea = has_pea_xea = False

        fileListId = self.__reg.file_path_list_len

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
            file_path = ar['file_name']

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            if file_type == 'nm-pea-xea':
                has_pea_xea = True
                break

            fileListId += 1

        def deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener):
            _type = 'default'
            _err = ''
            if lexer_err_listener is not None:
                messageList = lexer_err_listener.getMessageList()

                if messageList is not None:
                    for description in messageList:
                        _err = f"[Syntax error as {a_pk_format_name} file] "\
                               f"line {description['line_number']}:{description['column_position']} {description['message']}\n"
                        if 'input' in description:
                            enc = detect_encoding(description['input'])
                            is_not_ascii = False
                            if enc is not None and enc != 'ascii':
                                _err += f"{description['input']}\n".encode().decode('ascii', 'backslashreplace')
                                is_not_ascii = True
                            else:
                                _err += f"{description['input']}\n"
                            _err += f"{description['marker']}\n"
                            if is_not_ascii:
                                _err += f"[Unexpected text encoding] Encoding used in the above line is {enc!r} and must be 'ascii'.\n"

            if parser_err_listener is not None and len(_err) == 0:
                messageList = parser_err_listener.getMessageList()

                if messageList is not None:
                    for description in messageList:
                        if 'SPARKY' in a_pk_format_name\
                           and (MISMATCHED_INPUT_ERR_MSG in description['message']
                                or EXTRANEOUS_INPUT_ERR_MSG in description['message'])\
                           and "expecting {Lw1_Hz_LA, Lw2_Hz_LA, Lw3_Hz_LA, Lw4_Hz_LA" in description['message']\
                           and ('Height' in description['message']
                                or 'Data' in description['message']):
                            _type = 'reverse'
                        elif 'SPARKY' in a_pk_format_name\
                                and MISMATCHED_INPUT_ERR_MSG in description['message']\
                                and "'\\n' expecting {Integer, Float, Real, Real_vol}" in description['message']:
                            _type = 'no'
                        elif 'NMRVIEW' in a_pk_format_name\
                                and MISMATCHED_INPUT_ERR_MSG in description['message']\
                                and "' expecting L_brace" in description['message']:
                            _type = 'no_brace'
                        else:
                            _err += f"[Syntax error as {a_pk_format_name} file] "\
                                    f"line {description['line_number']}:{description['column_position']} {description['message']}\n"
                            if 'input' in description:
                                _err += f"{description['input']}\n"
                                _err += f"{description['marker']}\n"

            if len(_err) == 0:
                return False, _type

            err = f"The spectral peak list file {file_name!r} looks like {a_pk_format_name} file. "\
                "Please re-upload the spectral peak list file.\n"\
                "The following issues need to be fixed before re-upload.\n" + _err[:-1]

            self.__reg.report.error.appendDescription('format_issue',
                                                      {'file_name': file_name, 'description': err})

            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {file_name} {err}\n")

            return True, _type

        def deal_aux_warn_message(file_name, listener):

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}

                    if warn.startswith('[Concatenated sequence]'):
                        self.__reg.report.warning.appendDescription('concatenated_sequence', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch]'):
                        self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Unknown atom name]'):
                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Unknown residue name]'):
                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    else:
                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.validateLegacyPk() ++ KeyError  - " + warn)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ KeyError  - {warn}\n")

        if has_pea_xea:

            fileListId = self.__reg.file_path_list_len

            for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
                file_path = ar['file_name']

                if os.path.exists(file_path + '-corrected'):
                    file_path = file_path + '-corrected'

                input_source = self.__reg.report.input_sources[fileListId]
                input_source_dic = input_source.get()

                file_type = input_source_dic['file_type']

                fileListId += 1

                if file_type == 'nm-aux-xea':
                    has_aux_xea = True

                    file_name = input_source_dic['file_name']

                    original_file_name = None
                    if 'original_file_name' in input_source_dic:
                        if input_source_dic['original_file_name'] is not None:
                            original_file_name = os.path.basename(input_source_dic['original_file_name'])
                        if file_name != original_file_name and original_file_name is not None:
                            file_name = f"{original_file_name} ({file_name})"

                    reader = XeasyPROTReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)

                    listener, parser_err_listener, lexer_err_listener = reader.parse(file_path, self.__reg.cifPath)

                    _content_subtype = listener.getContentSubtype() if listener is not None else None
                    if _content_subtype is not None and len(_content_subtype) == 0:
                        _content_subtype = None

                    if None not in (lexer_err_listener, parser_err_listener, listener)\
                       and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                            or _content_subtype is not None):
                        _pk_format_name = getRestraintFormatName(file_type)
                        pk_format_name = _pk_format_name.split()[0]
                        a_pk_format_name = ('an ' if pk_format_name[0] in ('AINMX') else 'a ') + _pk_format_name
                        if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                            continue

                    if listener is not None:

                        deal_aux_warn_message(file_name, listener)

                        xeasyAtomNumberDict = listener.getAtomNumberDict()

                    break

        poly_seq_set = []

        create_sf_dict = self.__reg.remediation_mode

        if self.__reg.list_id_counter is None:
            self.__reg.list_id_counter = {}

        pk_sf_dict_holder = {}

        proc_nmr_ext_poly_seq = False

        if self.__reg.nmr_ext_poly_seq is None and not self.__reg.bmrb_only or not self.__reg.internal_mode:
            proc_nmr_ext_poly_seq = True

            self.__reg.nmr_ext_poly_seq = []

            input_source = self.__reg.report.input_sources[0]
            input_source_dic = input_source.get()

            nmr_poly_seq = input_source_dic['polymer_sequence']
            cif_poly_seq = self.__reg.caC['polymer_sequence']

            seq_align, _ = alignPolymerSequence(self.__reg.pA, cif_poly_seq, nmr_poly_seq)
            chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, 'nmr-star', cif_poly_seq, nmr_poly_seq, seq_align)

            if chain_assign is not None:

                for ca in chain_assign:
                    ref_chain_id = ca['ref_chain_id']
                    test_chain_id = ca['test_chain_id']

                    sa = next(sa for sa in seq_align
                              if sa['ref_chain_id'] == ref_chain_id
                              and sa['test_chain_id'] == test_chain_id)

                    if sa['conflict'] > 0 or sa['unmapped'] == 0:
                        continue

                    ps1 = next(ps for ps in nmr_poly_seq if ps['chain_id'] == test_chain_id)
                    ps2 = next(ps for ps in cif_poly_seq if ps['auth_chain_id'] == ref_chain_id)

                    self.__reg.pA.setReferenceSequence(ps1['comp_id'], 'REF' + test_chain_id)
                    self.__reg.pA.addTestSequence(ps2['comp_id'], test_chain_id)
                    self.__reg.pA.doAlign()

                    myAlign = self.__reg.pA.getAlignment(test_chain_id)

                    length = len(myAlign)

                    _matched, unmapped, conflict, offset_1, offset_2 = getScoreOfSeqAlign(myAlign)

                    if conflict == 0 and unmapped > 0:

                        nmr_seq_ids, cif_auth_seq_ids = [], []

                        for i in range(length):
                            if str(myAlign[i][0]) != '.' and i < len(ps1['seq_id']):
                                nmr_seq_ids.append(ps1['seq_id'][i])
                            else:
                                nmr_seq_ids.append(None)

                        for i in range(length):
                            if str(myAlign[i][1]) != '.' and i < len(ps2['seq_id']):
                                cif_auth_seq_ids.append(ps2['auth_seq_id'][i])
                            else:
                                cif_auth_seq_ids.append(None)

                        for i in range(length):
                            nmr_comp_id, cif_comp_id = str(myAlign[i][0]), str(myAlign[i][1])

                            if nmr_comp_id == cif_comp_id:
                                continue

                            if cif_comp_id == '.' and nmr_comp_id != '.':
                                nmr_seq_id = nmr_seq_ids[i] - offset_1 if nmr_seq_ids[i] is not None else None
                                if nmr_seq_id is not None:
                                    offset = None
                                    for _offset in range(1, 20):
                                        if i + _offset < length:
                                            _myPr = myAlign[i + _offset]
                                            if _myPr[0] == _myPr[1]:
                                                offset = _offset
                                                break
                                        if i - _offset >= 0:
                                            _myPr = myAlign[i - _offset]
                                            if _myPr[0] == _myPr[1]:
                                                offset = -_offset
                                                break

                                    if offset is not None and cif_auth_seq_ids[i + offset] is not None:
                                        cif_auth_seq_id = cif_auth_seq_ids[i + offset] - offset - offset_2
                                        self.__reg.nmr_ext_poly_seq.append({'auth_chain_id': ps2['auth_chain_id'],
                                                                            'auth_seq_id': cif_auth_seq_id,
                                                                            'auth_comp_id': nmr_comp_id})

        suspended_errors_for_lazy_eval = []

        def consume_suspended_message():

            if len(suspended_errors_for_lazy_eval) > 0:
                for msg in suspended_errors_for_lazy_eval:
                    for k, v in msg.items():
                        self.__reg.report.error.appendDescription(k, v)
                suspended_errors_for_lazy_eval.clear()

        def deal_pea_warn_message(file_name, listener, ignore_error):

            if listener.warningMessage is not None:

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}
                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        if g not in EMPTY_VALUE:
                            msg_dict['sf_framecode'] = g[1]
                            msg_dict['description'] = warn.replace(f', {g[1]}', '')

                    if warn.startswith('[Concatenated sequence]'):
                        self.__reg.report.warning.appendDescription('concatenated_sequence', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch]'):
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {warn}\n")

                    elif warn.startswith('[Atom not found]'):
                        if not self.__reg.remediation_mode or 'Macromolecules page' not in warn:
                            consume_suspended_message()

                            self.__reg.report.warning.appendDescription('assigned_peak_atom_not_found', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")
                        else:
                            self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Hydrogen not instantiated]'):
                        if (self.__reg.remediation_mode or self.__reg.internal_mode) and not self.__reg.conversion_server:
                            pass
                        else:
                            consume_suspended_message()

                        self.__reg.report.warning.appendDescription('hydrogen_not_instantiated', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Coordinate issue]'):
                        # consume_suspended_message()

                        self.__reg.report.warning.appendDescription('coordinate_issue', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Invalid atom nomenclature]'):
                        consume_suspended_message()

                        # DAOTHER-8905: change warning level from 'invalid_atom_nomenclature' error to 'atom_nomenclature_mismatch' warning
                        # because we accept atom nomenclature provided by depositor for peak list
                        self.__reg.report.warning.appendDescription('atom_nomenclature_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        # consume_suspended_message()

                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Sequence mismatch warning]'):
                        self.__reg.report.warning.appendDescription('sequence_mismatch', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                        if SEQ_MISMATCH_WARNING_PAT.match(warn):
                            g = SEQ_MISMATCH_WARNING_PAT.search(warn).groups()
                            d = {'auth_chain_id': g[2],
                                 'auth_seq_id': int(g[0]),
                                 'auth_comp_id': g[1]}
                            if d not in self.__reg.nmr_ext_poly_seq:
                                self.__reg.nmr_ext_poly_seq.append(d)

                    elif warn.startswith('[Inconsistent peak assignment]'):
                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Conflicted peak assignment]'):
                        self.__reg.report.warning.appendDescription('conflicted_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif warn.startswith('[Missing data]'):
                        if (self.__reg.remediation_mode or self.__reg.internal_mode) and not self.__reg.conversion_server:
                            pass
                        else:
                            self.__reg.report.error.appendDescription('missing_mandatory_item', msg_dict)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {warn}\n")

                    elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                        # consume_suspended_message()

                        self.__reg.report.error.appendDescription('anomalous_data', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ ValueError  - {warn}\n")

                    elif warn.startswith('[Range value warning]')\
                            or (warn.startswith('[Range value error]') and self.__reg.remediation_mode):
                        self.__reg.report.warning.appendDescription('inconsistent_peak_list', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                    elif not ignore_error:
                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.validateLegacyPk() ++ KeyError  - " + warn)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ KeyError  - {warn}\n")

        def deal_pea_warn_message_for_lazy_eval(file_name, listener):

            if listener.warningMessage is not None:

                def_sf_framecode = ''
                for warn in listener.warningMessage:

                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        if g[1] not in EMPTY_VALUE:
                            def_sf_framecode = g[1]
                            break

                for warn in listener.warningMessage:

                    msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}
                    if INCONSISTENT_RESTRAINT_WARNING_PAT.match(warn):
                        g = INCONSISTENT_RESTRAINT_WARNING_PAT.search(warn).groups()
                        msg_dict['sf_framecode'] = g[1] if g[1] not in EMPTY_VALUE else def_sf_framecode
                        msg_dict['description'] = warn.replace(f', {g[1]}', '')

                    if warn.startswith('[Sequence mismatch]'):
                        suspended_errors_for_lazy_eval.append({'sequence_mismatch': msg_dict})

                    # elif warn.startswith('[Atom not found]'):
                    #     if not self.__reg.remediation_mode or 'Macromolecules page' not in warn:
                    #         suspended_errors_for_lazy_eval.append({'atom_not_found': msg_dict})

                    # elif warn.startswith('[Hydrogen not instantiated]'):
                    #     if self.__reg.remediation_mode:
                    #         pass
                    #     else:
                    #         suspended_errors_for_lazy_eval.append({'hydrogen_not_instantiated': msg_dict})

                    # elif warn.startswith('[Coordinate issue]'):
                    #     suspended_errors_for_lazy_eval.append({'coordinate_issue': msg_dict})

                    # elif warn.startswith('[Invalid atom nomenclature]'):
                    #     suspended_errors_for_lazy_eval.append({'invalid_atom_nomenclature': msg_dict})

                    elif warn.startswith('[Invalid atom selection]') or warn.startswith('[Invalid data]'):
                        suspended_errors_for_lazy_eval.append({'invalid_data': msg_dict})

                    # elif warn.startswith('[Range value error]') and not self.__reg.remediation_mode:
                    #     suspended_errors_for_lazy_eval.append({'anomalous_data': msg_dict})

        fileListId = self.__reg.file_path_list_len

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
            file_path = ar['file_name']

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            ignore_error = False if 'ignore_error' not in input_source_dic else input_source_dic['ignore_error']

            fileListId += 1

            if file_type.startswith('nm-res') or file_type.startswith('nm-aux'):
                continue

            if self.__reg.remediation_mode and os.path.exists(file_path + '-ignored'):
                continue

            if os.path.exists(file_path + '-corrected'):
                file_path = file_path + '-corrected'

            file_name = input_source_dic['file_name']

            original_file_name = os.path.basename(file_path)
            # """
            # if 'original_file_name' in input_source_dic:
            #     if input_source_dic['original_file_name'] is not None:
            #         original_file_name = os.path.basename(input_source_dic['original_file_name'])
            #     if file_name != original_file_name and original_file_name is not None:
            #         file_name = f"{original_file_name} ({file_name})"
            # if original_file_name in EMPTY_VALUE:
            #     original_file_name = file_name
            # """
            if file_type == 'nm-pea-any':

                warn = f"We could not identify peak list file format of {file_name!r}. "\
                    "In order to add file format support in the future, "\
                    "the contents is temporarily stored as-is in the _Spectral_peak_list.Text_data tag "\
                    "and will be converted during future data remediation if the data matches a known peak list format."

                self.__reg.report.warning.appendDescription('unsupported_peak_list',
                                                            {'file_name': file_name, 'description': warn, 'inheritable': True})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Warning  - {warn}\n")

                continue

            if file_type == 'nm-pea-xea' and not has_aux_xea and not self.__reg.internal_mode:

                err = f"XEASY PROT file should be uploaded to verify XEASY spectral peak list file {file_name!r}."

                suspended_errors_for_lazy_eval.append({'missing_mandatory_content':
                                                       {'file_name': file_name, 'description': err}})

            _content_subtype = input_source_dic['content_subtype']

            if _content_subtype is None or len(_content_subtype) == 0:
                continue

            _pk_format_name = getRestraintFormatName(file_type)
            pk_format_name = _pk_format_name.split()[0]
            a_pk_format_name = ('an ' if pk_format_name[0] in ('AINMX') else 'a ') + _pk_format_name

            suspended_errors_for_lazy_eval.clear()

            if file_type == 'nm-pea-ari':
                reader = AriaPKReader(self.__reg.verbose, self.__reg.log,
                                      self.__reg.representative_model_id,
                                      self.__reg.representative_alt_id,
                                      self.__reg.mr_atom_name_mapping,
                                      self.__reg.cR, self.__reg.caC,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                if None not in (parser_err_listener, listener)\
                   and (parser_err_listener.getMessageList() is None or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, None, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = AriaPKReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (ARIA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-bar':
                reader = BarePKReader(self.__reg.verbose, self.__reg.log,
                                      self.__reg.representative_model_id,
                                      self.__reg.representative_alt_id,
                                      self.__reg.mr_atom_name_mapping,
                                      self.__reg.cR, self.__reg.caC,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                if None not in (parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, None, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = BarePKReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-ccp':
                reader = CcpnPKReader(self.__reg.verbose, self.__reg.log,
                                      self.__reg.representative_model_id,
                                      self.__reg.representative_alt_id,
                                      self.__reg.mr_atom_name_mapping,
                                      self.__reg.cR, self.__reg.caC,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = CcpnPKReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (CCPN) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-oli':
                reader = OliviaPKReader(self.__reg.verbose, self.__reg.log,
                                        self.__reg.representative_model_id,
                                        self.__reg.representative_alt_id,
                                        self.__reg.mr_atom_name_mapping,
                                        self.__reg.cR, self.__reg.caC,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = OliviaPKReader(self.__reg.verbose, self.__reg.log,
                                                self.__reg.representative_model_id,
                                                self.__reg.representative_alt_id,
                                                self.__reg.mr_atom_name_mapping,
                                                self.__reg.cR, self.__reg.caC,
                                                self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (OLIVIA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-pip':
                reader = NmrPipePKReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = NmrPipePKReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (NMRPIPE) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-pon':
                reader = PonderosaPKReader(self.__reg.verbose, self.__reg.log,
                                           self.__reg.representative_model_id,
                                           self.__reg.representative_alt_id,
                                           self.__reg.mr_atom_name_mapping,
                                           self.__reg.cR, self.__reg.caC,
                                           self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = PonderosaPKReader(self.__reg.verbose, self.__reg.log,
                                                   self.__reg.representative_model_id,
                                                   self.__reg.representative_alt_id,
                                                   self.__reg.mr_atom_name_mapping,
                                                   self.__reg.cR, self.__reg.caC,
                                                   self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                   reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (PONDEROSA) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-spa':
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                reader = SparkyPKReader(self.__reg.verbose, self.__reg.log,
                                        self.__reg.representative_model_id,
                                        self.__reg.representative_alt_id,
                                        self.__reg.mr_atom_name_mapping,
                                        self.__reg.cR, self.__reg.caC,
                                        self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                spa_type = 'default'
                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    skip, spa_type = deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)
                    if skip and spa_type == 'default':
                        continue

                if spa_type == 'reverse':
                    self.__reg.list_id_counter = copy.copy(__list_id_counter)

                    reader = SparkyRPKReader(self.__reg.verbose, self.__reg.log,
                                             self.__reg.representative_model_id,
                                             self.__reg.representative_alt_id,
                                             self.__reg.mr_atom_name_mapping,
                                             self.__reg.cR, self.__reg.caC,
                                             self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    _list_id_counter = copy.copy(self.__reg.list_id_counter)

                    listener, parser_err_listener, lexer_err_listener =\
                        reader.parse(file_path, self.__reg.cifPath,
                                     createSfDict=create_sf_dict, originalFileName=original_file_name,
                                     listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                     entryId=self.__reg.entry_id,
                                     csLoops=self.__reg.lp_data['chem_shift'])

                    _content_subtype = listener.getContentSubtype() if listener is not None else None
                    if _content_subtype is not None and len(_content_subtype) == 0:
                        _content_subtype = None

                    if None not in (lexer_err_listener, parser_err_listener, listener)\
                       and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                            or _content_subtype is not None):
                        if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                            continue

                if spa_type == 'no':
                    if self.__reg.internal_mode:
                        self.__reg.list_id_counter = copy.copy(__list_id_counter)

                        reader = SparkyNPKReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        _list_id_counter = copy.copy(self.__reg.list_id_counter)

                        listener, parser_err_listener, lexer_err_listener =\
                            reader.parse(file_path, self.__reg.cifPath,
                                         createSfDict=create_sf_dict, originalFileName=original_file_name,
                                         listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                         entryId=self.__reg.entry_id,
                                         csLoops=self.__reg.lp_data['chem_shift'])

                        _content_subtype = listener.getContentSubtype() if listener is not None else None
                        if _content_subtype is not None and len(_content_subtype) == 0:
                            _content_subtype = None

                        if None not in (lexer_err_listener, parser_err_listener, listener)\
                           and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                                or _content_subtype is not None):
                            if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                                continue

                    else:
                        warn = "Neither peak height nor peak volume are included in the file. Please re-upload the spectral peak list file."
                        msg_dict = {'file_name': file_name, 'description': warn, 'inheritable': True}

                        self.__reg.report.error.appendDescription('format_issue', msg_dict)

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {warn}\n")
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        if spa_type == 'reverse':
                            reader = SparkyRPKReader(self.__reg.verbose, self.__reg.log,
                                                     self.__reg.representative_model_id,
                                                     self.__reg.representative_alt_id,
                                                     self.__reg.mr_atom_name_mapping,
                                                     self.__reg.cR, self.__reg.caC,
                                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                     reasons)
                        elif spa_type == 'default' or not self.__reg.internal_mode:
                            reader = SparkyPKReader(self.__reg.verbose, self.__reg.log,
                                                    self.__reg.representative_model_id,
                                                    self.__reg.representative_alt_id,
                                                    self.__reg.mr_atom_name_mapping,
                                                    self.__reg.cR, self.__reg.caC,
                                                    self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                    reasons)
                        else:
                            reader = SparkyNPKReader(self.__reg.verbose, self.__reg.log,
                                                     self.__reg.representative_model_id,
                                                     self.__reg.representative_alt_id,
                                                     self.__reg.mr_atom_name_mapping,
                                                     self.__reg.cR, self.__reg.caC,
                                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                     reasons)
                            reader.setInternalMode(self.__reg.internal_mode)

                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (SPARKY) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-sps':
                reader = SparkySPKReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = SparkySPKReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (SPARKY) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-top':
                reader = TopSpinPKReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                # ignore lexer error because of incomplete XML file format
                listener, parser_err_listener, _ =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                if None not in (parser_err_listener, listener)\
                   and (parser_err_listener.getMessageList() is None or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, None, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = TopSpinPKReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (TOPSPIN) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-vie':
                __list_id_counter = copy.copy(self.__reg.list_id_counter)

                reader = NmrViewPKReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                vie_type = 'default'
                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    skip, vie_type = deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)
                    if skip and vie_type == 'default':
                        continue

                if vie_type != 'default':
                    self.__reg.list_id_counter = copy.copy(__list_id_counter)

                    reader = NmrViewNPKReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                    reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                    reader.setInternalMode(self.__reg.internal_mode)

                    _list_id_counter = copy.copy(self.__reg.list_id_counter)

                    listener, parser_err_listener, lexer_err_listener =\
                        reader.parse(file_path, self.__reg.cifPath,
                                     createSfDict=create_sf_dict, originalFileName=original_file_name,
                                     listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                     entryId=self.__reg.entry_id,
                                     csLoops=self.__reg.lp_data['chem_shift'])

                    _content_subtype = listener.getContentSubtype() if listener is not None else None
                    if _content_subtype is not None and len(_content_subtype) == 0:
                        _content_subtype = None

                    if None not in (lexer_err_listener, parser_err_listener, listener)\
                       and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                            or _content_subtype is not None):
                        if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                            continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        if vie_type == 'default':
                            reader = NmrViewPKReader(self.__reg.verbose, self.__reg.log,
                                                     self.__reg.representative_model_id,
                                                     self.__reg.representative_alt_id,
                                                     self.__reg.mr_atom_name_mapping,
                                                     self.__reg.cR, self.__reg.caC,
                                                     self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                     reasons)
                        else:
                            reader = NmrViewNPKReader(self.__reg.verbose, self.__reg.log,
                                                      self.__reg.representative_model_id,
                                                      self.__reg.representative_alt_id,
                                                      self.__reg.mr_atom_name_mapping,
                                                      self.__reg.cR, self.__reg.caC,
                                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                      reasons)

                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (NMRVIEW) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-vnm':
                reader = VnmrPKReader(self.__reg.verbose, self.__reg.log,
                                      self.__reg.representative_model_id,
                                      self.__reg.representative_alt_id,
                                      self.__reg.mr_atom_name_mapping,
                                      self.__reg.cR, self.__reg.caC,
                                      self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = VnmrPKReader(self.__reg.verbose, self.__reg.log,
                                              self.__reg.representative_model_id,
                                              self.__reg.representative_alt_id,
                                              self.__reg.mr_atom_name_mapping,
                                              self.__reg.cR, self.__reg.caC,
                                              self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                              reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (VNMR) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-xea':
                reader = XeasyPKReader(self.__reg.verbose, self.__reg.log,
                                       self.__reg.representative_model_id,
                                       self.__reg.representative_alt_id,
                                       self.__reg.mr_atom_name_mapping,
                                       self.__reg.cR, self.__reg.caC,
                                       self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                       xeasyAtomNumberDict)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id,
                                 csLoops=self.__reg.lp_data['chem_shift'])

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None and listener.warningMessage is not None and len(listener.warningMessage) > 0:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = XeasyPKReader(self.__reg.verbose, self.__reg.log,
                                               self.__reg.representative_model_id,
                                               self.__reg.representative_alt_id,
                                               self.__reg.mr_atom_name_mapping,
                                               self.__reg.cR, self.__reg.caC,
                                               self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                               xeasyAtomNumberDict,
                                               reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id,
                                                      csLoops=self.__reg.lp_data['chem_shift'])

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (XEASY) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

            elif file_type == 'nm-pea-xwi':
                reader = XwinNmrPKReader(self.__reg.verbose, self.__reg.log,
                                         self.__reg.representative_model_id,
                                         self.__reg.representative_alt_id,
                                         self.__reg.mr_atom_name_mapping,
                                         self.__reg.cR, self.__reg.caC,
                                         self.__reg.ccU, self.__reg.csStat, self.__reg.nefT)
                reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                reader.setInternalMode(self.__reg.internal_mode)

                _list_id_counter = copy.copy(self.__reg.list_id_counter)

                listener, parser_err_listener, lexer_err_listener =\
                    reader.parse(file_path, self.__reg.cifPath,
                                 createSfDict=create_sf_dict, originalFileName=original_file_name,
                                 listIdCounter=self.__reg.list_id_counter, reservedListIds=reserved_list_ids,
                                 entryId=self.__reg.entry_id)

                _content_subtype = listener.getContentSubtype() if listener is not None else None
                if _content_subtype is not None and len(_content_subtype) == 0:
                    _content_subtype = None

                if None not in (lexer_err_listener, parser_err_listener, listener)\
                   and ((lexer_err_listener.getMessageList() is None and parser_err_listener.getMessageList() is None)
                        or _content_subtype is not None):
                    if deal_lexer_or_parser_error(a_pk_format_name, file_name, lexer_err_listener, parser_err_listener)[0]:
                        continue

                if listener is not None:
                    reasons = listener.getReasonsForReparsing()

                    if reasons is not None:
                        deal_pea_warn_message_for_lazy_eval(file_name, listener)

                        reader = XwinNmrPKReader(self.__reg.verbose, self.__reg.log,
                                                 self.__reg.representative_model_id,
                                                 self.__reg.representative_alt_id,
                                                 self.__reg.mr_atom_name_mapping,
                                                 self.__reg.cR, self.__reg.caC,
                                                 self.__reg.ccU, self.__reg.csStat, self.__reg.nefT,
                                                 reasons)
                        reader.enforcePeakRowFormat(self.__reg.enforce_peak_row_format)
                        reader.setInternalMode(self.__reg.internal_mode)

                        listener, _, _ = reader.parse(file_path, self.__reg.cifPath,
                                                      createSfDict=create_sf_dict, originalFileName=original_file_name,
                                                      listIdCounter=_list_id_counter, reservedListIds=reserved_list_ids,
                                                      entryId=self.__reg.entry_id)

                    deal_pea_warn_message(file_name, listener, ignore_error)

                    poly_seq = listener.getPolymerSequence()
                    if poly_seq is not None:
                        input_source.setItemValue('polymer_sequence', poly_seq)
                        poly_seq_set.append(poly_seq)

                    seq_align = listener.getSequenceAlignment()
                    if seq_align is not None:
                        self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

                    if create_sf_dict:
                        if len(listener.getContentSubtype()) == 0 and not ignore_error:
                            err = f"Failed to validate spectral peak list file (XWINNMR) {file_name!r}."

                            self.__reg.report.error.appendDescription('internal_error',
                                                                      f"+{self.__class_name__}.validateLegacyPk() ++ Error  - " + err)

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.validateLegacyPk() ++ Error  - {err}\n")

                        self.__reg.list_id_counter, sf_dict = listener.getSfDict()
                        if sf_dict is not None:
                            for k, v in sf_dict.items():
                                content_subtype = contentSubtypeOf(k[0])
                                if content_subtype not in pk_sf_dict_holder:
                                    pk_sf_dict_holder[content_subtype] = []
                                for sf in v:
                                    if sf not in pk_sf_dict_holder[content_subtype]:
                                        pk_sf_dict_holder[content_subtype].append(sf)

        if len(self.__reg.star_data) > 0 and isinstance(self.__reg.star_data[0], pynmrstar.Entry):
            master_entry = self.__reg.star_data[0]

            if content_subtype in pk_sf_dict_holder:

                for sf in pk_sf_dict_holder[content_subtype]:

                    cs_list = get_first_sf_tag(sf['saveframe'], 'Chemical_shift_list')

                    if cs_list in EMPTY_VALUE:
                        sf_category = SF_CATEGORIES['nmr-star']['chem_shift']
                        cs_sf_list = master_entry.get_saveframes_by_category(sf_category)
                        if len(cs_sf_list) == 1:
                            set_sf_tag(sf['saveframe'], 'Chemical_shift_list', get_first_sf_tag(cs_sf_list[0], 'Sf_framecode'))

                    # prevent duplication of spectral peak list
                    data_file_name = get_first_sf_tag(sf['saveframe'], 'Data_file_name')
                    if data_file_name not in EMPTY_VALUE\
                       and len(master_entry.get_saveframes_by_tag_and_value('Data_file_name', data_file_name)) > 0:
                        continue

                    try:
                        master_entry.add_saveframe(sf['saveframe'])
                    except ValueError:
                        pass

                self.__reg.pk_sf_holder = pk_sf_dict_holder['spectral_peak']

        if len(poly_seq_set) > 1:

            poly_seq_rst = None
            for idx, poly_seq in enumerate(poly_seq_set):
                if idx == 0:
                    poly_seq_rst = poly_seq
                    continue
                for ps in poly_seq:
                    chain_id = ps['chain_id']
                    for seq_id, comp_id in zip(ps['seq_id'], ps['comp_id']):
                        updatePolySeqRst(poly_seq_rst, chain_id, seq_id, comp_id)

            poly_seq_model = self.__reg.caC['polymer_sequence']

            sortPolySeqRst(poly_seq_rst)

            file_type = 'nm-pea-any'

            seq_align, _ = alignPolymerSequence(self.__reg.pA, poly_seq_model, poly_seq_rst, conservative=False)
            chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type,
                                                    poly_seq_model, poly_seq_rst, seq_align)

            if chain_assign is not None:

                if len(poly_seq_model) == len(poly_seq_rst):

                    chain_mapping = {}

                    for ca in chain_assign:
                        ref_chain_id = ca['ref_chain_id']
                        test_chain_id = ca['test_chain_id']

                        if ref_chain_id != test_chain_id:
                            chain_mapping[test_chain_id] = ref_chain_id

                    if len(chain_mapping) == len(poly_seq_model):

                        for ps in poly_seq_rst:
                            if ps['chain_id'] in chain_mapping:
                                ps['chain_id'] = chain_mapping[ps['chain_id']]

                        seq_align, _ = alignPolymerSequence(self.__reg.pA, poly_seq_model, poly_seq_rst, conservative=False)
                        chain_assign, _ = assignPolymerSequence(self.__reg.pA, self.__reg.ccU, file_type,
                                                                poly_seq_model, poly_seq_rst, seq_align)

                    trimSequenceAlignment(seq_align, chain_assign)

            input_source.setItemValue('polymer_sequence', poly_seq_rst)

            self.__reg.report.sequence_alignment.setItemValue(f'model_poly_seq_vs_{content_subtype}', seq_align)

        if proc_nmr_ext_poly_seq and len(self.__reg.nmr_ext_poly_seq) > 0:
            entity_assembly = self.__reg.caC['entity_assembly']
            auth_chain_ids = list(set(d['auth_chain_id'] for d in self.__reg.nmr_ext_poly_seq))
            for auth_chain_id in auth_chain_ids:
                item = next(item for item in entity_assembly if auth_chain_id in item['auth_asym_id'].split(','))
                if item['entity_type'] == 'polymer':
                    poly_type = item['entity_poly_type']
                    if poly_type.startswith('polypeptide'):
                        unknown_residue = 'UNK'
                    elif any(True for comp_id in item['comp_id_set'] if comp_id in ('DA', 'DC', 'DG', 'DT'))\
                            and any(True for comp_id in item['comp_id_set'] if comp_id in ('A', 'C', 'G', 'U')):
                        unknown_residue = 'DN'
                    elif poly_type == 'polydeoxyribonucleotide':
                        unknown_residue = 'DN'
                    elif poly_type == 'polyribonucleotide':
                        unknown_residue = 'N'
                    else:
                        continue
                    ps = next(ps for ps in self.__reg.caC['polymer_sequence'] if ps['auth_chain_id'] == auth_chain_id)
                    auth_seq_ids = [d['auth_seq_id'] for d in self.__reg.nmr_ext_poly_seq if d['auth_chain_id'] == auth_chain_id]
                    auth_seq_ids.extend(list(filter(None, ps['auth_seq_id'])))
                    min_auth_seq_id = min(auth_seq_ids)
                    max_auth_seq_id = max(auth_seq_ids)
                    for auth_seq_id in range(min_auth_seq_id, max_auth_seq_id + 1):
                        if auth_seq_id not in ps['auth_seq_id']\
                           and not any(True for d in self.__reg.nmr_ext_poly_seq
                                       if d['auth_chain_id'] == auth_chain_id and d['auth_seq_id'] == auth_seq_id):
                            self.__reg.nmr_ext_poly_seq.append({'auth_chain_id': auth_chain_id,
                                                                'auth_seq_id': auth_seq_id,
                                                                'auth_comp_id': unknown_residue})

            self.__reg.nmr_ext_poly_seq = sorted(self.__reg.nmr_ext_poly_seq, key=itemgetter('auth_chain_id', 'auth_seq_id'))

        return not self.__reg.report.isError()

    def validateSaxsMr(self) -> bool:
        """ Validate SAXS restraint files.
        """

        if self.__reg.combined_mode:
            return True

        if AR_FILE_PATH_LIST_KEY not in self.__reg.inputParamDict:
            return True

        content_subtype = 'saxs_restraint'

        if self.__reg.list_id_counter is None:
            self.__reg.list_id_counter = {}
        if self.__reg.mr_sf_dict_holder is None:
            self.__reg.mr_sf_dict_holder = {}

        if content_subtype not in self.__reg.mr_sf_dict_holder:
            self.__reg.mr_sf_dict_holder[content_subtype] = []

        fileListId = self.__reg.file_path_list_len

        for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
            file_path = ar['file_name']

            input_source = self.__reg.report.input_sources[fileListId]
            input_source_dic = input_source.get()

            file_type = input_source_dic['file_type']

            fileListId += 1

            if file_type != 'nm-res-sax':
                continue

            file_name = input_source_dic['file_name']

            original_file_name = os.path.basename(file_name).replace('-corrected', '').replace('-selected-as-res-sax', '')
            if '-div_' in original_file_name:
                original_file_name = None
                # if 'original_file_name' in input_source_dic:
                #     if input_source_dic['original_file_name'] is not None:
                #         original_file_name = os.path.basename(input_source_dic['original_file_name'])

            sf_item = {}

            title = _row = None

            _q_value = 0.0

            lp_count = 0

            with open(file_path, 'r') as ifh:
                for line in ifh:

                    line = ' '.join(line.split())

                    _line = line.split()

                    len_line = len(_line)

                    if len_line == 0:
                        continue

                    if line.startswith('#') or line.startswith('!'):

                        if len(line) == 1:
                            continue

                        __line = line[1:].split(' ')

                        if len(__line) == 0 or line[1].startswith('#') or line[1].startswith('!'):
                            continue

                        title_can = __line[0]
                        if len(title_can) == 0 and len(__line) > 1:
                            title_can = __line[1]

                        try:
                            float(title_can)
                            continue
                        except ValueError:
                            if len(title_can) > 1\
                               and '(' not in title_can and ')' not in title_can\
                               and '[' not in title_can and ']' not in title_can:
                                if len(title_can) > 0:
                                    title = title_can
                            _row = None

                        continue

                    if len_line != 3:
                        continue

                    try:

                        q_value = float(_line[0])
                        float(_line[1])
                        float(_line[2])

                        dstFunc = {'weight': '1.0',
                                   'target_value': _line[1].replace('E', 'e'),
                                   'target_value_uncertainty': _line[2].replace('E', 'e')}

                        if _q_value == 0.0:

                            if len(sf_item) > 0 and sf_item['id'] > 0:
                                self.__reg.mr_sf_dict_holder[content_subtype].append(sf_item)
                                lp_count += 1

                            self.__reg.list_id_counter = incListIdCounter(content_subtype, self.__reg.list_id_counter, reduced=False)

                            list_id = self.__reg.list_id_counter[content_subtype]

                            restraint_name = getRestraintName(content_subtype)

                            sf_framecode = restraint_name.replace(' ', '_').lower() + f'_{list_id}'

                            if original_file_name is not None:
                                title = original_file_name

                            sf = getSaveframe(content_subtype, sf_framecode, list_id, self.__reg.entry_id, title, reduced=False)

                            _restraint_name = restraint_name.split()

                            sf_item = {'file_type': file_type, 'saveframe': sf, 'list_id': list_id,
                                       'id': 0, 'index_id': 0,
                                       'constraint_type': ' '.join(_restraint_name[:-1])}

                            lp = getLoop(content_subtype, reduced=False)

                            sf.add_loop(lp)
                            sf_item['loop'] = lp

                            if _row is not None:

                                sf_item['loop'].add_data(_row)

                                sf_item['id'] = sf_item['index_id'] = 1

                                _row = None

                        if q_value > _q_value:

                            sf_item['id'] += 1
                            sf_item['index_id'] += 1

                            row = getRow('saxs', sf_item['id'], sf_item['index_id'], None, None, _line[0].replace('E', 'e'),
                                         sf_item['list_id'], self.__reg.entry_id, dstFunc, None, None, None, None, None)
                            sf_item['loop'].add_data(row)

                            _q_value = q_value

                        else:

                            _row = getRow('saxs', 1, 1, None, None, _line[0].replace('E', 'e'),
                                          sf_item['list_id'] + 1, self.__reg.entry_id, dstFunc, None, None, None, None, None)

                            _q_value = 0.0

                    except ValueError:
                        continue

            if len(sf_item) > 0 and sf_item['id'] > 0:
                self.__reg.mr_sf_dict_holder[content_subtype].append(sf_item)

                lp_count += 1
                input_source.setItemValue('content_subtype', {'saxs_restraint': lp_count})

        if len(self.__reg.mr_sf_dict_holder[content_subtype]) == 0:
            del self.__reg.mr_sf_dict_holder[content_subtype]

        return True

    def updateConstraintStats(self) -> bool:
        """ Update _Constraint_stat_list saveframe.
        """

        if (not self.__reg.combined_mode and not self.__reg.remediation_mode)\
           or self.__reg.dstPath is None\
           or self.__reg.release_mode\
           or self.__reg.report.getInputSourceIdOfCoord() < 0:
            return True

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        file_type = input_source_dic['file_type']

        if file_type == 'nef':
            return True

        if len(self.__reg.star_data) == 0 or not isinstance(self.__reg.star_data[0], pynmrstar.Entry):
            return False

        master_entry = self.__reg.star_data[0]

        if 'constraint_statistics' in self.__reg.sf_category_list and self.__reg.list_id_counter is not None:
            return False

        if self.__reg.bmrb_only and self.__reg.internal_mode and self.__reg.bmrb_id is not None:
            master_entry.entry_id = self.__reg.bmrb_id
        else:
            master_entry.entry_id = f'nef_{self.__reg.entry_id.lower()}'

        self.__reg.c2S.set_entry_id(master_entry, self.__reg.entry_id)

        # refresh _Constraint_stat_list saveframe

        sf_framecode = 'constraint_statistics'

        cst_sfs = master_entry.get_saveframes_by_category(sf_framecode)

        if len(cst_sfs) > 0:

            if self.__reg.list_id_counter is None:
                master_entry.remove_saveframe(sf_framecode)

            else:

                lp_category = '_Constraint_file'

                key_items = [{'name': 'ID', 'type': 'int'},
                             {'name': 'Constraint_filename', 'type': 'str'},
                             {'name': 'Block_ID', 'type': 'int'},
                             ]
                data_items = [{'name': 'Constraint_type', 'type': 'str', 'mandatory': True},
                              {'name': 'Constraint_subtype', 'type': 'str'},
                              {'name': 'Constraint_subsubtype', 'type': 'str',
                               'enum': ('ambi', 'simple')},
                              {'name': 'Constraint_number', 'type': 'int'},
                              {'name': 'Constraint_stat_list_ID', 'type': 'int', 'mandatory': True,
                               'default': '1', 'default-from': 'parent'},
                              {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                              ]

                allowed_tags = ['ID', 'Constraint_filename', 'Software_ID', 'Software_label', 'Software_name',
                                'Block_ID', 'Constraint_type', 'Constraint_subtype', 'Constraint_subsubtype', 'Constraint_number',
                                'Sf_ID', 'Entry_ID', 'Constraint_stat_list_ID']

                try:

                    for parent_pointer, cst_sf in enumerate(cst_sfs, start=1):

                        self.__reg.nefT.check_data(cst_sf, lp_category, key_items, data_items,
                                                   allowed_tags, None, parent_pointer=parent_pointer,
                                                   enforce_allowed_tags=(file_type == 'nmr-star'),
                                                   excl_missing_data=self.__reg.excl_missing_data)

                    return True

                except Exception:
                    for cst_sf in reversed(cst_sfs):
                        del master_entry[cst_sf]

        self.__reg.sf_category_list, self.__reg.lp_category_list = self.__reg.nefT.get_inventory_list(master_entry)

        # initialize loop counter
        lp_counts = {t: 0 for t in NMR_CONTENT_SUBTYPES}

        # increment loop counter of each content subtype
        for lp_category in self.__reg.lp_category_list:
            if lp_category in LP_CATEGORIES[file_type].values():
                lp_counts[[k for k, v in LP_CATEGORIES[file_type].items() if v == lp_category][0]] += 1

        content_subtypes = {k: lp_counts[k] for k in lp_counts if lp_counts[k] > 0}

        input_source.setItemValue('content_subtype', content_subtypes)

        sf_item = {}

        cst_sf = pynmrstar.Saveframe.from_scratch(sf_framecode)
        cst_sf.set_tag_prefix('_Constraint_stat_list')
        cst_sf.add_tag('Sf_category', sf_framecode)
        cst_sf.add_tag('Sf_framecode', sf_framecode)
        cst_sf.add_tag('Entry_ID', self.__reg.entry_id)
        cst_sf.add_tag('ID', 1)
        if self.__reg.srcName is not None:
            cst_sf.add_tag('Data_file_name', self.__reg.srcName)

        if has_key_value(input_source_dic, 'content_subtype'):

            for content_subtype in input_source_dic['content_subtype']:

                if content_subtype == 'dist_restraint':

                    sf_category = SF_CATEGORIES[file_type][content_subtype]
                    lp_category = LP_CATEGORIES[file_type][content_subtype]

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        avr_method = get_first_sf_tag(sf, 'NOE_dist_averaging_method')
                        if len(avr_method) > 0 and avr_method not in EMPTY_VALUE:
                            cst_sf.add_tag('NOE_dist_averaging_method', avr_method)
                            break

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        if sf_framecode not in sf_item:
                            sf_item[sf_framecode] = {'constraint_type': 'distance', 'constraint_subsubtype': 'simple'}
                            constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                            if len(constraint_type) > 0 and constraint_type not in EMPTY_VALUE:
                                sf_item[sf_framecode]['constraint_subtype'] = constraint_type

                        lp = sf.get_loop(lp_category)

                        item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                        id_col = lp.tags.index('ID')
                        member_logic_code_col = lp.tags.index('Member_logic_code') if 'Member_logic_code' in lp.tags else -1
                        auth_asym_id_1_col = lp.tags.index('Auth_asym_ID_1')
                        auth_seq_id_1_col = lp.tags.index('Auth_seq_ID_1')
                        auth_asym_id_2_col = lp.tags.index('Auth_asym_ID_2')
                        auth_seq_id_2_col = lp.tags.index('Auth_seq_ID_2')
                        comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                        comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                        atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                        atom_id_2_col = lp.tags.index(item_names['atom_id_2'])

                        try:
                            target_value_col = lp.tags.index(item_names['target_value'])
                        except ValueError:
                            target_value_col = -1
                        try:
                            lower_limit_col = lp.tags.index(item_names['lower_limit'])
                        except ValueError:
                            lower_limit_col = -1
                        try:
                            upper_limit_col = lp.tags.index(item_names['upper_limit'])
                        except ValueError:
                            upper_limit_col = -1
                        try:
                            lower_linear_limit_col = lp.tags.index(item_names['lower_linear_limit'])
                        except ValueError:
                            lower_linear_limit_col = -1
                        try:
                            upper_linear_limit_col = lp.tags.index(item_names['upper_linear_limit'])
                        except ValueError:
                            upper_linear_limit_col = -1

                        has_or_code = False

                        potential_type = get_first_sf_tag(sf, 'Potential_type')
                        has_potential_type = len(potential_type) > 0 and potential_type not in EMPTY_VALUE and potential_type != 'unknown'

                        _potential_type = None
                        count = 0

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                if member_logic_code_col != -1 and row[member_logic_code_col] == 'OR':
                                    has_or_code = True
                                continue
                            prev_id = _id
                            count += 1
                            if not has_potential_type:
                                dst_func = {}
                                if target_value_col != -1 and row[target_value_col] not in EMPTY_VALUE:
                                    dst_func['target_value'] = float(row[target_value_col])
                                if lower_limit_col != -1 and row[lower_limit_col] not in EMPTY_VALUE:
                                    dst_func['lower_limit'] = float(row[lower_limit_col])
                                if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE:
                                    dst_func['upper_limit'] = float(row[upper_limit_col])
                                if lower_linear_limit_col != -1 and row[lower_linear_limit_col] not in EMPTY_VALUE:
                                    dst_func['lower_linear_limit'] = float(row[lower_linear_limit_col])
                                if upper_linear_limit_col != -1 and row[upper_linear_limit_col] not in EMPTY_VALUE:
                                    dst_func['upper_linear_limit'] = float(row[upper_linear_limit_col])
                                if _potential_type is None:
                                    _potential_type = getPotentialType(file_type, 'dist', dst_func)
                                else:
                                    if getPotentialType(file_type, 'dist', dst_func) != _potential_type:
                                        has_potential_type = True

                        if not has_potential_type and _potential_type is not None:
                            set_sf_tag(sf, 'Potential_type', _potential_type)

                        sf_item[sf_framecode]['id'] = count

                        if has_or_code:

                            prev_id = -1
                            for row in lp:
                                if member_logic_code_col != -1 and row[member_logic_code_col] == 'OR':
                                    _id = int(row[id_col])
                                    if _id != prev_id:
                                        _atom1 = {'chain_id': row[auth_asym_id_1_col],
                                                  'seq_id':
                                                  int(row[auth_seq_id_1_col]) if row[auth_seq_id_1_col] not in EMPTY_VALUE else None,
                                                  'comp_id': row[comp_id_1_col],
                                                  'atom_id': row[atom_id_1_col]}
                                        _atom2 = {'chain_id': row[auth_asym_id_2_col],
                                                  'seq_id':
                                                  int(row[auth_seq_id_2_col]) if row[auth_seq_id_2_col] not in EMPTY_VALUE else None,
                                                  'comp_id': row[comp_id_2_col],
                                                  'atom_id': row[atom_id_2_col]}
                                        prev_id = _id
                                        continue
                                    atom1 = {'chain_id': row[auth_asym_id_1_col],
                                             'seq_id':
                                             int(row[auth_seq_id_1_col]) if row[auth_seq_id_1_col] not in EMPTY_VALUE else None,
                                             'comp_id': row[comp_id_1_col],
                                             'atom_id': row[atom_id_1_col]}
                                    atom2 = {'chain_id': row[auth_asym_id_2_col],
                                             'seq_id':
                                             int(row[auth_seq_id_2_col]) if row[auth_seq_id_2_col] not in EMPTY_VALUE else None,
                                             'comp_id': row[comp_id_2_col],
                                             'atom_id': row[atom_id_2_col]}
                                    if isAmbigAtomSelection([_atom1, atom1], self.__reg.csStat)\
                                       or isAmbigAtomSelection([_atom2, atom2], self.__reg.csStat):
                                        sf_item[sf_framecode]['constraint_subsubtype'] = 'ambi'
                                        break
                                    _atom1, _atom2 = atom1, atom2

                            if sf_item[sf_framecode]['constraint_subsubtype'] == 'ambi':

                                if 'pre' in sf_framecode or 'paramag' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'paramagnetic relaxation'
                                if 'cidnp' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'photo cidnp'
                                if 'csp' in sf_framecode or 'perturb' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'chemical shift perturbation'
                                if 'mutat' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'mutation'
                                if 'protect' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'hydrogen exchange protection'
                                if 'symm' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'symmetry'

                        if sf_item[sf_framecode]['constraint_subsubtype'] == 'simple':

                            metal_coord = disele_bond = disulf_bond = hydrog_bond = False

                            for row in lp:
                                comp_id_1 = row[comp_id_1_col]
                                comp_id_2 = row[comp_id_2_col]
                                atom_id_1 = row[atom_id_1_col]
                                atom_id_2 = row[atom_id_2_col]

                                if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE:
                                    continue

                                atom_id_1_ = atom_id_1[0]
                                atom_id_2_ = atom_id_2[0]
                                if comp_id_1 == atom_id_1 or comp_id_2 == atom_id_2:
                                    metal_coord = True
                                elif 'SE' in (atom_id_1, atom_id_2):
                                    disele_bond = True
                                elif 'SG' in (atom_id_1, atom_id_2):
                                    disulf_bond = True
                                elif (atom_id_1_ == 'F' and atom_id_2_ in PROTON_BEGIN_CODE)\
                                        or (atom_id_2_ == 'F' and atom_id_1_ in PROTON_BEGIN_CODE):
                                    hydrog_bond = True
                                elif (atom_id_1_ == 'F' and atom_id_2_ == 'F') or (atom_id_2_ == 'F' and atom_id_1_ == 'F'):
                                    hydrog_bond = True
                                elif (atom_id_1_ == 'O' and atom_id_2_ in PROTON_BEGIN_CODE)\
                                        or (atom_id_2_ == 'O' and atom_id_1_ in PROTON_BEGIN_CODE):
                                    hydrog_bond = True
                                elif (atom_id_1_ == 'O' and atom_id_2_ == 'N') or (atom_id_2_ == 'O' and atom_id_1_ == 'N'):
                                    hydrog_bond = True
                                elif (atom_id_1_ == 'O' and atom_id_2_ == 'O') or (atom_id_2_ == 'O' and atom_id_1_ == 'O'):
                                    hydrog_bond = True
                                elif (atom_id_1_ == 'N' and atom_id_2_ in PROTON_BEGIN_CODE)\
                                        or (atom_id_2_ == 'N' and atom_id_1_ in PROTON_BEGIN_CODE):
                                    hydrog_bond = True
                                elif (atom_id_1_ == 'N' and atom_id_2_ == 'N') or (atom_id_2_ == 'N' and atom_id_1_ == 'N'):
                                    hydrog_bond = True

                            if not metal_coord and not disele_bond and not disulf_bond and not hydrog_bond:
                                if 'build' in sf_framecode and 'up' in sf_framecode:
                                    if 'roe' in sf_framecode:
                                        sf_item[sf_framecode]['constraint_subtype'] = 'ROE build-up'
                                    else:
                                        sf_item[sf_framecode]['constraint_subtype'] = 'NOE build-up'

                                elif 'not' in sf_framecode and 'seen' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'NOE not seen'

                                elif 'roe' in sf_framecode:
                                    sf_item[sf_framecode]['constraint_subtype'] = 'ROE'

                                sf_item[sf_framecode]['constraint_subtype'] = 'NOE'

                            elif metal_coord and not disele_bond and not disulf_bond and not hydrog_bond:
                                sf_item[sf_framecode]['constraint_subtype'] = 'metal coordination'

                            elif not metal_coord and disele_bond and not disulf_bond and not hydrog_bond:
                                sf_item[sf_framecode]['constraint_subtype'] = 'diselenide bond'

                            elif not metal_coord and not disele_bond and disulf_bond and not hydrog_bond:
                                sf_item[sf_framecode]['constraint_subtype'] = 'disulfide bond'

                            elif not metal_coord and not disele_bond and not disulf_bond and hydrog_bond:
                                sf_item[sf_framecode]['constraint_subtype'] = 'hydrogen bond'

                    NOE_tot_num =\
                        NOE_intraresidue_tot_num =\
                        NOE_sequential_tot_num =\
                        NOE_medium_range_tot_num =\
                        NOE_long_range_tot_num =\
                        NOE_unique_tot_num =\
                        NOE_intraresidue_unique_tot_num =\
                        NOE_sequential_unique_tot_num =\
                        NOE_medium_range_unique_tot_num =\
                        NOE_long_range_unique_tot_num =\
                        NOE_unamb_intramol_tot_num =\
                        NOE_unamb_intermol_tot_num =\
                        NOE_ambig_intramol_tot_num =\
                        NOE_ambig_intermol_tot_num =\
                        NOE_interentity_tot_num =\
                        NOE_other_tot_num = 0

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        potential_type = get_first_sf_tag(sf, 'Potential_type')
                        if 'lower' in potential_type:
                            continue
                        if 'constraint_subtype' in sf_item[sf_framecode] and 'NOE' in sf_item[sf_framecode]['constraint_subtype']:
                            # NOE_tot_num += sf_item[sf_framecode]['id']

                            lp = sf.get_loop(lp_category)

                            item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                            id_col = lp.tags.index('ID')
                            chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                            chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                            seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                            seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                            comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                            comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                            atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                            atom_id_2_col = lp.tags.index(item_names['atom_id_2'])
                            # try:
                            #     member_logic_code_col = lp.tags.index(item_names['member_logic_code'])
                            # except ValueError:
                            #     member_logic_code_col = -1
                            try:
                                combination_id_col = lp.tags.index(item_names['combination_id'])
                            except ValueError:
                                combination_id_col = -1
                            try:
                                upper_limit_col = lp.tags.index(item_names['upper_limit'])
                            except ValueError:
                                upper_limit_col = -1

                            prev_id = -1

                            for row in lp:
                                _id = int(row[id_col])
                                # member_logic_code = row[member_logic_code_col] if member_logic_code_col != -1 else None
                                try:
                                    chain_id_1 = int(row[chain_id_1_col])
                                    chain_id_2 = int(row[chain_id_2_col])
                                    seq_id_1 = int(row[seq_id_1_col])
                                    seq_id_2 = int(row[seq_id_2_col])
                                except (ValueError, TypeError):
                                    continue
                                comp_id_1 = row[comp_id_1_col]
                                comp_id_2 = row[comp_id_2_col]
                                atom_id_1 = row[atom_id_1_col]
                                atom_id_2 = row[atom_id_2_col]

                                if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE or _id == prev_id:
                                    continue

                                prev_id = _id

                                combination_id = row[combination_id_col] if combination_id_col != -1 else None
                                upper_limit = float(row[upper_limit_col])\
                                    if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE else None

                                offset = abs(seq_id_1 - seq_id_2)
                                ambig = upper_limit is not None and (upper_limit <= DIST_AMBIG_LOW or upper_limit >= DIST_AMBIG_UP)
                                uniq = combination_id in EMPTY_VALUE and not ambig

                                NOE_tot_num += 1

                                if uniq:
                                    NOE_unique_tot_num += 1

                                if chain_id_1 == chain_id_2:
                                    if uniq:
                                        NOE_unamb_intramol_tot_num += 1
                                    else:
                                        NOE_ambig_intramol_tot_num += 1
                                    if offset == 0:
                                        NOE_intraresidue_tot_num += 1
                                        if uniq:
                                            NOE_intraresidue_unique_tot_num += 1
                                    elif offset == 1:
                                        NOE_sequential_tot_num += 1
                                        if uniq:
                                            NOE_sequential_unique_tot_num += 1
                                    elif offset < 5:
                                        NOE_medium_range_tot_num += 1
                                        if uniq:
                                            NOE_medium_range_unique_tot_num += 1
                                    else:
                                        NOE_long_range_tot_num += 1
                                        if uniq:
                                            NOE_long_range_unique_tot_num += 1
                                else:
                                    NOE_interentity_tot_num += 1
                                    if uniq:
                                        NOE_unamb_intermol_tot_num += 1
                                    else:
                                        NOE_ambig_intermol_tot_num += 1

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        potential_type = get_first_sf_tag(sf, 'Potential_type')
                        if 'lower' in potential_type:
                            continue
                        constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                        if constraint_type in ('paramagnetic relaxation',
                                               'photo cidnp',
                                               'chemical shift perturbation',
                                               'mutation',
                                               'symmetry'):
                            NOE_other_tot_num += sf_item[sf_framecode]['id']

                    if NOE_tot_num > 0:
                        cst_sf.add_tag('NOE_tot_num', NOE_tot_num)
                        cst_sf.add_tag('NOE_intraresidue_tot_num', NOE_intraresidue_tot_num)
                        cst_sf.add_tag('NOE_sequential_tot_num', NOE_sequential_tot_num)
                        cst_sf.add_tag('NOE_medium_range_tot_num', NOE_medium_range_tot_num)
                        cst_sf.add_tag('NOE_long_range_tot_num', NOE_long_range_tot_num)
                        cst_sf.add_tag('NOE_unique_tot_num', NOE_unique_tot_num)
                        cst_sf.add_tag('NOE_intraresidue_unique_tot_num', NOE_intraresidue_unique_tot_num)
                        cst_sf.add_tag('NOE_sequential_unique_tot_num', NOE_sequential_unique_tot_num)
                        cst_sf.add_tag('NOE_medium_range_unique_tot_num', NOE_medium_range_unique_tot_num)
                        cst_sf.add_tag('NOE_long_range_unique_tot_num', NOE_long_range_unique_tot_num)
                        cst_sf.add_tag('NOE_unamb_intramol_tot_num', NOE_unamb_intramol_tot_num)
                        cst_sf.add_tag('NOE_unamb_intermol_tot_num', NOE_unamb_intermol_tot_num)
                        cst_sf.add_tag('NOE_ambig_intramol_tot_num', NOE_ambig_intramol_tot_num)
                        cst_sf.add_tag('NOE_ambig_intermol_tot_num', NOE_ambig_intermol_tot_num)
                        cst_sf.add_tag('NOE_interentity_tot_num', NOE_interentity_tot_num)
                        cst_sf.add_tag('NOE_other_tot_num', NOE_other_tot_num)

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        avr_method = get_first_sf_tag(sf, 'ROE_dist_averaging_method')
                        if len(avr_method) > 0 or avr_method not in EMPTY_VALUE:
                            cst_sf.add_tag('ROE_dist_averaging_method', avr_method)
                            break

                    ROE_tot_num =\
                        ROE_intraresidue_tot_num =\
                        ROE_sequential_tot_num =\
                        ROE_medium_range_tot_num =\
                        ROE_long_range_tot_num =\
                        ROE_unambig_intramol_tot_num =\
                        ROE_unambig_intermol_tot_num =\
                        ROE_ambig_intramol_tot_num =\
                        ROE_ambig_intermol_tot_num =\
                        ROE_other_tot_num = 0

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        potential_type = get_first_sf_tag(sf, 'Potential_type')
                        if 'lower' in potential_type:
                            continue
                        if 'constraint_subtype' in sf_item[sf_framecode] and 'ROE' in sf_item[sf_framecode]['constraint_subtype']:
                            # ROE_tot_num += sf_item[sf_framecode]['id']

                            lp = sf.get_loop(lp_category)

                            item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                            id_col = lp.tags.index('ID')
                            chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                            chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                            seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                            seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                            comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                            comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                            atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                            atom_id_2_col = lp.tags.index(item_names['atom_id_2'])
                            # try:
                            #     member_logic_code_col = lp.tags.index(item_names['member_logic_code'])
                            # except ValueError:
                            #     member_logic_code_col = -1
                            try:
                                combination_id_col = lp.tags.index(item_names['combination_id'])
                            except ValueError:
                                combination_id_col = -1
                            try:
                                upper_limit_col = lp.tags.index(item_names['upper_limit'])
                            except ValueError:
                                upper_limit_col = -1

                            prev_id = -1

                            for row in lp:
                                _id = int(row[id_col])
                                # member_logic_code = row[member_logic_code_col] if member_logic_code_col != -1 else None
                                try:
                                    chain_id_1 = int(row[chain_id_1_col])
                                    chain_id_2 = int(row[chain_id_2_col])
                                    seq_id_1 = int(row[seq_id_1_col])
                                    seq_id_2 = int(row[seq_id_2_col])
                                except (ValueError, TypeError):
                                    continue
                                comp_id_1 = row[comp_id_1_col]
                                comp_id_2 = row[comp_id_2_col]
                                atom_id_1 = row[atom_id_1_col]
                                atom_id_2 = row[atom_id_2_col]

                                if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE or _id == prev_id:
                                    continue

                                prev_id = _id

                                combination_id = row[combination_id_col] if combination_id_col != -1 else None
                                upper_limit = float(row[upper_limit_col])\
                                    if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE else None

                                offset = abs(seq_id_1 - seq_id_2)
                                ambig = upper_limit is not None and (upper_limit <= DIST_AMBIG_LOW or upper_limit >= DIST_AMBIG_UP)
                                uniq = combination_id in EMPTY_VALUE and not ambig

                                ROE_tot_num += 1

                                if chain_id_1 == chain_id_2:
                                    if uniq:
                                        ROE_unambig_intramol_tot_num += 1
                                    else:
                                        ROE_ambig_intramol_tot_num += 1
                                    if offset == 0:
                                        ROE_intraresidue_tot_num += 1
                                    elif offset == 1:
                                        ROE_sequential_tot_num += 1
                                    elif offset < 5:
                                        ROE_medium_range_tot_num += 1
                                    else:
                                        ROE_long_range_tot_num += 1
                                else:
                                    ROE_other_tot_num += 1
                                    if uniq:
                                        ROE_unambig_intermol_tot_num += 1
                                    else:
                                        ROE_ambig_intermol_tot_num += 1

                    if ROE_tot_num > 0:
                        cst_sf.add_tag('ROE_tot_num', ROE_tot_num)
                        cst_sf.add_tag('ROE_intraresidue_tot_num', ROE_intraresidue_tot_num)
                        cst_sf.add_tag('ROE_sequential_tot_num', ROE_sequential_tot_num)
                        cst_sf.add_tag('ROE_medium_range_tot_num', ROE_medium_range_tot_num)
                        cst_sf.add_tag('ROE_long_range_tot_num', ROE_long_range_tot_num)
                        cst_sf.add_tag('ROE_unambig_intramol_tot_num', ROE_unambig_intramol_tot_num)
                        cst_sf.add_tag('ROE_unambig_intermol_tot_num', ROE_unambig_intermol_tot_num)
                        cst_sf.add_tag('ROE_ambig_intramol_tot_num', ROE_ambig_intramol_tot_num)
                        cst_sf.add_tag('ROE_ambig_intermol_tot_num', ROE_ambig_intermol_tot_num)
                        cst_sf.add_tag('ROE_other_tot_num', ROE_other_tot_num)

                elif content_subtype == 'dihed_restraint':

                    sf_category = SF_CATEGORIES[file_type][content_subtype]
                    lp_category = LP_CATEGORIES[file_type][content_subtype]

                    auth_to_entity_type = self.__reg.caC['auth_to_entity_type']

                    Dihedral_angle_tot_num = 0
                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        if sf_framecode not in sf_item:
                            sf_item[sf_framecode] = {'constraint_type': 'dihedral angle'}

                        lp = sf.get_loop(lp_category)

                        item_names = ITEM_NAMES_IN_DIHED_LOOP[file_type]
                        id_col = lp.tags.index('ID')
                        try:
                            target_value_col = lp.tags.index(item_names['target_value'])
                        except ValueError:
                            target_value_col = -1
                        try:
                            lower_limit_col = lp.tags.index(item_names['lower_limit'])
                        except ValueError:
                            lower_limit_col = -1
                        try:
                            upper_limit_col = lp.tags.index(item_names['upper_limit'])
                        except ValueError:
                            upper_limit_col = -1
                        try:
                            lower_linear_limit_col = lp.tags.index(item_names['lower_linear_limit'])
                        except ValueError:
                            lower_linear_limit_col = -1
                        try:
                            upper_linear_limit_col = lp.tags.index(item_names['upper_linear_limit'])
                        except ValueError:
                            upper_linear_limit_col = -1

                        potential_type = get_first_sf_tag(sf, 'Potential_type')
                        has_potential_type = len(potential_type) > 0 and potential_type not in EMPTY_VALUE and potential_type != 'unknown'

                        _potential_type = None
                        count = 0

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            count += 1
                            if not has_potential_type:
                                dst_func = {}
                                if target_value_col != -1 and row[target_value_col] not in EMPTY_VALUE:
                                    dst_func['target_value'] = float(row[target_value_col])
                                if lower_limit_col != -1 and row[lower_limit_col] not in EMPTY_VALUE:
                                    dst_func['lower_limit'] = float(row[lower_limit_col])
                                if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE:
                                    dst_func['upper_limit'] = float(row[upper_limit_col])
                                if lower_linear_limit_col != -1 and row[lower_linear_limit_col] not in EMPTY_VALUE:
                                    dst_func['lower_linear_limit'] = float(row[lower_linear_limit_col])
                                if upper_linear_limit_col != -1 and row[upper_linear_limit_col] not in EMPTY_VALUE:
                                    dst_func['upper_linear_limit'] = float(row[upper_linear_limit_col])
                                if _potential_type is None:
                                    _potential_type = getPotentialType(file_type, 'dihed', dst_func)
                                else:
                                    if getPotentialType(file_type, 'dihed', dst_func) != _potential_type:
                                        has_potential_type = True

                        if not has_potential_type and _potential_type is not None:
                            set_sf_tag(sf, 'Potential_type', _potential_type)

                        sf_item[sf_framecode]['id'] = count
                        Dihedral_angle_tot_num += count

                    if Dihedral_angle_tot_num > 0:
                        cst_sf.add_tag('Dihedral_angle_tot_num', Dihedral_angle_tot_num)

                    Protein_dihedral_angle_tot_num =\
                        Protein_phi_angle_tot_num =\
                        Protein_psi_angle_tot_num =\
                        Protein_chi_one_angle_tot_num =\
                        Protein_other_angle_tot_num = 0

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                        lp = sf.get_loop(lp_category)

                        id_col = lp.tags.index('ID')
                        auth_asym_id_col = lp.tags.index('Auth_asym_ID_2')
                        auth_seq_id_col = lp.tags.index('Auth_seq_ID_2')
                        auth_comp_id_col = lp.tags.index('Auth_comp_ID_2')
                        angle_name_col = lp.tags.index('Torsion_angle_name')

                        _protein_angles = _other_angles = 0
                        _protein_bb_angles = _protein_oth_angles = 0

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            auth_asym_id = row[auth_asym_id_col]
                            try:
                                auth_seq_id = int(row[auth_seq_id_col]) if row[auth_seq_id_col] not in EMPTY_VALUE else None
                            except (ValueError, TypeError):
                                continue
                            auth_comp_id = row[auth_comp_id_col]
                            angle_name = row[angle_name_col]
                            if angle_name is None:
                                continue

                            seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                            if seq_key in auth_to_entity_type:
                                entity_type = auth_to_entity_type[seq_key]

                                if 'peptide' in entity_type:
                                    Protein_dihedral_angle_tot_num += 1
                                    _protein_angles += 1
                                    if angle_name == 'PHI':
                                        Protein_phi_angle_tot_num += 1
                                        _protein_bb_angles += 1
                                    elif angle_name == 'PSI':
                                        Protein_psi_angle_tot_num += 1
                                        _protein_bb_angles += 1
                                    elif angle_name == 'CHI1':
                                        Protein_chi_one_angle_tot_num += 1
                                        _protein_oth_angles += 1
                                    else:
                                        Protein_other_angle_tot_num += 1
                                        _protein_oth_angles += 1
                                else:
                                    _other_angles += 1

                        if _protein_angles > _other_angles == 0:
                            sf_item[sf_framecode]['constraint_type'] = 'protein dihedral angle'

                            tagNames = [t[0] for t in sf.tags]

                            if 'Constraint_type' not in tagNames:
                                sf_item[sf_framecode]['constraint_subtype'] = 'backbone chemical shifts'
                                sf.add_tag('Constraint_subtype', 'backbone chemical shifts')

                    if Protein_dihedral_angle_tot_num > 0:
                        cst_sf.add_tag('Protein_dihedral_angle_tot_num', Protein_dihedral_angle_tot_num)
                        cst_sf.add_tag('Protein_phi_angle_tot_num', Protein_phi_angle_tot_num)
                        cst_sf.add_tag('Protein_psi_angle_tot_num', Protein_psi_angle_tot_num)
                        cst_sf.add_tag('Protein_chi_one_angle_tot_num', Protein_chi_one_angle_tot_num)
                        cst_sf.add_tag('Protein_other_angle_tot_num', Protein_other_angle_tot_num)

                    NA_dihedral_angle_tot_num =\
                        NA_alpha_angle_tot_num =\
                        NA_beta_angle_tot_num =\
                        NA_gamma_angle_tot_num =\
                        NA_delta_angle_tot_num =\
                        NA_epsilon_angle_tot_num =\
                        NA_chi_angle_tot_num =\
                        NA_other_angle_tot_num =\
                        NA_amb_dihedral_angle_tot_num = 0

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                        lp = sf.get_loop(lp_category)

                        id_col = lp.tags.index('ID')
                        auth_asym_id_col = lp.tags.index('Auth_asym_ID_2')
                        auth_seq_id_col = lp.tags.index('Auth_seq_ID_2')
                        auth_comp_id_col = lp.tags.index('Auth_comp_ID_2')
                        angle_name_col = lp.tags.index('Torsion_angle_name')

                        _na_angles = _other_angles = 0

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            auth_asym_id = row[auth_asym_id_col]
                            try:
                                auth_seq_id = int(row[auth_seq_id_col]) if row[auth_seq_id_col] not in EMPTY_VALUE else None
                            except (ValueError, TypeError):
                                continue
                            auth_comp_id = row[auth_comp_id_col]
                            angle_name = row[angle_name_col]
                            if angle_name is None:
                                continue

                            seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                            if seq_key in auth_to_entity_type:
                                entity_type = auth_to_entity_type[seq_key]

                                if 'nucleotide' in entity_type:
                                    NA_dihedral_angle_tot_num += 1
                                    _na_angles += 1
                                    if angle_name == 'ALPHA':
                                        NA_alpha_angle_tot_num += 1
                                    elif angle_name == 'BETA':
                                        NA_beta_angle_tot_num += 1
                                    elif angle_name == 'GAMMA':
                                        NA_gamma_angle_tot_num += 1
                                    elif angle_name == 'DELTA':
                                        NA_delta_angle_tot_num += 1
                                    elif angle_name == 'EPSILON':
                                        NA_epsilon_angle_tot_num += 1
                                    elif angle_name == 'CHI':
                                        NA_chi_angle_tot_num += 1
                                    elif angle_name == 'PPA':
                                        NA_amb_dihedral_angle_tot_num += 1
                                    else:
                                        NA_other_angle_tot_num += 1
                                else:
                                    _other_angles += 1

                        if _na_angles > _other_angles:
                            sf_item[sf_framecode]['constraint_type'] = 'nucleic acid dihedral angle'

                            tagNames = [t[0] for t in sf.tags]

                            if 'Constraint_type' not in tagNames:
                                sf_item[sf_framecode]['constraint_subtype'] = 'unknown'
                                sf.add_tag('Constraint_type', 'unknown')

                    if NA_dihedral_angle_tot_num > 0:
                        cst_sf.add_tag('NA_dihedral_angle_tot_num', NA_dihedral_angle_tot_num)
                        cst_sf.add_tag('NA_alpha_angle_tot_num', NA_alpha_angle_tot_num)
                        cst_sf.add_tag('NA_beta_angle_tot_num', NA_beta_angle_tot_num)
                        cst_sf.add_tag('NA_gamma_angle_tot_num', NA_gamma_angle_tot_num)
                        cst_sf.add_tag('NA_delta_angle_tot_num', NA_delta_angle_tot_num)
                        cst_sf.add_tag('NA_epsilon_angle_tot_num', NA_epsilon_angle_tot_num)
                        cst_sf.add_tag('NA_chi_angle_tot_num', NA_chi_angle_tot_num)
                        cst_sf.add_tag('NA_other_angle_tot_num', NA_other_angle_tot_num)
                        cst_sf.add_tag('NA_amb_dihedral_angle_tot_num', NA_amb_dihedral_angle_tot_num)

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                        lp = sf.get_loop(lp_category)

                        id_col = lp.tags.index('ID')
                        auth_asym_id_col = lp.tags.index('Auth_asym_ID_2')
                        auth_seq_id_col = lp.tags.index('Auth_seq_ID_2')
                        auth_comp_id_col = lp.tags.index('Auth_comp_ID_2')
                        angle_name_col = lp.tags.index('Torsion_angle_name')

                        _br_angles = _other_angles = 0

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            auth_asym_id = row[auth_asym_id_col]
                            try:
                                auth_seq_id = int(row[auth_seq_id_col]) if row[auth_seq_id_col] not in EMPTY_VALUE else None
                            except (ValueError, TypeError):
                                continue
                            auth_comp_id = row[auth_comp_id_col]
                            angle_name = row[angle_name_col]
                            if angle_name is None:
                                continue

                            seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                            if seq_key in auth_to_entity_type:
                                entity_type = auth_to_entity_type[seq_key]

                                if 'saccharide' in entity_type:
                                    _br_angles += 1
                                else:
                                    _other_angles += 1

                        if _br_angles > _other_angles:
                            sf_item[sf_framecode]['constraint_type'] = 'carbohydrate dihedral angle'  # DAOTHER-9471

                            tagNames = [t[0] for t in sf.tags]

                            if 'Constraint_type' not in tagNames:
                                sf_item[sf_framecode]['constraint_subtype'] = 'unknown'
                                sf.add_tag('Constraint_type', 'unknown')

                elif content_subtype == 'rdc_restraint':

                    sf_category = SF_CATEGORIES[file_type][content_subtype]
                    lp_category = LP_CATEGORIES[file_type][content_subtype]

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        if sf_framecode not in sf_item:
                            sf_item[sf_framecode] = {'constraint_type': 'dipolar coupling', 'constraint_subtype': 'RDC'}  # DAOTHER-9471

                        lp = sf.get_loop(lp_category)

                        item_names = ITEM_NAMES_IN_RDC_LOOP[file_type]
                        id_col = lp.tags.index('ID')
                        try:
                            target_value_col = lp.tags.index(item_names['target_value'])
                        except ValueError:
                            target_value_col = -1
                        try:
                            lower_limit_col = lp.tags.index(item_names['lower_limit'])
                        except ValueError:
                            lower_limit_col = -1
                        try:
                            upper_limit_col = lp.tags.index(item_names['upper_limit'])
                        except ValueError:
                            upper_limit_col = -1
                        try:
                            lower_linear_limit_col = lp.tags.index(item_names['lower_linear_limit'])
                        except ValueError:
                            lower_linear_limit_col = -1
                        try:
                            upper_linear_limit_col = lp.tags.index(item_names['upper_linear_limit'])
                        except ValueError:
                            upper_linear_limit_col = -1

                        potential_type = get_first_sf_tag(sf, 'Potential_type')
                        has_potential_type = len(potential_type) > 0 and potential_type not in EMPTY_VALUE and potential_type != 'unknown'

                        _potential_type = None
                        count = 0

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            count += 1
                            if not has_potential_type:
                                dst_func = {}
                                if target_value_col != -1 and row[target_value_col] not in EMPTY_VALUE:
                                    dst_func['target_value'] = float(row[target_value_col])
                                if lower_limit_col != -1 and row[lower_limit_col] not in EMPTY_VALUE:
                                    dst_func['lower_limit'] = float(row[lower_limit_col])
                                if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE:
                                    dst_func['upper_limit'] = float(row[upper_limit_col])
                                if lower_linear_limit_col != -1 and row[lower_linear_limit_col] not in EMPTY_VALUE:
                                    dst_func['lower_linear_limit'] = float(row[lower_linear_limit_col])
                                if upper_linear_limit_col != -1 and row[upper_linear_limit_col] not in EMPTY_VALUE:
                                    dst_func['upper_linear_limit'] = float(row[upper_linear_limit_col])
                                if _potential_type is None:
                                    _potential_type = getPotentialType(file_type, 'rdc', dst_func)
                                else:
                                    if getPotentialType(file_type, 'rdc', dst_func) != _potential_type:
                                        has_potential_type = True

                        if not has_potential_type and _potential_type is not None:
                            set_sf_tag(sf, 'Potential_type', _potential_type)

                        sf_item[sf_framecode]['id'] = count

                    RDC_tot_num =\
                        RDC_HH_tot_num =\
                        RDC_HNC_tot_num =\
                        RDC_NH_tot_num =\
                        RDC_CC_tot_num =\
                        RDC_CN_i_1_tot_num =\
                        RDC_CAHA_tot_num =\
                        RDC_HNHA_tot_num =\
                        RDC_HNHA_i_1_tot_num =\
                        RDC_CAC_tot_num =\
                        RDC_CAN_tot_num =\
                        RDC_other_tot_num =\
                        RDC_intraresidue_tot_num =\
                        RDC_sequential_tot_num =\
                        RDC_medium_range_tot_num =\
                        RDC_long_range_tot_num =\
                        RDC_unambig_intramol_tot_num =\
                        RDC_unambig_intermol_tot_num =\
                        RDC_ambig_intramol_tot_num =\
                        RDC_ambig_intermol_tot_num =\
                        RDC_intermol_tot_num = 0

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                        lp = sf.get_loop(lp_category)

                        # RDC_tot_num += sf_item[sf_framecode]['id']

                        item_names = ITEM_NAMES_IN_RDC_LOOP[file_type]
                        id_col = lp.tags.index('ID')
                        chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                        chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                        seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                        seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                        comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                        atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                        atom_id_2_col = lp.tags.index(item_names['atom_id_2'])
                        try:
                            combination_id_col = lp.tags.index(item_names['combination_id'])
                        except ValueError:
                            combination_id_col = -1

                        prev_id = -1
                        for row in lp:
                            _id = int(row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            chain_id_1 = row[chain_id_1_col]
                            chain_id_2 = row[chain_id_2_col]
                            try:
                                seq_id_1 = int(row[seq_id_1_col]) if row[seq_id_1_col] not in EMPTY_VALUE else None
                                seq_id_2 = int(row[seq_id_2_col]) if row[seq_id_2_col] not in EMPTY_VALUE else None
                            except (ValueError, TypeError):
                                continue
                            comp_id_1 = row[comp_id_1_col]
                            atom_id_1 = row[atom_id_1_col]
                            atom_id_2 = row[atom_id_2_col]

                            if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE:
                                continue

                            combination_id = row[combination_id_col] if combination_id_col != -1 else None

                            vector = {atom_id_1, atom_id_2}
                            offset = abs(seq_id_1 - seq_id_2)

                            RDC_tot_num += 1

                            if chain_id_1 == chain_id_2:
                                if vector == {'H', 'C'} and offset == 1:
                                    RDC_HNC_tot_num += 1
                                elif vector == {'H', 'N'} and offset == 0:
                                    RDC_NH_tot_num += 1
                                elif vector == {'C', 'N'} and offset == 1:
                                    RDC_CN_i_1_tot_num += 1
                                elif vector == {'CA', 'HA'} and offset == 0:
                                    RDC_CAHA_tot_num += 1
                                elif vector == {'H', 'HA'} and offset == 0:
                                    RDC_HNHA_tot_num += 1
                                elif vector == {'H', 'HA'} and offset == 1:
                                    RDC_HNHA_i_1_tot_num += 1
                                elif vector == {'CA', 'C'} and offset == 0:
                                    RDC_CAC_tot_num += 1
                                elif vector == {'CA', 'N'} and offset == 0:
                                    RDC_CAN_tot_num += 1
                                elif atom_id_1[0] == atom_id_2[0]:
                                    if atom_id_1[0] in PROTON_BEGIN_CODE:
                                        RDC_HH_tot_num += 1
                                    elif atom_id_1[0] == 'C':
                                        RDC_CC_tot_num += 1
                                    else:
                                        RDC_other_tot_num += 1
                                elif offset == 0 and comp_id_1 == 'TRP' and vector == {'HE1', 'NE1'}:
                                    RDC_NH_tot_num += 1
                                elif offset == 0 and comp_id_1 == 'ARG' and vector == {'HE', 'NE'}:
                                    RDC_NH_tot_num += 1
                                else:
                                    RDC_other_tot_num += 1

                            if chain_id_1 == chain_id_2:
                                if offset == 0:
                                    RDC_intraresidue_tot_num += 1
                                elif offset == 1:
                                    RDC_sequential_tot_num += 1
                                elif offset < 5:
                                    RDC_medium_range_tot_num += 1
                                else:
                                    RDC_long_range_tot_num += 1
                                if combination_id in EMPTY_VALUE:
                                    RDC_unambig_intramol_tot_num += 1
                                else:
                                    RDC_ambig_intramol_tot_num += 1

                            else:
                                RDC_intermol_tot_num += 1
                                if combination_id in EMPTY_VALUE:
                                    RDC_unambig_intermol_tot_num += 1
                                else:
                                    RDC_ambig_intermol_tot_num += 1

                    if RDC_tot_num > 0:
                        cst_sf.add_tag('RDC_tot_num', RDC_tot_num)
                        cst_sf.add_tag('RDC_HH_tot_num', RDC_HH_tot_num)
                        cst_sf.add_tag('RDC_HNC_tot_num', RDC_HNC_tot_num)
                        cst_sf.add_tag('RDC_NH_tot_num', RDC_NH_tot_num)
                        cst_sf.add_tag('RDC_CC_tot_num', RDC_CC_tot_num)
                        cst_sf.add_tag('RDC_CN_i_1_tot_num', RDC_CN_i_1_tot_num)
                        cst_sf.add_tag('RDC_CAHA_tot_num', RDC_CAHA_tot_num)
                        cst_sf.add_tag('RDC_HNHA_tot_num', RDC_HNHA_tot_num)
                        cst_sf.add_tag('RDC_HNHA_i_1_tot_num', RDC_HNHA_i_1_tot_num)
                        cst_sf.add_tag('RDC_CAC_tot_num', RDC_CAC_tot_num)
                        cst_sf.add_tag('RDC_CAN_tot_num', RDC_CAN_tot_num)
                        cst_sf.add_tag('RDC_other_tot_num', RDC_other_tot_num)
                        cst_sf.add_tag('RDC_intraresidue_tot_num', RDC_intraresidue_tot_num)
                        cst_sf.add_tag('RDC_sequential_tot_num', RDC_sequential_tot_num)
                        cst_sf.add_tag('RDC_medium_range_tot_num', RDC_medium_range_tot_num)
                        cst_sf.add_tag('RDC_long_range_tot_num', RDC_long_range_tot_num)
                        cst_sf.add_tag('RDC_unambig_intramol_tot_num', RDC_unambig_intramol_tot_num)
                        cst_sf.add_tag('RDC_unambig_intermol_tot_num', RDC_unambig_intermol_tot_num)
                        cst_sf.add_tag('RDC_ambig_intramol_tot_num', RDC_ambig_intramol_tot_num)
                        cst_sf.add_tag('RDC_ambig_intermol_tot_num', RDC_ambig_intermol_tot_num)
                        cst_sf.add_tag('RDC_intermol_tot_num', RDC_intermol_tot_num)

                elif content_subtype in self.__reg.mr_content_subtypes:

                    sf_category = SF_CATEGORIES[file_type][content_subtype]
                    lp_category = LP_CATEGORIES[file_type][content_subtype]

                    restraint_name = getRestraintName(content_subtype)
                    _restraint_name = restraint_name.split()

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
                        if sf_framecode not in sf_item:
                            sf_item[sf_framecode] = {'constraint_type': ' '.join(_restraint_name[:-1])}

                            lp = sf.get_loop(lp_category)

                            id_col = lp.tags.index('ID')

                            count = 0

                            prev_id = -1
                            for row in lp:
                                _id = int(row[id_col])
                                if _id == prev_id:
                                    continue
                                prev_id = _id
                                count += 1

                            sf_item[sf_framecode]['id'] = count

        content_subtype = 'dist_restraint'

        sf_category = SF_CATEGORIES[file_type][content_subtype]

        H_bonds_constrained_tot_num = 0
        for sf in master_entry.get_saveframes_by_category(sf_category):
            sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
            try:
                if 'constraint_subtype' in sf_item[sf_framecode]\
                   and sf_item[sf_framecode]['constraint_subtype'] == 'hydrogen bond':
                    H_bonds_constrained_tot_num += sf_item[sf_framecode]['id']
            except KeyError:
                pass

        if H_bonds_constrained_tot_num > 0:
            cst_sf.add_tag('H_bonds_constrained_tot_num', H_bonds_constrained_tot_num)

        SS_bonds_constrained_tot_num = 0
        for sf in master_entry.get_saveframes_by_category(sf_category):
            sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
            try:
                if 'constraint_subtype' in sf_item[sf_framecode]\
                   and sf_item[sf_framecode]['constraint_subtype'] == 'disulfide bond':
                    SS_bonds_constrained_tot_num += sf_item[sf_framecode]['id']
            except KeyError:
                pass

        if SS_bonds_constrained_tot_num > 0:
            cst_sf.add_tag('SS_bonds_constrained_tot_num', SS_bonds_constrained_tot_num)

        Derived_photo_cidnps_tot_num = 0
        for sf in master_entry.get_saveframes_by_category(sf_category):
            sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
            try:
                if 'constraint_subtype' in sf_item[sf_framecode]\
                   and sf_item[sf_framecode]['constraint_subtype'] == 'photo cidnp':
                    Derived_photo_cidnps_tot_num += sf_item[sf_framecode]['id']
            except KeyError:
                pass

        if Derived_photo_cidnps_tot_num > 0:
            cst_sf.add_tag('Derived_photo_cidnps_tot_num', Derived_photo_cidnps_tot_num)

        Derived_paramag_relax_tot_num = 0
        for sf in master_entry.get_saveframes_by_category(sf_category):
            sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')
            try:
                if 'constraint_subtype' in sf_item[sf_framecode]\
                   and sf_item[sf_framecode]['constraint_subtype'] == 'paramagnetic relaxation':
                    Derived_paramag_relax_tot_num += sf_item[sf_framecode]['id']
            except KeyError:
                pass

        if Derived_paramag_relax_tot_num > 0:
            cst_sf.add_tag('Derived_paramag_relax_tot_num', Derived_paramag_relax_tot_num)

        lp_category = '_Constraint_file'
        cf_loop = pynmrstar.Loop.from_scratch(lp_category)

        cf_key_items = [{'name': 'ID', 'type': 'int'},
                        {'name': 'Constraint_filename', 'type': 'str'},
                        # {'name': 'Software_ID', 'type': 'int'},
                        # {'name': 'Software_label', 'type': 'str'},
                        # {'name': 'Software_name', 'type': 'str'},
                        {'name': 'Block_ID', 'type': 'int'},
                        {'name': 'Constraint_type', 'type': 'enum',
                         'enum': ('distance', 'dipolar coupling', 'protein dihedral angle', 'nucleic acid dihedral angle',
                                  'coupling constant', 'chemical shift', 'other angle', 'chemical shift anisotropy',
                                  'hydrogen exchange', 'line broadening', 'pseudocontact shift', 'intervector projection angle',
                                  'protein peptide planarity', 'protein other kinds of constraints',
                                  'nucleic acid base planarity', 'nucleic acid other kinds of constraints',
                                  'carbohydrate dihedral angle')},
                        {'name': 'Constraint_subtype', 'type': 'enum',
                         'enum': ('Not applicable', 'NOE', 'NOE buildup', 'NOE not seen', 'general distance',
                                  'alignment tensor', 'chirality', 'prochirality', 'disulfide bond', 'hydrogen bond',
                                  'symmetry', 'ROE', 'peptide', 'ring', 'PRE')},
                        {'name': 'Constraint_subsubtype', 'type': 'enum',
                         'enum': ('ambi', 'simple')}
                        ]
        cf_data_items = [{'name': 'Constraint_number', 'type': 'int'},
                         {'name': 'Constraint_stat_list_ID', 'type': 'int', 'mandatory': True, 'default': '1', 'default-from': 'parent'},
                         {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                         ]

        tags = [lp_category + '.' + _item['name'] for _item in cf_key_items]
        tags.extend([lp_category + '.' + _item['name'] for _item in cf_data_items])

        cf_loop.add_tag(tags)

        if has_key_value(input_source_dic, 'content_subtype'):

            block_id = 0

            for content_subtype in self.__reg.mr_content_subtypes:
                if content_subtype in input_source_dic['content_subtype']:
                    sf_category = SF_CATEGORIES[file_type][content_subtype]

                    for sf in master_entry.get_saveframes_by_category(sf_category):
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                        row = [None] * len(tags)

                        row[0], row[1] = 1, self.__reg.srcName
                        sf_allowed_tags = SF_ALLOWED_TAGS[file_type][content_subtype]
                        if 'Constraint_file_ID' in sf_allowed_tags:
                            set_sf_tag(sf, 'Constraint_file_ID', 1)
                        if 'Block_ID' in sf_allowed_tags:
                            block_id += 1
                            _block_id = str(block_id)
                            set_sf_tag(sf, 'Block_ID', _block_id)
                            row[2] = _block_id
                        constraint_type = sf_item[sf_framecode]['constraint_type']
                        constraint_subtype = get_first_sf_tag(sf, 'Constraint_type')\
                            if content_subtype != 'other_restraint' else get_first_sf_tag(sf, 'Definition')
                        if len(constraint_subtype) == 0 or constraint_subtype in EMPTY_VALUE:
                            constraint_subtype = sf_item[sf_framecode]['constraint_subtype']\
                                if 'constraint_subtype' in sf_item[sf_framecode] else None
                        if constraint_subtype is not None and constraint_subtype == 'RDC':  # DAOTHER-9471
                            constraint_type = 'dipolar coupling'

                        constraint_subsubtype = sf_item[sf_framecode]['constraint_subsubtype']\
                            if 'constraint_subsubtype' in sf_item[sf_framecode] else None
                        row[3], row[4], row[5], row[6] =\
                            constraint_type, constraint_subtype, constraint_subsubtype, sf_item[sf_framecode]['id']
                        row[7], row[8] = 1, self.__reg.entry_id

                        cf_loop.add_data(row)

            cst_sf.add_loop(cf_loop)

            if len(cf_loop) > 0:
                master_entry.add_saveframe(cst_sf)

        # resolve CYANA distance subtype

        tags = ['Constraint_filename', 'Block_ID', 'Constraint_type', 'Constraint_subtype', 'Constraint_subsubtype']

        if set(tags) & set(cf_loop.tags) != set(tags):
            dat = cf_loop.get_tag(tags)

            for dist_subtype in ['NOE', 'ROE', 'hydrogen bond', 'disulfide bond', 'diselenide bond']:
                cyana_subtype = {}
                for row in dat:
                    if row[2] == 'distance' and row[3] == dist_subtype and row[4] == 'simple':
                        if row[0] not in cyana_subtype:
                            cyana_subtype[row[0]] = []
                        cyana_subtype[row[0]].append(row[1] if isinstance(row[1], str) else str(row[1]))

                if any(True for v in cyana_subtype.values() if len(v) > 1):
                    for v in cyana_subtype.values():
                        if len(v) < 2:
                            continue
                        cyana_potential_type = {}
                        for block_id in v:
                            for sf in master_entry.get_saveframes_by_category('general_distance_constraints'):
                                _block_id = get_first_sf_tag(sf, 'Block_ID')
                                if _block_id in EMPTY_VALUE:
                                    continue
                                if isinstance(_block_id, int):
                                    _block_id = str(_block_id)
                                if _block_id == block_id:
                                    cyana_potential_type[get_first_sf_tag(sf, 'Potential_type').split('-')[0]] = block_id
                        if len(cyana_potential_type) > 1:
                            if 'upper' in cyana_potential_type:
                                block_id = cyana_potential_type['upper']
                                for idx, row in enumerate(dat):
                                    if row[2] == 'distance' and row[3] == dist_subtype and row[4] == 'simple'\
                                       and (row[1] if isinstance(row[1], str) else str(row[1])) == block_id:
                                        cf_loop.data[idx][cf_loop.tags.index('Constraint_subtype')] = f'{dist_subtype} (upper bound)'

        # update _Data_set/Datum loop

        try:

            content_subtype = 'entry_info'

            sf_category = SF_CATEGORIES[file_type][content_subtype]

            sf = master_entry.get_saveframes_by_category(sf_category)[0]

            # update _Data_set loop

            lp_category = '_Data_set'

            loop = next((loop for loop in sf.loops if loop.category == lp_category), None)

            if loop is not None:
                del sf[loop]

            lp = pynmrstar.Loop.from_scratch(lp_category)

            items = ['Type', 'Count', 'Entry_ID']

            tags = [lp_category + '.' + item for item in items]

            lp.add_tag(tags)

            for content_subtype in self.__reg.nmr_rep_content_subtypes:
                sf_category = SF_CATEGORIES[file_type][content_subtype]

                if sf_category.endswith('constraints'):  # ignore non-quantitative data set
                    continue

                count = sum(1 for sf in master_entry.frame_list if sf.category == sf_category)

                if count > 0:
                    row = [sf_category, count, self.__reg.entry_id]
                    lp.add_data(row)
                    lp.data.sort()

            lp.sort_rows('Type')

            sf.add_loop(lp)

            # update _Datum loop

            lp_category = '_Datum'

            loop = next((loop for loop in sf.loops if loop.category == lp_category), None)

            if loop is not None:
                del sf[loop]

            lp = pynmrstar.Loop.from_scratch(lp_category)

            tags = [lp_category + '.' + item for item in items]

            lp.add_tag(tags)

            datum_counter = self.__reg.dpV.getDatumCounter(master_entry)

            for k, v in datum_counter.items():
                row = [k, v, self.__reg.entry_id]
                lp.add_data(row)

            sf.add_loop(lp)

        except IndexError:
            pass

        master_entry = self.__reg.c2S.normalize_str(master_entry)

        master_entry.write_to_file(self.__reg.dstPath,
                                   show_comments=(self.__reg.bmrb_only and self.__reg.internal_mode),
                                   skip_empty_loops=True, skip_empty_tags=False)

        return True

    def mergeLegacyData(self) -> bool:
        """ Merge CS+MR+PK into next NMR combined data files.
        """

        if self.__reg.combined_mode or not self.__reg.remediation_mode or self.__reg.dstPath is None:
            return True

        if len(self.__reg.star_data) == 0 or not isinstance(self.__reg.star_data[0], pynmrstar.Entry):
            return False

        master_entry = self.__reg.star_data[0]

        sf_framecode = 'constraint_statistics'

        cst_sfs = master_entry.get_saveframes_by_category(sf_framecode)

        if len(cst_sfs) > 0:
            for cst_sf in reversed(cst_sfs):
                del master_entry[cst_sf]

        input_source = self.__reg.report.input_sources[0]
        input_source_dic = input_source.get()

        original_file_name = input_source_dic['file_name']
        if 'original_file_name' in input_source_dic and input_source_dic['original_file_name'] is not None:
            original_file_name = os.path.basename(input_source_dic['original_file_name'])

        file_type = 'nmr-star'

        master_entry.entry_id = f'cs_{self.__reg.entry_id.lower()}'

        self.__reg.c2S.set_entry_id(master_entry, self.__reg.entry_id)

        self.__reg.c2S.normalize_str(master_entry)
        # """
        # if self.__reg.remediation_mode and self.__reg.internal_mode:
        #
        #     if isinstance(self.__reg.inputParamDict[CS_FILE_PATH_LIST][0], str):
        #         dir_path = os.path.dirname(self.__reg.inputParamDict[CS_FILE_PATH_LIST][0])
        #     else:
        #         dir_path = os.path.dirname(self.__reg.inputParamDict[CS_FILE_PATH_LIST][0]['file_name'])
        #
        #     dst_cs_path = os.path.join(dir_path, input_source_dic['file_name'])
        #
        #     master_entry.write_to_file(dst_cs_path,
        #                                show_comments=(self.__reg.bmrb_only and self.__reg.internal_mode),
        #                                skip_empty_loops=True, skip_empty_tags=False)
        # """
        if self.__reg.bmrb_only and self.__reg.internal_mode and self.__reg.bmrb_id is not None:
            master_entry.entry_id = self.__reg.bmrb_id
        else:
            master_entry.entry_id = f'nef_{self.__reg.entry_id.lower()}'

        self.__reg.c2S.set_entry_id(master_entry, self.__reg.entry_id)

        # remove _Audit loop if exists

        content_subtype = 'entry_info'

        sf_category = SF_CATEGORIES[file_type][content_subtype]
        lp_category = '_Audit'
        update_audit = False

        sf_list = master_entry.get_saveframes_by_category(sf_category)

        if self.__reg.internal_mode:
            today = datetime.today()
            today_weekday = today.weekday()
            days_ahead = (4 - today_weekday) % 7
            this_friday = today + timedelta(days=days_ahead)

        try:

            sf = sf_list[0]

            try:

                loop = sf.get_loop(lp_category)

                if self.__reg.internal_mode:

                    dat = loop.get_tag(['Revision_ID', 'Update_record'])

                    if any(True for row in dat if row[1] == 'Initial release'):
                        last_revision_id = int(dat[-1][0])

                        row = [None] * len(loop.tags)
                        row[loop.tags.index('Revision_ID')] = last_revision_id + 1
                        row[loop.tags.index('Creation_date')] = this_friday.strftime('%Y-%m-%d')
                        row[loop.tags.index('Update_record')] = 'Remediation'
                        row[loop.tags.index('Entry_ID')] = self.__reg.entry_id

                        loop.add_data(row)

                        update_audit = True

                else:
                    del sf[loop]

            except KeyError:
                pass

        except IndexError:
            pass

        if len(sf_list) > 1:

            for sf in sf_list[1:]:

                try:

                    loop = sf.get_loop(lp_category)

                    if self.__reg.internal_mode:

                        dat = loop.get_tag(['Revision_ID', 'Update_record'])

                        if any(True for row in dat if row[1] == 'Initial release'):
                            last_revision_id = int(dat[-1][0])

                            row = [None] * len(loop.tags)
                            row[loop.tags.index('Revision_ID')] = last_revision_id + 1
                            row[loop.tags.index('Creation_date')] = this_friday.strftime('%Y-%m-%d')
                            row[loop.tags.index('Update_record')] = 'Remediation'
                            row[loop.tags.index('Entry_ID')] = self.__reg.entry_id

                            loop.add_data(row)

                            update_audit = True

                        sf_list[0].add_loop(loop)

                except KeyError:
                    pass

                del master_entry[sf]

        if self.__reg.internal_mode and not self.__reg.bmrb_only and not update_audit:

            sf_list = master_entry.get_saveframes_by_category(sf_category)

            try:

                sf = sf_list[0]

                try:

                    loop = sf.get_loop(lp_category)

                except KeyError:

                    lp = pynmrstar.Loop.from_scratch(lp_category)

                    items = ['Revision_ID', 'Creation_date', 'Update_record', 'Creation_method', 'Entry_ID']

                    tags = [lp_category + '.' + item for item in items]

                    lp.add_tag(tags)

                    lp.add_data([1, this_friday.strftime('%Y-%m-%d'), 'Preliminary version', None, self.__reg.entry_id])

                    sf.add_loop(lp)

            except IndexError:
                pass

        if self.__reg.internal_mode and not self.__reg.bmrb_only:

            nmr_star_version = get_first_sf_tag(sf_list[0], 'NMR_STAR_version')

            if len(nmr_star_version) == 0:
                set_sf_tag(sf_list[0], 'NMR_star_version', NMR_STAR_VERSION)

            sf_category = 'entry_interview'

            sf_list = master_entry.get_saveframes_by_category(sf_category)

            if len(sf_list) > 0:

                pdb_deposition = get_first_sf_tag(sf_list[0], 'PDB_deposition')
                if pdb_deposition == 'no':
                    set_sf_tag(sf_list[0], 'PDB_deposition', 'yes')

                view_mode = get_first_sf_tag(sf_list[0], 'View_mode')
                if len(view_mode) > 0 and view_mode != 'PDB/BMRB':
                    set_sf_tag(sf_list[0], 'View_mode', 'PDB/BMRB')

        # refresh _Constraint_stat_list saveframe

        sf_framecode = 'constraint_statistics'

        cst_sf = pynmrstar.Saveframe.from_scratch(sf_framecode)
        cst_sf.set_tag_prefix('_Constraint_stat_list')
        cst_sf.add_tag('Sf_category', sf_framecode)
        cst_sf.add_tag('Sf_framecode', sf_framecode)
        cst_sf.add_tag('Entry_ID', self.__reg.entry_id)
        cst_sf.add_tag('ID', 1)

        if self.__reg.remediation_mode:

            if AR_FILE_PATH_LIST_KEY in self.__reg.inputParamDict:

                fileListId = self.__reg.file_path_list_len

                file_names = []

                for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:

                    input_source = self.__reg.report.input_sources[fileListId]
                    input_source_dic = input_source.get()

                    fileListId += 1

                    ar_file_type = input_source_dic['file_type']

                    if not ar_file_type.startswith('nm-res') or ar_file_type == 'nm-res-mr':
                        continue

                    if 'original_file_name' in ar and ar['original_file_name'] not in EMPTY_VALUE:
                        file_name = ar['original_file_name']
                    else:
                        file_name = input_source_dic['file_name']

                    file_names.append(retrieveOriginalFileName(file_name))

                if len(file_names) > 0:
                    cst_sf.add_tag('Data_file_name', ','.join(file_names))

        # statistics

        if self.__reg.mr_sf_dict_holder is not None:

            content_subtype = 'dist_restraint'

            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    if 'NOE_dist_averaging_method' in sf_item:
                        cst_sf.add_tag('NOE_dist_averaging_method', sf_item['NOE_dist_averaging_method'])
                        break

                NOE_tot_num =\
                    NOE_intraresidue_tot_num =\
                    NOE_sequential_tot_num =\
                    NOE_medium_range_tot_num =\
                    NOE_long_range_tot_num =\
                    NOE_unique_tot_num =\
                    NOE_intraresidue_unique_tot_num =\
                    NOE_sequential_unique_tot_num =\
                    NOE_medium_range_unique_tot_num =\
                    NOE_long_range_unique_tot_num =\
                    NOE_unamb_intramol_tot_num =\
                    NOE_unamb_intermol_tot_num =\
                    NOE_ambig_intramol_tot_num =\
                    NOE_ambig_intermol_tot_num =\
                    NOE_interentity_tot_num =\
                    NOE_other_tot_num = 0

                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:

                    sf = sf_item['saveframe']
                    sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                    use_member_logic_code = sf_framecode.startswith('XPLOR') or sf_framecode.startswith('CNS')\
                        or sf_framecode.startswith('CHARMM')
                    if use_member_logic_code:
                        lp = sf_item['loop']
                        if 'Member_logic_code' not in lp.tags:
                            use_member_logic_code = False
                        else:
                            dat = lp.get_tag(['Member_logic_code'])
                            use_member_logic_code = any(True for row in dat if row not in EMPTY_VALUE)

                    if not use_member_logic_code:
                        self.__reg.dpV.updateGenDistConstIdInMrStr(sf_item)

                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if 'NOE' in constraint_type:
                        # NOE_tot_num += sf_item['id']

                        lp = sf_item['loop']

                        item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                        id_col = lp.tags.index('ID')
                        chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                        chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                        seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                        seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                        comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                        comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                        atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                        atom_id_2_col = lp.tags.index(item_names['atom_id_2'])
                        # try:
                        #     member_logic_code_col = lp.tags.index(item_names['member_logic_code'])
                        # except ValueError:
                        #     member_logic_code_col = -1
                        try:
                            combination_id_col = lp.tags.index(item_names['combination_id'])
                        except ValueError:
                            combination_id_col = -1
                        try:
                            upper_limit_col = lp.tags.index(item_names['upper_limit'])
                        except ValueError:
                            upper_limit_col = -1

                        prev_id = -1

                        for row in lp:
                            _id = int(row[id_col])
                            # member_logic_code = row[member_logic_code_col] if member_logic_code_col != -1 else None
                            try:
                                chain_id_1 = int(row[chain_id_1_col])
                                chain_id_2 = int(row[chain_id_2_col])
                                seq_id_1 = int(row[seq_id_1_col])
                                seq_id_2 = int(row[seq_id_2_col])
                            except (ValueError, TypeError):
                                continue
                            comp_id_1 = row[comp_id_1_col]
                            comp_id_2 = row[comp_id_2_col]
                            atom_id_1 = row[atom_id_1_col]
                            atom_id_2 = row[atom_id_2_col]

                            if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE or _id == prev_id:
                                continue

                            prev_id = _id

                            combination_id = row[combination_id_col] if combination_id_col != -1 else None
                            upper_limit =\
                                float(row[upper_limit_col]) if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE\
                                else None

                            offset = abs(seq_id_1 - seq_id_2)
                            ambig = upper_limit is not None and (upper_limit <= DIST_AMBIG_LOW or upper_limit >= DIST_AMBIG_UP)
                            uniq = combination_id in EMPTY_VALUE and not ambig

                            NOE_tot_num += 1

                            if uniq:
                                NOE_unique_tot_num += 1

                            if chain_id_1 == chain_id_2:
                                if uniq:
                                    NOE_unamb_intramol_tot_num += 1
                                else:
                                    NOE_ambig_intramol_tot_num += 1
                                if offset == 0:
                                    NOE_intraresidue_tot_num += 1
                                    if uniq:
                                        NOE_intraresidue_unique_tot_num += 1
                                elif offset == 1:
                                    NOE_sequential_tot_num += 1
                                    if uniq:
                                        NOE_sequential_unique_tot_num += 1
                                elif offset < 5:
                                    NOE_medium_range_tot_num += 1
                                    if uniq:
                                        NOE_medium_range_unique_tot_num += 1
                                else:
                                    NOE_long_range_tot_num += 1
                                    if uniq:
                                        NOE_long_range_unique_tot_num += 1
                            else:
                                NOE_interentity_tot_num += 1
                                if uniq:
                                    NOE_unamb_intermol_tot_num += 1
                                else:
                                    NOE_ambig_intermol_tot_num += 1

                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    sf = sf_item['saveframe']
                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if constraint_type in ('paramagnetic relaxation',
                                           'photo cidnp',
                                           'chemical shift perturbation',
                                           'mutation',
                                           'symmetry'):
                        NOE_other_tot_num += sf_item['id']

                if NOE_tot_num > 0:
                    cst_sf.add_tag('NOE_tot_num', NOE_tot_num)
                    cst_sf.add_tag('NOE_intraresidue_tot_num', NOE_intraresidue_tot_num)
                    cst_sf.add_tag('NOE_sequential_tot_num', NOE_sequential_tot_num)
                    cst_sf.add_tag('NOE_medium_range_tot_num', NOE_medium_range_tot_num)
                    cst_sf.add_tag('NOE_long_range_tot_num', NOE_long_range_tot_num)
                    cst_sf.add_tag('NOE_unique_tot_num', NOE_unique_tot_num)
                    cst_sf.add_tag('NOE_intraresidue_unique_tot_num', NOE_intraresidue_unique_tot_num)
                    cst_sf.add_tag('NOE_sequential_unique_tot_num', NOE_sequential_unique_tot_num)
                    cst_sf.add_tag('NOE_medium_range_unique_tot_num', NOE_medium_range_unique_tot_num)
                    cst_sf.add_tag('NOE_long_range_unique_tot_num', NOE_long_range_unique_tot_num)
                    cst_sf.add_tag('NOE_unamb_intramol_tot_num', NOE_unamb_intramol_tot_num)
                    cst_sf.add_tag('NOE_unamb_intermol_tot_num', NOE_unamb_intermol_tot_num)
                    cst_sf.add_tag('NOE_ambig_intramol_tot_num', NOE_ambig_intramol_tot_num)
                    cst_sf.add_tag('NOE_ambig_intermol_tot_num', NOE_ambig_intermol_tot_num)
                    cst_sf.add_tag('NOE_interentity_tot_num', NOE_interentity_tot_num)
                    cst_sf.add_tag('NOE_other_tot_num', NOE_other_tot_num)

                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    if 'ROE_dist_averaging_method' in sf_item:
                        cst_sf.add_tag('ROE_dist_averaging_method', sf_item['ROE_dist_averaging_method'])
                        break

                ROE_tot_num =\
                    ROE_intraresidue_tot_num =\
                    ROE_sequential_tot_num =\
                    ROE_medium_range_tot_num =\
                    ROE_long_range_tot_num =\
                    ROE_unambig_intramol_tot_num =\
                    ROE_unambig_intermol_tot_num =\
                    ROE_ambig_intramol_tot_num =\
                    ROE_ambig_intermol_tot_num =\
                    ROE_other_tot_num = 0

                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    sf = sf_item['saveframe']
                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if 'ROE' in constraint_type:
                        # ROE_tot_num += sf_item['id']

                        lp = sf_item['loop']

                        item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                        id_col = lp.tags.index('ID')
                        chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                        chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                        seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                        seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                        comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                        comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                        atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                        atom_id_2_col = lp.tags.index(item_names['atom_id_2'])
                        # try:
                        #     member_logic_code_col = lp.tags.index(item_names['member_logic_code'])
                        # except ValueError:
                        #     member_logic_code_col = -1
                        try:
                            combination_id_col = lp.tags.index(item_names['combination_id'])
                        except ValueError:
                            combination_id_col = -1
                        try:
                            upper_limit_col = lp.tags.index(item_names['upper_limit'])
                        except ValueError:
                            upper_limit_col = -1

                        prev_id = -1

                        for row in lp:
                            _id = int(row[id_col])
                            # member_logic_code = row[member_logic_code_col] if member_logic_code_col != -1 else None
                            try:
                                chain_id_1 = int(row[chain_id_1_col])
                                chain_id_2 = int(row[chain_id_2_col])
                                seq_id_1 = int(row[seq_id_1_col])
                                seq_id_2 = int(row[seq_id_2_col])
                            except (ValueError, TypeError):
                                continue
                            comp_id_1 = row[comp_id_1_col]
                            comp_id_2 = row[comp_id_2_col]
                            atom_id_1 = row[atom_id_1_col]
                            atom_id_2 = row[atom_id_2_col]

                            if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE or _id == prev_id:
                                continue

                            prev_id = _id

                            combination_id = row[combination_id_col] if combination_id_col != -1 else None
                            upper_limit =\
                                float(row[upper_limit_col]) if upper_limit_col != -1 and row[upper_limit_col] not in EMPTY_VALUE\
                                else None

                            offset = abs(seq_id_1 - seq_id_2)
                            ambig = upper_limit is not None and (upper_limit <= DIST_AMBIG_LOW or upper_limit >= DIST_AMBIG_UP)
                            uniq = combination_id in EMPTY_VALUE and not ambig

                            ROE_tot_num += 1

                            if chain_id_1 == chain_id_2:
                                if uniq:
                                    ROE_unambig_intramol_tot_num += 1
                                else:
                                    ROE_ambig_intramol_tot_num += 1
                                if offset == 0:
                                    ROE_intraresidue_tot_num += 1
                                elif offset == 1:
                                    ROE_sequential_tot_num += 1
                                elif offset < 5:
                                    ROE_medium_range_tot_num += 1
                                else:
                                    ROE_long_range_tot_num += 1
                            else:
                                ROE_other_tot_num += 1
                                if uniq:
                                    ROE_unambig_intermol_tot_num += 1
                                else:
                                    ROE_ambig_intermol_tot_num += 1

                if ROE_tot_num > 0:
                    cst_sf.add_tag('ROE_tot_num', ROE_tot_num)
                    cst_sf.add_tag('ROE_intraresidue_tot_num', ROE_intraresidue_tot_num)
                    cst_sf.add_tag('ROE_sequential_tot_num', ROE_sequential_tot_num)
                    cst_sf.add_tag('ROE_medium_range_tot_num', ROE_medium_range_tot_num)
                    cst_sf.add_tag('ROE_long_range_tot_num', ROE_long_range_tot_num)
                    cst_sf.add_tag('ROE_unambig_intramol_tot_num', ROE_unambig_intramol_tot_num)
                    cst_sf.add_tag('ROE_unambig_intermol_tot_num', ROE_unambig_intermol_tot_num)
                    cst_sf.add_tag('ROE_ambig_intramol_tot_num', ROE_ambig_intramol_tot_num)
                    cst_sf.add_tag('ROE_ambig_intermol_tot_num', ROE_ambig_intermol_tot_num)
                    cst_sf.add_tag('ROE_other_tot_num', ROE_other_tot_num)

            content_subtype = 'dihed_restraint'

            auth_to_entity_type = self.__reg.caC['auth_to_entity_type']

            Dihedral_angle_tot_num = 0
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    Dihedral_angle_tot_num += sf_item['id']

            if Dihedral_angle_tot_num > 0:
                cst_sf.add_tag('Dihedral_angle_tot_num', Dihedral_angle_tot_num)

            Protein_dihedral_angle_tot_num =\
                Protein_phi_angle_tot_num =\
                Protein_psi_angle_tot_num =\
                Protein_chi_one_angle_tot_num =\
                Protein_other_angle_tot_num = 0

            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    self.__reg.dpV.updateTorsionAngleConstIdInMrStr(sf_item)

                    lp = sf_item['loop']

                    lp.sort_rows('ID')
                    lp.renumber_rows('Index_ID')

                    id_col = lp.tags.index('ID')
                    auth_asym_id_col = lp.tags.index('Auth_asym_ID_2')
                    auth_seq_id_col = lp.tags.index('Auth_seq_ID_2')
                    auth_comp_id_col = lp.tags.index('Auth_comp_ID_2')
                    angle_name_col = lp.tags.index('Torsion_angle_name')

                    _protein_angles = _other_angles = _protein_bb_angles = _protein_oth_angles = 0

                    prev_id = -1
                    for row in lp:
                        _id = int(row[id_col])
                        if _id == prev_id:
                            continue
                        prev_id = _id
                        auth_asym_id = row[auth_asym_id_col]
                        try:
                            auth_seq_id = int(row[auth_seq_id_col]) if row[auth_seq_id_col] not in EMPTY_VALUE else None
                        except (ValueError, TypeError):
                            continue
                        auth_comp_id = row[auth_comp_id_col]
                        angle_name = row[angle_name_col]
                        if angle_name is None:
                            continue

                        seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                        if seq_key in auth_to_entity_type:
                            entity_type = auth_to_entity_type[seq_key]

                            if 'peptide' in entity_type:
                                Protein_dihedral_angle_tot_num += 1
                                _protein_angles += 1
                                if angle_name == 'PHI':
                                    Protein_phi_angle_tot_num += 1
                                    _protein_bb_angles += 1
                                elif angle_name == 'PSI':
                                    Protein_psi_angle_tot_num += 1
                                    _protein_bb_angles += 1
                                elif angle_name == 'CHI1':
                                    Protein_chi_one_angle_tot_num += 1
                                    _protein_oth_angles += 1
                                else:
                                    Protein_other_angle_tot_num += 1
                                    _protein_oth_angles += 1
                            else:
                                _other_angles += 1

                    if _protein_angles > _other_angles:
                        sf_item['constraint_type'] = 'protein dihedral angle'

                        sf = sf_item['saveframe']

                        if 'jcoup_restraint' not in self.__reg.mr_sf_dict_holder:
                            set_sf_tag(sf, 'Constraint_type', 'backbone chemical shifts')

                        else:

                            _protein_jcoups = _protein_bb_jcoups = _protein_oth_jcoups = 0

                            for _sf_item in self.__reg.mr_sf_dict_holder['jcoup_restraint']:

                                _lp = _sf_item['loop']

                                auth_asym_id_col = _lp.tags.index('Auth_asym_ID_2')
                                auth_seq_id_col = _lp.tags.index('Auth_seq_ID_2')
                                auth_comp_id_col = _lp.tags.index('Auth_comp_ID_2')
                                atom_id_1_col = _lp.tags.index('Atom_ID_1')
                                atom_id_4_col = _lp.tags.index('Atom_ID_4')

                                for _row in _lp:
                                    auth_asym_id = _row[auth_asym_id_col]
                                    try:
                                        auth_seq_id = int(_row[auth_seq_id_col])
                                    except (ValueError, TypeError):
                                        continue
                                    auth_comp_id = _row[auth_comp_id_col]
                                    atom_id_1 = _row[atom_id_1_col]
                                    atom_id_4 = _row[atom_id_4_col]

                                    seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                                    if seq_key in auth_to_entity_type:
                                        entity_type = auth_to_entity_type[seq_key]

                                        if 'peptide' in entity_type:
                                            _protein_jcoups += 1
                                            if 'H' in (atom_id_1, atom_id_4):
                                                _protein_bb_jcoups += 1
                                            else:
                                                _protein_oth_jcoups += 1

                            if (_protein_bb_angles > 0 and _protein_oth_angles == 0
                                and _protein_bb_jcoups > 0 and _protein_oth_jcoups == 0)\
                               or (_protein_bb_angles > 0 and _protein_oth_angles > 0
                                   and _protein_bb_jcoups > 0 and _protein_oth_jcoups > 0)\
                               or (_protein_bb_angles == 0 and _protein_oth_angles > 0
                                   and _protein_bb_jcoups == 0 and _protein_oth_jcoups > 0):
                                set_sf_tag(sf, 'Constraint_type', 'J-couplings')

                            elif _protein_jcoups == 0:
                                set_sf_tag(sf, 'Constraint_type', 'backbone chemical shifts')

                            else:
                                set_sf_tag(sf, 'Constraint_type', 'unknown')

            if Protein_dihedral_angle_tot_num > 0:
                cst_sf.add_tag('Protein_dihedral_angle_tot_num', Protein_dihedral_angle_tot_num)
                cst_sf.add_tag('Protein_phi_angle_tot_num', Protein_phi_angle_tot_num)
                cst_sf.add_tag('Protein_psi_angle_tot_num', Protein_psi_angle_tot_num)
                cst_sf.add_tag('Protein_chi_one_angle_tot_num', Protein_chi_one_angle_tot_num)
                cst_sf.add_tag('Protein_other_angle_tot_num', Protein_other_angle_tot_num)

            NA_dihedral_angle_tot_num =\
                NA_alpha_angle_tot_num =\
                NA_beta_angle_tot_num =\
                NA_gamma_angle_tot_num =\
                NA_delta_angle_tot_num =\
                NA_epsilon_angle_tot_num =\
                NA_chi_angle_tot_num =\
                NA_other_angle_tot_num =\
                NA_amb_dihedral_angle_tot_num = 0

            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:

                    lp = sf_item['loop']

                    id_col = lp.tags.index('ID')
                    auth_asym_id_col = lp.tags.index('Auth_asym_ID_2')
                    auth_seq_id_col = lp.tags.index('Auth_seq_ID_2')
                    auth_comp_id_col = lp.tags.index('Auth_comp_ID_2')
                    angle_name_col = lp.tags.index('Torsion_angle_name')

                    _na_angles = _other_angles = 0

                    prev_id = -1
                    for row in lp:
                        _id = int(row[id_col])
                        if _id == prev_id:
                            continue
                        prev_id = _id
                        auth_asym_id = row[auth_asym_id_col]
                        try:
                            auth_seq_id = int(row[auth_seq_id_col]) if row[auth_seq_id_col] not in EMPTY_VALUE else None
                        except (ValueError, TypeError):
                            continue
                        auth_comp_id = row[auth_comp_id_col]
                        angle_name = row[angle_name_col]
                        if angle_name is None:
                            continue

                        seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                        if seq_key in auth_to_entity_type:
                            entity_type = auth_to_entity_type[seq_key]

                            if 'nucleotide' in entity_type:
                                NA_dihedral_angle_tot_num += 1
                                _na_angles += 1
                                if angle_name == 'ALPHA':
                                    NA_alpha_angle_tot_num += 1
                                elif angle_name == 'BETA':
                                    NA_beta_angle_tot_num += 1
                                elif angle_name == 'GAMMA':
                                    NA_gamma_angle_tot_num += 1
                                elif angle_name == 'DELTA':
                                    NA_delta_angle_tot_num += 1
                                elif angle_name == 'EPSILON':
                                    NA_epsilon_angle_tot_num += 1
                                elif angle_name == 'CHI':
                                    NA_chi_angle_tot_num += 1
                                elif angle_name == 'PPA':
                                    NA_amb_dihedral_angle_tot_num += 1
                                else:
                                    NA_other_angle_tot_num += 1
                            else:
                                _other_angles += 1

                    if _na_angles > _other_angles:
                        sf_item['constraint_type'] = 'nucleic acid dihedral angle'

                        sf = sf_item['saveframe']

                        if 'jcoup_restraint' not in self.__reg.mr_sf_dict_holder:
                            set_sf_tag(sf, 'Constraint_type', 'unknown')

                        else:

                            _na_jcoups = 0

                            for _sf_item in self.__reg.mr_sf_dict_holder['jcoup_restraint']:

                                _lp = _sf_item['loop']

                                auth_asym_id_col = _lp.tags.index('Auth_asym_ID_2')
                                auth_seq_id_col = _lp.tags.index('Auth_seq_ID_2')
                                auth_comp_id_col = _lp.tags.index('Auth_comp_ID_2')

                                for _row in _lp:
                                    auth_asym_id = _row[auth_asym_id_col]
                                    try:
                                        auth_seq_id = int(_row[auth_seq_id_col])
                                    except (ValueError, TypeError):
                                        continue
                                    auth_comp_id = _row[auth_comp_id_col]

                                    seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                                    if seq_key in auth_to_entity_type:
                                        entity_type = auth_to_entity_type[seq_key]

                                        if 'nucleotide' in entity_type:
                                            _na_jcoups += 1

                            set_sf_tag(sf, 'Constraint_type', 'J-couplings' if _na_jcoups > 0 else 'unknown')

            if NA_dihedral_angle_tot_num > 0:
                cst_sf.add_tag('NA_dihedral_angle_tot_num', NA_dihedral_angle_tot_num)
                cst_sf.add_tag('NA_alpha_angle_tot_num', NA_alpha_angle_tot_num)
                cst_sf.add_tag('NA_beta_angle_tot_num', NA_beta_angle_tot_num)
                cst_sf.add_tag('NA_gamma_angle_tot_num', NA_gamma_angle_tot_num)
                cst_sf.add_tag('NA_delta_angle_tot_num', NA_delta_angle_tot_num)
                cst_sf.add_tag('NA_epsilon_angle_tot_num', NA_epsilon_angle_tot_num)
                cst_sf.add_tag('NA_chi_angle_tot_num', NA_chi_angle_tot_num)
                cst_sf.add_tag('NA_other_angle_tot_num', NA_other_angle_tot_num)
                cst_sf.add_tag('NA_amb_dihedral_angle_tot_num', NA_amb_dihedral_angle_tot_num)

            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:

                    lp = sf_item['loop']

                    id_col = lp.tags.index('ID')
                    auth_asym_id_col = lp.tags.index('Auth_asym_ID_2')
                    auth_seq_id_col = lp.tags.index('Auth_seq_ID_2')
                    auth_comp_id_col = lp.tags.index('Auth_comp_ID_2')
                    angle_name_col = lp.tags.index('Torsion_angle_name')

                    _br_angles = _other_angles = 0

                    prev_id = -1
                    for row in lp:
                        _id = int(row[id_col])
                        if _id == prev_id:
                            continue
                        prev_id = _id
                        auth_asym_id = row[auth_asym_id_col]
                        try:
                            auth_seq_id = int(row[auth_seq_id_col]) if row[auth_seq_id_col] not in EMPTY_VALUE else None
                        except (ValueError, TypeError):
                            continue
                        auth_comp_id = row[auth_comp_id_col]
                        angle_name = row[angle_name_col]
                        if angle_name is None:
                            continue

                        seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                        if seq_key in auth_to_entity_type:
                            entity_type = auth_to_entity_type[seq_key]

                            if 'saccharide' in entity_type:
                                _br_angles += 1
                            else:
                                _other_angles += 1

                    if _br_angles > _other_angles:
                        sf_item['constraint_type'] = 'carbohydrate dihedral angle'  # DAOTHER-9471

                        sf = sf_item['saveframe']

                        if 'jcoup_restraint' not in self.__reg.mr_sf_dict_holder:
                            set_sf_tag(sf, 'Constraint_type', 'unknown')

                        else:

                            _br_jcoups = 0

                            for _sf_item in self.__reg.mr_sf_dict_holder['jcoup_restraint']:

                                _lp = _sf_item['loop']

                                auth_asym_id_col = _lp.tags.index('Auth_asym_ID_2')
                                auth_seq_id_col = _lp.tags.index('Auth_seq_ID_2')
                                auth_comp_id_col = _lp.tags.index('Auth_comp_ID_2')

                                for _row in _lp:
                                    auth_asym_id = _row[auth_asym_id_col]
                                    try:
                                        auth_seq_id = int(_row[auth_seq_id_col])
                                    except (ValueError, TypeError):
                                        continue
                                    auth_comp_id = _row[auth_comp_id_col]

                                    seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                                    if seq_key in auth_to_entity_type:
                                        entity_type = auth_to_entity_type[seq_key]

                                        if 'saccharide' in entity_type:
                                            _br_jcoups += 1

                            set_sf_tag(sf, 'Constraint_type', 'J-couplings' if _br_jcoups > 0 else 'unknown')

            content_subtype = 'rdc_restraint'

            RDC_tot_num =\
                RDC_HH_tot_num =\
                RDC_HNC_tot_num =\
                RDC_NH_tot_num =\
                RDC_CC_tot_num =\
                RDC_CN_i_1_tot_num =\
                RDC_CAHA_tot_num =\
                RDC_HNHA_tot_num =\
                RDC_HNHA_i_1_tot_num =\
                RDC_CAC_tot_num =\
                RDC_CAN_tot_num =\
                RDC_other_tot_num =\
                RDC_intraresidue_tot_num =\
                RDC_sequential_tot_num =\
                RDC_medium_range_tot_num =\
                RDC_long_range_tot_num =\
                RDC_unambig_intramol_tot_num =\
                RDC_unambig_intermol_tot_num =\
                RDC_ambig_intramol_tot_num =\
                RDC_ambig_intermol_tot_num =\
                RDC_intermol_tot_num = 0

            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    lp = sf_item['loop']

                    # RDC_tot_num += sf_item['id']

                    item_names = ITEM_NAMES_IN_RDC_LOOP[file_type]
                    id_col = lp.tags.index('ID')
                    chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                    chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                    seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                    seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                    comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                    atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                    atom_id_2_col = lp.tags.index(item_names['atom_id_2'])
                    try:
                        combination_id_col = lp.tags.index(item_names['combination_id'])
                    except ValueError:
                        combination_id_col = -1

                    prev_id = -1
                    for row in lp:
                        _id = int(row[id_col])
                        if _id == prev_id:
                            continue
                        prev_id = _id
                        try:
                            chain_id_1 = int(row[chain_id_1_col])
                            chain_id_2 = int(row[chain_id_2_col])
                            seq_id_1 = int(row[seq_id_1_col])
                            seq_id_2 = int(row[seq_id_2_col])
                        except (ValueError, TypeError):
                            continue
                        comp_id_1 = row[comp_id_1_col]
                        atom_id_1 = row[atom_id_1_col]
                        atom_id_2 = row[atom_id_2_col]

                        if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE:
                            continue

                        combination_id = row[combination_id_col] if combination_id_col != -1 else None

                        vector = {atom_id_1, atom_id_2}
                        offset = abs(seq_id_1 - seq_id_2)

                        RDC_tot_num += 1

                        if chain_id_1 == chain_id_2:
                            if vector == {'H', 'C'} and offset == 1:
                                RDC_HNC_tot_num += 1
                            elif vector == {'H', 'N'} and offset == 0:
                                RDC_NH_tot_num += 1
                            elif vector == {'C', 'N'} and offset == 1:
                                RDC_CN_i_1_tot_num += 1
                            elif vector == {'CA', 'HA'} and offset == 0:
                                RDC_CAHA_tot_num += 1
                            elif vector == {'H', 'HA'} and offset == 0:
                                RDC_HNHA_tot_num += 1
                            elif vector == {'H', 'HA'} and offset == 1:
                                RDC_HNHA_i_1_tot_num += 1
                            elif vector == {'CA', 'C'} and offset == 0:
                                RDC_CAC_tot_num += 1
                            elif vector == {'CA', 'N'} and offset == 0:
                                RDC_CAN_tot_num += 1
                            elif atom_id_1[0] == atom_id_2[0]:
                                if atom_id_1[0] in PROTON_BEGIN_CODE:
                                    RDC_HH_tot_num += 1
                                elif atom_id_1[0] == 'C':
                                    RDC_CC_tot_num += 1
                                else:
                                    RDC_other_tot_num += 1
                            elif offset == 0 and comp_id_1 == 'TRP' and vector == {'HE1', 'NE1'}:
                                RDC_NH_tot_num += 1
                            elif offset == 0 and comp_id_1 == 'ARG' and vector == {'HE', 'NE'}:
                                RDC_NH_tot_num += 1
                            else:
                                RDC_other_tot_num += 1

                        if chain_id_1 == chain_id_2:
                            if offset == 0:
                                RDC_intraresidue_tot_num += 1
                            elif offset == 1:
                                RDC_sequential_tot_num += 1
                            elif offset < 5:
                                RDC_medium_range_tot_num += 1
                            else:
                                RDC_long_range_tot_num += 1
                            if combination_id in EMPTY_VALUE:
                                RDC_unambig_intramol_tot_num += 1
                            else:
                                RDC_ambig_intramol_tot_num += 1

                        else:
                            RDC_intermol_tot_num += 1
                            if combination_id in EMPTY_VALUE:
                                RDC_unambig_intermol_tot_num += 1
                            else:
                                RDC_ambig_intermol_tot_num += 1

            if RDC_tot_num > 0:
                cst_sf.add_tag('RDC_tot_num', RDC_tot_num)
                cst_sf.add_tag('RDC_HH_tot_num', RDC_HH_tot_num)
                cst_sf.add_tag('RDC_HNC_tot_num', RDC_HNC_tot_num)
                cst_sf.add_tag('RDC_NH_tot_num', RDC_NH_tot_num)
                cst_sf.add_tag('RDC_CC_tot_num', RDC_CC_tot_num)
                cst_sf.add_tag('RDC_CN_i_1_tot_num', RDC_CN_i_1_tot_num)
                cst_sf.add_tag('RDC_CAHA_tot_num', RDC_CAHA_tot_num)
                cst_sf.add_tag('RDC_HNHA_tot_num', RDC_HNHA_tot_num)
                cst_sf.add_tag('RDC_HNHA_i_1_tot_num', RDC_HNHA_i_1_tot_num)
                cst_sf.add_tag('RDC_CAC_tot_num', RDC_CAC_tot_num)
                cst_sf.add_tag('RDC_CAN_tot_num', RDC_CAN_tot_num)
                cst_sf.add_tag('RDC_other_tot_num', RDC_other_tot_num)
                cst_sf.add_tag('RDC_intraresidue_tot_num', RDC_intraresidue_tot_num)
                cst_sf.add_tag('RDC_sequential_tot_num', RDC_sequential_tot_num)
                cst_sf.add_tag('RDC_medium_range_tot_num', RDC_medium_range_tot_num)
                cst_sf.add_tag('RDC_long_range_tot_num', RDC_long_range_tot_num)
                cst_sf.add_tag('RDC_unambig_intramol_tot_num', RDC_unambig_intramol_tot_num)
                cst_sf.add_tag('RDC_unambig_intermol_tot_num', RDC_unambig_intermol_tot_num)
                cst_sf.add_tag('RDC_ambig_intramol_tot_num', RDC_ambig_intramol_tot_num)
                cst_sf.add_tag('RDC_ambig_intermol_tot_num', RDC_ambig_intermol_tot_num)
                cst_sf.add_tag('RDC_intermol_tot_num', RDC_intermol_tot_num)

            content_subtype = 'dist_restraint'

            hbond_pairs = set()
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    sf = sf_item['saveframe']
                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if constraint_type != 'hydrogen bond':
                        continue

                    lp = sf_item['loop']

                    item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                    chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                    chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                    seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                    seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                    comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                    comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                    atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                    atom_id_2_col = lp.tags.index(item_names['atom_id_2'])

                    for row in lp:
                        try:
                            chain_id_1 = int(row[chain_id_1_col])
                            chain_id_2 = int(row[chain_id_2_col])
                            seq_id_1 = int(row[seq_id_1_col])
                            seq_id_2 = int(row[seq_id_2_col])
                        except (ValueError, TypeError):
                            continue
                        comp_id_1 = row[comp_id_1_col]
                        comp_id_2 = row[comp_id_2_col]
                        atom_id_1 = row[atom_id_1_col]
                        atom_id_2 = row[atom_id_2_col]

                        if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE:
                            continue

                        if atom_id_1[0] in PROTON_BEGIN_CODE:
                            if self.__reg.ccU.updateChemCompDict(comp_id_1):
                                bonded_atom_id_1 = self.__reg.ccU.getBondedAtoms(comp_id_1, atom_id_1)
                                if len(bonded_atom_id_1) == 0:
                                    continue
                                if any(True for _row in lp
                                       if (_row[chain_id_1_col] is not None and int(_row[chain_id_1_col]) == chain_id_1
                                           and _row[seq_id_1_col] is not None and int(_row[seq_id_1_col]) == seq_id_1
                                           and _row[atom_id_1_col] == bonded_atom_id_1[0])
                                       or (_row[chain_id_2_col] is not None and int(_row[chain_id_2_col]) == chain_id_1
                                           and _row[seq_id_2_col] is not None and int(_row[seq_id_2_col]) == seq_id_1
                                           and _row[atom_id_2_col] == bonded_atom_id_1[0])):
                                    continue
                        if atom_id_2[0] in PROTON_BEGIN_CODE:
                            if self.__reg.ccU.updateChemCompDict(comp_id_2):
                                bonded_atom_id_2 = self.__reg.ccU.getBondedAtoms(comp_id_2, atom_id_2)
                                if len(bonded_atom_id_2) == 0:
                                    continue
                                if any(True for _row in lp
                                       if (_row[chain_id_1_col] is not None and int(_row[chain_id_1_col]) == chain_id_2
                                           and _row[seq_id_1_col] is not None and int(_row[seq_id_1_col]) == seq_id_2
                                           and _row[atom_id_1_col] == bonded_atom_id_2[0])
                                       or (_row[chain_id_2_col] is not None and int(_row[chain_id_2_col]) == chain_id_2
                                           and _row[seq_id_2_col] is not None and int(_row[seq_id_2_col]) == seq_id_2
                                           and _row[atom_id_2_col] == bonded_atom_id_2[0])):
                                    continue
                        p1 = (chain_id_1, seq_id_1, atom_id_1)
                        p2 = (chain_id_2, seq_id_2, atom_id_2)
                        hbond_pair = sorted([p1, p2], key=itemgetter(0, 1, 2))
                        hbond_pairs.add(str(hbond_pair))

            H_bonds_constrained_tot_num = len(hbond_pairs)
            if H_bonds_constrained_tot_num > 0:
                cst_sf.add_tag('H_bonds_constrained_tot_num', H_bonds_constrained_tot_num)

            ssbond_pairs = set()
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    sf = sf_item['saveframe']
                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if constraint_type != 'disulfide bond':
                        continue

                    lp = sf_item['loop']

                    item_names = ITEM_NAMES_IN_DIST_LOOP[file_type]
                    chain_id_1_col = lp.tags.index(item_names['chain_id_1'])
                    chain_id_2_col = lp.tags.index(item_names['chain_id_2'])
                    seq_id_1_col = lp.tags.index(item_names['seq_id_1'])
                    seq_id_2_col = lp.tags.index(item_names['seq_id_2'])
                    comp_id_1_col = lp.tags.index(item_names['comp_id_1'])
                    comp_id_2_col = lp.tags.index(item_names['comp_id_2'])
                    atom_id_1_col = lp.tags.index(item_names['atom_id_1'])
                    atom_id_2_col = lp.tags.index(item_names['atom_id_2'])

                    for row in lp:
                        try:
                            chain_id_1 = int(row[chain_id_1_col])
                            chain_id_2 = int(row[chain_id_2_col])
                            seq_id_1 = int(row[seq_id_1_col])
                            seq_id_2 = int(row[seq_id_2_col])
                        except (ValueError, TypeError):
                            continue
                        comp_id_1 = row[comp_id_1_col]
                        comp_id_2 = row[comp_id_2_col]
                        atom_id_1 = row[atom_id_1_col]
                        atom_id_2 = row[atom_id_2_col]

                        if atom_id_1 in EMPTY_VALUE or atom_id_2 in EMPTY_VALUE:
                            continue

                        if atom_id_1[0] in PROTON_BEGIN_CODE:
                            if self.__reg.ccU.updateChemCompDict(comp_id_1):
                                bonded_atom_id_1 = self.__reg.ccU.getBondedAtoms(comp_id_1, atom_id_1)
                                if len(bonded_atom_id_1) == 0:
                                    continue
                                if any(True for _row in lp
                                       if (_row[chain_id_1_col] is not None and int(_row[chain_id_1_col]) == chain_id_1
                                           and _row[seq_id_1_col] is not None and int(_row[seq_id_1_col]) == seq_id_1
                                           and _row[atom_id_1_col] == bonded_atom_id_1[0])
                                       or (_row[chain_id_2_col] is not None and int(_row[chain_id_2_col]) == chain_id_1
                                           and _row[seq_id_2_col] is not None and int(_row[seq_id_2_col]) == seq_id_1
                                           and _row[atom_id_2_col] == bonded_atom_id_1[0])):
                                    continue
                        if atom_id_2[0] in PROTON_BEGIN_CODE:
                            if self.__reg.ccU.updateChemCompDict(comp_id_2):
                                bonded_atom_id_2 = self.__reg.ccU.getBondedAtoms(comp_id_2, atom_id_2)
                                if len(bonded_atom_id_2) == 0:
                                    continue
                                if any(True for _row in lp
                                       if (_row[chain_id_1_col] is not None and int(_row[chain_id_1_col]) == chain_id_2
                                           and _row[seq_id_1_col] is not None and int(_row[seq_id_1_col]) == seq_id_2
                                           and _row[atom_id_1_col] == bonded_atom_id_2[0])
                                       or (_row[chain_id_2_col] is not None and int(_row[chain_id_2_col]) == chain_id_2
                                           and _row[seq_id_2_col] is not None and int(_row[seq_id_2_col]) == seq_id_2
                                           and _row[atom_id_2_col] == bonded_atom_id_2[0])):
                                    continue
                        p1 = (chain_id_1, seq_id_1, atom_id_1)
                        p2 = (chain_id_2, seq_id_2, atom_id_2)
                        ssbond_pair = sorted([p1, p2], key=itemgetter(0, 1, 2))
                        ssbond_pairs.add(str(ssbond_pair))

            SS_bonds_constrained_tot_num = len(ssbond_pairs)
            if SS_bonds_constrained_tot_num > 0:
                cst_sf.add_tag('SS_bonds_constrained_tot_num', SS_bonds_constrained_tot_num)

            content_subtype = 'jcoup_restraint'

            Derived_coupling_const_tot_num = 0
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    Derived_coupling_const_tot_num += sf_item['id']

            if Derived_coupling_const_tot_num > 0:
                cst_sf.add_tag('Derived_coupling_const_tot_num', Derived_coupling_const_tot_num)

            content_subtype = 'hvycs_restraint'

            Derived_CACB_chem_shift_tot_num = 0
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    Derived_CACB_chem_shift_tot_num += sf_item['id']

            if Derived_CACB_chem_shift_tot_num > 0:
                cst_sf.add_tag('Derived_CACB_chem_shift_tot_num', Derived_CACB_chem_shift_tot_num)

            content_subtype = 'procs_restraint'

            Derived_1H_chem_shift_tot_num = 0
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    Derived_1H_chem_shift_tot_num += sf_item['id']

            if Derived_1H_chem_shift_tot_num > 0:
                cst_sf.add_tag('Derived_1H_chem_shift_tot_num', Derived_1H_chem_shift_tot_num)

            content_subtype = 'dist_restraint'

            Derived_photo_cidnps_tot_num = 0
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    sf = sf_item['saveframe']
                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if constraint_type != 'photo cidnp':
                        continue
                    Derived_photo_cidnps_tot_num += sf_item['id']

            if Derived_photo_cidnps_tot_num > 0:
                cst_sf.add_tag('Derived_photo_cidnps_tot_num', Derived_photo_cidnps_tot_num)

            Derived_paramag_relax_tot_num = 0
            if content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    sf = sf_item['saveframe']
                    potential_type = get_first_sf_tag(sf, 'Potential_type')
                    if 'lower' in potential_type:
                        continue
                    constraint_type = get_first_sf_tag(sf, 'Constraint_type')
                    if constraint_type != 'paramagnetic relaxation':
                        continue
                    Derived_paramag_relax_tot_num += sf_item['id']

            if Derived_paramag_relax_tot_num > 0:
                cst_sf.add_tag('Derived_paramag_relax_tot_num', Derived_paramag_relax_tot_num)

            content_subtype = 'other_restraint'

            if content_subtype in self.__reg.mr_sf_dict_holder:
                Protein_other_tot_num = NA_other_tot_num = 0
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    lp = sf_item['loop']
                    lp_tags = lp['tags']
                    lp_data = lp['data']

                    auth_asym_id_col = lp_tags.index('auth_asym_id') if 'auth_asym_id' in lp_tags\
                        else lp_tags.index('auth_asym_id_1') if 'auth_asym_id_1' in lp_tags\
                        else lp_tags.index('plane_1_auth_asym_id_1')
                    auth_seq_id_col = lp_tags.index('auth_seq_id') if 'auth_seq_id' in lp_tags\
                        else lp_tags.index('auth_seq_id_1') if 'auth_seq_id_1' in lp_tags\
                        else lp_tags.index('plane_1_auth_seq_id_1')
                    auth_comp_id_col = lp_tags.index('auth_comp_id') if 'auth_comp_id' in lp_tags\
                        else lp_tags.index('auth_comp_id_1') if 'auth_comp_id_1' in lp_tags\
                        else lp_tags.index('plane_1_auth_comp_id_1')

                    for row in lp_data:
                        auth_asym_id = row[auth_asym_id_col]
                        try:
                            auth_seq_id = int(row[auth_seq_id_col])
                        except (ValueError, TypeError):
                            continue
                        auth_comp_id = row[auth_comp_id_col]

                        seq_key = (auth_asym_id, auth_seq_id, auth_comp_id)

                        if seq_key in auth_to_entity_type:
                            entity_type = auth_to_entity_type[seq_key]

                            if 'peptide' in entity_type:
                                Protein_other_tot_num += 1
                            elif 'nucleotide' in entity_type:
                                NA_other_tot_num += 1

                if Protein_other_tot_num > 0:
                    cst_sf.add_tag('Protein_other_tot_num', Protein_other_tot_num)
                if NA_other_tot_num > 0:
                    cst_sf.add_tag('NA_other_tot_num', NA_other_tot_num)

        lp_category = '_Constraint_file'
        cf_loop = pynmrstar.Loop.from_scratch(lp_category)

        cf_key_items = [{'name': 'ID', 'type': 'int'},
                        {'name': 'Constraint_filename', 'type': 'str'},
                        {'name': 'Software_ID', 'type': 'int'},
                        {'name': 'Software_label', 'type': 'str'},
                        {'name': 'Software_name', 'type': 'str'},
                        {'name': 'Block_ID', 'type': 'int'},
                        {'name': 'Constraint_type', 'type': 'enum',
                         'enum': ('distance', 'dipolar coupling', 'protein dihedral angle', 'nucleic acid dihedral angle',
                                  'coupling constant', 'chemical shift', 'other angle', 'chemical shift anisotropy',
                                  'hydrogen exchange', 'line broadening', 'pseudocontact shift', 'intervector projection angle',
                                  'protein peptide planarity', 'protein other kinds of constraints',
                                  'nucleic acid base planarity', 'nucleic acid other kinds of constraints',
                                  'carbohydrate dihedral angle')},
                        {'name': 'Constraint_subtype', 'type': 'enum',
                         'enum': ('Not applicable', 'NOE', 'NOE buildup', 'NOE not seen', 'general distance',
                                  'alignment tensor', 'chirality', 'prochirality', 'disulfide bond', 'hydrogen bond',
                                  'symmetry', 'ROE', 'peptide', 'ring', 'PRE')},
                        {'name': 'Constraint_subsubtype', 'type': 'enum',
                         'enum': ('ambi', 'simple')}
                        ]
        cf_data_items = [{'name': 'Constraint_number', 'type': 'int'},
                         {'name': 'Constraint_stat_list_ID', 'type': 'int', 'mandatory': True, 'default': '1', 'default-from': 'parent'},
                         {'name': 'Entry_ID', 'type': 'str', 'mandatory': False}
                         ]

        tags = [lp_category + '.' + _item['name'] for _item in cf_key_items]
        tags.extend([lp_category + '.' + _item['name'] for _item in cf_data_items])

        cf_loop.add_tag(tags)

        # inspect _Software saveframes to extend Software_ID in _Constraint_file loop

        defined_software = []
        software_dict = {}
        software_id = 0

        if 'software' in self.__reg.sf_category_list:
            for sf in master_entry.get_saveframes_by_category('software'):
                _id = get_first_sf_tag(sf, 'ID')
                _name = get_first_sf_tag(sf, 'Name')
                _code = get_first_sf_tag(sf, 'Sf_framecode')
                defined_software.append(_name)
                if _id not in EMPTY_VALUE and _name not in EMPTY_VALUE \
                   and (isinstance(_id, int) or _id.isdigit())\
                   and _name not in software_dict:
                    _id_ = int(_id) if isinstance(_id, str) else _id
                    software_dict[_name] = (_id_, _code)
                    software_id = max(software_id, _id_)

        file_name_dict = {}
        file_id = block_id = 0

        for content_subtype in self.__reg.mr_content_subtypes:
            if self.__reg.mr_sf_dict_holder is not None and content_subtype in self.__reg.mr_sf_dict_holder:
                for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                    row = [None] * len(tags)

                    sf = sf_item['saveframe']
                    file_name = get_first_sf_tag(sf, 'Data_file_name')
                    if file_name not in file_name_dict:
                        file_id += 1
                        file_name_dict[file_name] = file_id
                    row[0], row[1] = file_name_dict[file_name], file_name if len(file_name) > 0 else None
                    sf_allowed_tags = SF_ALLOWED_TAGS[file_type][content_subtype]
                    if 'Constraint_file_ID' in sf_allowed_tags:
                        sf.add_tag('Constraint_file_ID', file_name_dict[file_name], update=True)
                    _name = get_first_sf_tag(sf, 'Sf_framecode').split('_')[0]
                    _name_ = _name.upper()
                    if _name == _name_:
                        _name = getPdbxNmrSoftwareName(_name_)
                        if _name in software_dict:
                            row[2], row[3], row[4] =\
                                software_dict[_name][0], \
                                f'${software_dict[_name][1]}' if _name in defined_software else None, \
                                _name
                        else:
                            software_id += 1
                            _code = f'software_{software_id}'
                            row[2], row[3], row[4] =\
                                software_id, f'${_code}' if _name in defined_software else None, \
                                _name
                            software_dict[_name] = (software_id, _code)
                    if 'Block_ID' in sf_allowed_tags:
                        block_id += 1
                        _block_id = str(block_id)
                        sf.add_tag('Block_ID', _block_id, update=True)
                        row[5] = _block_id
                    constraint_type = sf_item['constraint_type']
                    if constraint_type == 'planarity':
                        try:
                            for item in sf_item['loop']['data']:
                                auth_comp_id = item[4]
                                peptide, nucleotide, _ = self.__reg.csStat.getTypeOfCompId(auth_comp_id)
                                if peptide:
                                    constraint_type = 'protein peptide planarity'
                                    break
                                if nucleotide:
                                    constraint_type = 'nucleic acid base planarity'
                        except (KeyError, IndexError):
                            pass

                    if constraint_type == 'scalar J-coupling':  # DAOTHER-9471
                        constraint_type = 'coupling constant'
                    if constraint_type == 'angle database':  # DAOTHER-9471
                        constraint_type = 'protein dihedral angle'
                    if constraint_type == 'paramagnetic relaxation enhancement':  # DAOTHER-9471
                        constraint_type = 'line broadening'
                    constraint_subtype = (get_first_sf_tag(sf, 'Constraint_type') if content_subtype != 'other_restraint'
                                          else get_first_sf_tag(sf, 'Definition'))
                    if len(constraint_subtype) == 0:
                        constraint_subtype = None
                    if content_subtype == 'auto_relax_restraint'\
                       and get_first_sf_tag(sf, 'Common_relaxation_type_name') == 'paramagnetic relaxation enhancement':
                        constraint_subtype = 'PRE'
                    if sf_item['file_type'] == 'nm-res-sax':
                        constraint_subtype = 'SAXS'
                    if constraint_subtype is not None and constraint_subtype == 'RDC':
                        constraint_type = 'dipolar coupling'  # DAOTHER-9471
                    if constraint_type == 'scalar J-coupling':  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'coupling constant', 'J-couplings'
                    if constraint_type in ('hydrogen bond', 'disulfide bond', 'diselenide bond'):  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'distance', constraint_type
                    if constraint_type in ('carbon chemical shift', 'proton chemical shift'):  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'chemical shift', f'{constraint_type}s'
                    if constraint_type == 'floating chiral stereo assignments':  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'chemical shift', constraint_type
                    if constraint_type == 'NOESY peak volume':  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'peak volume', 'NOE'
                    if constraint_type == 'radius of gyration':  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'coordinate geometry', constraint_type
                    if constraint_type == 'small angle X-ray scattering':  # DAOTHER-9471
                        constraint_type, constraint_subtype = 'coordinate geometry', 'SAXS'

                    if constraint_subtype is not None:
                        if 'prochirality' in constraint_subtype:  # DAOTHER-9471
                            constraint_subtype = 'prochirality'
                        if 'NCS restraint' in constraint_subtype:  # DAOTHER-9471
                            constraint_subtype = 'symmetry'
                        if constraint_subtype == 'angle restraint':  # DAOTHER-9471
                            constraint_subtype = 'general angle'
                        if constraint_subtype == 'chemical shift perturbation':  # DAOTHER-9471
                            constraint_subtype = 'CSP'
                        if constraint_subtype == 'covalent bond linkage':  # DAOTHER-9471
                            constraint_subtype = 'covalent bond'
                        if constraint_subtype == 'paramagnetic relaxation':  # DAOTHER-9471
                            constraint_subtype = 'PRE'
                        if 'planality' in constraint_subtype:  # DAOTHER-9471
                            constraint_subtype = None
                        if 'radius of gyration' in constraint_subtype:  # DAOTHER-9471
                            constraint_type, constraint_subtype = 'coordinate geometry', constraint_type
                        if constraint_subtype == 'unknown':  # DAOTHER-9471
                            constraint_subtype = 'Not applicable'

                    constraint_subsubtype = sf_item.get('constraint_subsubtype')

                    try:
                        id_col = sf_item['loop'].tags.index('ID')
                        count = 0

                        prev_id = -1
                        for _row in sf_item['loop']:
                            _id = int(_row[id_col])
                            if _id == prev_id:
                                continue
                            prev_id = _id
                            count += 1

                        sf_item['id'] = count
                    except AttributeError:
                        pass

                    row[6], row[7], row[8], row[9] =\
                        constraint_type, constraint_subtype, constraint_subsubtype, sf_item['id']
                    row[10], row[11] = 1, self.__reg.entry_id

                    cf_loop.add_data(row)

        ext_mr_sf_holder = []

        if AR_FILE_PATH_LIST_KEY in self.__reg.inputParamDict:

            fileListId = self.__reg.file_path_list_len

            for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:
                file_path = ar['file_name']

                input_source = self.__reg.report.input_sources[fileListId]
                input_source_dic = input_source.get()

                mr_file_type = input_source_dic['file_type']

                fileListId += 1

                if mr_file_type != 'nm-res-oth':
                    continue

                original_file_name = None
                if 'original_file_name' in input_source_dic:
                    if input_source_dic['original_file_name'] is not None:
                        original_file_name = os.path.basename(input_source_dic['original_file_name'])

                self.__reg.list_id_counter = incListIdCounter(None, self.__reg.list_id_counter)

                list_id = self.__reg.list_id_counter['other_restraint']

                sf_framecode = f'NMR_restraints_not_interpreted_{list_id}'

                dir_path = os.path.dirname(file_path)

                details = data_format = None

                unknown_mr_desc = os.path.join(dir_path, '.entry_with_unknown_mr')
                if os.path.exists(unknown_mr_desc):
                    with open(unknown_mr_desc, 'r') as ifh:
                        details = ifh.read().splitlines()
                        data_format = details[0].split(' ')[0]
                        if not data_format.isupper():
                            data_format = None
                        break

                sf = getSaveframe(None, sf_framecode, list_id, self.__reg.entry_id, original_file_name,
                                  constraintType=details)

                file_id += 1
                sf.add_tag('Constraint_file_ID', file_id, update=True)

                block_id += 1
                _block_id = str(block_id)
                sf.add_tag('Block_ID', _block_id, update=True)

                row = [None] * len(tags)
                row[0], row[1], row[5] = file_id, original_file_name, _block_id

                if data_format is not None and data_format != 'UNKNOWN':
                    if data_format in software_dict:
                        row[2], row[3], row[4] =\
                            software_dict[data_format][0], \
                            f'${software_dict[data_format][1]}' if data_format in defined_software else None, \
                            data_format
                    else:
                        software_id += 1
                        _code = f'software_{software_id}'
                        row[2], row[3], row[4] =\
                            software_id, \
                            f'${_code}' if data_format in defined_software else None, \
                            data_format
                        software_dict[data_format] = (software_id, _code)

                sel_res_cif_file = os.path.join(dir_path, file_path + '-selected-as-res-cif')
                sel_res_oth_file = os.path.join(dir_path, file_path + '-selected-as-res-oth')

                if os.path.exists(sel_res_cif_file):
                    data_format = 'mmCIF'

                sf.add_tag('Text_data_format', data_format)

                with open(file_path, 'r', encoding='ascii', errors='ignore') as ifh:
                    sf.add_tag('Text_data', ifh.read())

                row[10], row[11] = 1, self.__reg.entry_id

                # cf_loop.add_data(row)

                ext_mr_sf_holder.append(sf)

                if not os.path.exists(sel_res_cif_file) and not os.path.exists(sel_res_oth_file):

                    if self.__reg.internal_mode:

                        err = f"Uninterpreted restraints are stored in {sf_framecode} saveframe as raw text format. "\
                            "@todo: It needs to be reviewed."

                        self.__reg.report.error.appendDescription('internal_error',
                                                                  f"+{self.__class_name__}.mergeLegacyData() ++ Error  - {err}")

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.mergeLegacyData() ++ Error  - {err}\n")

                    else:

                        file_name = input_source_dic['file_name']
                        if file_name != original_file_name and original_file_name is not None:
                            file_name = f"{original_file_name} ({file_name})"

                        warn = f"We could not identify restraint file format of {file_name!r}. "\
                               "In order to add file format support in the future, "\
                               "the contents is temporarily stored as-is in the _Other_data_type_list.Text_data tag "\
                               "and will be converted during future data remediation if the data matches a known restraint format."

                        self.__reg.report.warning.appendDescription('unsupported_mr_data',
                                                                    {'file_name': file_name, 'description': warn, 'inheritable': True})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.mergeLegacyData() ++ Warning  - {warn}\n")

        cst_sf.add_loop(cf_loop)

        if len(cf_loop) > 0:
            master_entry.add_saveframe(cst_sf)

        # resolve CYANA distance subtype

        dat = cf_loop.get_tag(['Constraint_filename', 'Software_name', 'Block_ID',
                               'Constraint_type', 'Constraint_subtype', 'Constraint_subsubtype'])

        for dist_subtype in ['NOE', 'ROE', 'hydrogen bond', 'disulfide bond', 'diselenide bond']:
            cyana_subtype = {}
            for row in dat:
                if row[1] == 'CYANA' and row[3] == 'distance' and row[4] == dist_subtype and row[5] == 'simple':
                    if row[0] not in cyana_subtype or row[2] in EMPTY_VALUE:
                        cyana_subtype[row[0]] = []
                    cyana_subtype[row[0]].append(row[2] if isinstance(row[2], str) else str(row[2]))

            if any(True for v in cyana_subtype.values() if len(v) > 1):
                for v in cyana_subtype.values():
                    if len(v) < 2:
                        continue
                    cyana_potential_type = {}
                    for block_id in v:
                        for sf in master_entry.get_saveframes_by_category('general_distance_constraints'):
                            _block_id = get_first_sf_tag(sf, 'Block_ID')
                            if _block_id in EMPTY_VALUE:
                                continue
                            if isinstance(_block_id, int):
                                _block_id = str(_block_id)
                            if _block_id == block_id:
                                cyana_potential_type[get_first_sf_tag(sf, 'Potential_type').split('-')[0]] = block_id
                    if len(cyana_potential_type) > 1:
                        if 'upper' in cyana_potential_type:
                            block_id = cyana_potential_type['upper']
                            for idx, row in enumerate(dat):
                                if row[1] == 'CYANA' and row[3] == 'distance' and row[4] == dist_subtype and row[5] == 'simple'\
                                   and (row[2] if isinstance(row[2], str) else str(row[2])) == block_id:
                                    cf_loop.data[idx][cf_loop.tags.index('Constraint_subtype')] = f'{dist_subtype} (upper bound)'

        update_data_file_name = False
        data_file_name_map = {}

        for content_subtype in self.__reg.mr_content_subtypes:
            if self.__reg.mr_sf_dict_holder is not None and content_subtype in self.__reg.mr_sf_dict_holder:
                if content_subtype != 'other_restraint':
                    lp_category = LP_CATEGORIES[file_type][content_subtype]
                    for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                        sf = sf_item['saveframe']
                        sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                        if content_subtype == 'fchiral_restraint':
                            set_sf_tag(sf, 'Stereo_assigned_count', sf_item['id'])

                        if 'XPLOR-NIH_' in sf_framecode or sf_framecode.startswith('CNS'):
                            if 'XPLOR-NIH' in sf_framecode:
                                alt_sf_framecode = 'XPLOR-NIH/CNS' + sf_framecode[9:]
                            else:
                                alt_sf_framecode = 'XPLOR-NIH/' + sf_framecode

                        else:
                            alt_sf_framecode = sf_framecode

                        if any(True for _sf in master_entry.frame_list if _sf.name in (sf_framecode, alt_sf_framecode)):

                            if self.__reg.internal_mode or self.__reg.bmrb_only:
                                _sf = next(_sf for _sf in master_entry.frame_list if _sf.name in (sf_framecode, alt_sf_framecode))
                                _data_file_name = get_first_sf_tag(_sf, 'Data_file_name')
                                data_file_name = get_first_sf_tag(sf, 'Data_file_name')
                                if len(_data_file_name) > 0 and _data_file_name != data_file_name and self.__reg.internal_mode:
                                    data_file_name_map[data_file_name] = _data_file_name
                                    set_sf_tag(sf, 'Data_file_name', _data_file_name)

                                    fileListId = self.__reg.file_path_list_len

                                    for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:

                                        input_source = self.__reg.report.input_sources[fileListId]
                                        input_source_dic = input_source.get()

                                        fileListId += 1

                                        ar_file_type = input_source_dic['file_type']

                                        if not ar_file_type.startswith('nm-res') or ar_file_type == 'nm-res-mr':
                                            continue

                                        if 'original_file_name' in ar and ar['original_file_name'] not in EMPTY_VALUE:
                                            if ar['original_file_name'] == data_file_name:
                                                ar['original_file_name'] = _data_file_name
                                                update_data_file_name = True
                                                break

                                        elif getRestraintFormatName(ar_file_type).split()[0] in sf_framecode:
                                            ar['original_file_name'] = _data_file_name
                                            update_data_file_name = True
                                            break

                                if any(True for _sf in master_entry.frame_list if _sf.name == sf_framecode):
                                    master_entry.remove_saveframe(sf_framecode)
                                else:
                                    master_entry.remove_saveframe(alt_sf_framecode)

                            else:

                                err = f"Couldn't add a saveframe with name {sf_framecode!r} "\
                                      f"since a saveframe with that name already exists in {original_file_name!r} file. "\
                                      f"Please remove {sf_framecode!r} saveframe and re-upload the {READABLE_FILE_TYPE[file_type]} file."

                                self.__reg.report.error.appendDescription('format_issue',
                                                                          {'file_name': file_name, 'description': err})

                                self.__reg.log.write(f"+{self.__class_name__}.mergeLegacyData() ++ Error  - "
                                                     f"{file_name} {err}\n")
                                continue

                        master_entry.add_saveframe(sf)

                        _lp = next((lp for lp in self.__reg.lp_data[content_subtype] if lp['sf_framecode'] == sf_framecode), None)
                        if _lp is not None:
                            self.__reg.lp_data[content_subtype].remove(_lp)
                            data_file_name = get_first_sf_tag(sf, 'Data_file_name')
                            self.__reg.dpV.testDataConsistencyInLoop(0, data_file_name, 'nmr-star', content_subtype,
                                                                     sf, sf_framecode, lp_category, sf_item['list_id'])

                else:
                    for sf_item in self.__reg.mr_sf_dict_holder[content_subtype]:
                        sf = sf_item['saveframe']
                        sf_framecode = sf.get_tag('Sf_framecode')[0]

                        other_data = {'entry_id': self.__reg.entry_id,
                                      'saveframes': [{'name': sf_framecode,
                                                      'category': 'undefined',
                                                      'tag_prefix': '?',
                                                      'tags': [['Sf_category', 'undefined'],
                                                               ['Sf_framecode', sf_framecode],
                                                               ['Definition', sf.get_tag('Definition')[0]],
                                                               ['Data_file_name', sf.get_tag('Data_file_name')[0]],
                                                               ['ID', sf.get_tag('ID')[0]],
                                                               ['Entry_ID', self.__reg.entry_id]
                                                               ],
                                                      'loops': [{'category': 'unknown',
                                                                 'tags': sf_item['loop']['tags'],
                                                                 'data': sf_item['loop']['data']
                                                                 }]
                                                      }]
                                      }

                        sf.add_tag('Text_data_format', 'json')
                        sf.add_tag('Text_data', getPrettyJson(other_data))

                        if 'XPLOR-NIH_' in sf_framecode or sf_framecode.startswith('CNS'):
                            if 'XPLOR-NIH' in sf_framecode:
                                alt_sf_framecode = 'XPLOR-NIH/CNS' + sf_framecode[9:]
                            else:
                                alt_sf_framecode = 'XPLOR-NIH/' + sf_framecode

                        else:
                            alt_sf_framecode = sf_framecode

                        if any(True for _sf in master_entry.frame_list if _sf.name in (sf_framecode, alt_sf_framecode)):

                            if self.__reg.internal_mode or self.__reg.bmrb_only:
                                _sf = next(_sf for _sf in master_entry.frame_list if _sf.name in (sf_framecode, alt_sf_framecode))
                                _data_file_name = get_first_sf_tag(_sf, 'Data_file_name')
                                data_file_name = get_first_sf_tag(sf, 'Data_file_name')
                                if len(_data_file_name) > 0 and _data_file_name != data_file_name and self.__reg.bmrb_only:
                                    data_file_name_map[data_file_name] = _data_file_name
                                    set_sf_tag(sf, 'Data_file_name', _data_file_name)

                                    fileListId = self.__reg.file_path_list_len

                                    for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:

                                        input_source = self.__reg.report.input_sources[fileListId]
                                        input_source_dic = input_source.get()

                                        fileListId += 1

                                        ar_file_type = input_source_dic['file_type']

                                        if not ar_file_type.startswith('nm-res') or ar_file_type == 'nm-res-mr':
                                            continue

                                        if 'original_file_name' in ar and ar['original_file_name'] not in EMPTY_VALUE:
                                            if ar['original_file_name'] == data_file_name:
                                                ar['original_file_name'] = _data_file_name
                                                update_data_file_name = True
                                                break

                                        else:
                                            ar['original_file_name'] = _data_file_name
                                            update_data_file_name = True
                                            break

                                if any(True for _sf in master_entry.frame_list if _sf.name == sf_framecode):
                                    master_entry.remove_saveframe(sf_framecode)
                                else:
                                    master_entry.remove_saveframe(alt_sf_framecode)

                            else:

                                err = f"Couldn't add a saveframe with name {sf_framecode!r} "\
                                      f"since a saveframe with that name already exists in {original_file_name!r} file. "\
                                      f"Please remove {sf_framecode!r} saveframe and re-upload the {READABLE_FILE_TYPE[file_type]} file."

                                self.__reg.report.error.appendDescription('format_issue',
                                                                          {'file_name': file_name, 'description': err})

                                self.__reg.log.write(f"+{self.__class_name__}.mergeLegacyData() ++ Error  - "
                                                     f"{file_name} {err}\n")
                                continue

                        master_entry.add_saveframe(sf)

        for sf in ext_mr_sf_holder:

            if self.__reg.internal_mode and any(True for _sf in master_entry.frame_list if _sf.name == sf.name):
                continue

            master_entry.add_saveframe(sf)

        if update_data_file_name:

            for idx, row in enumerate(cf_loop):
                if row[1] in data_file_name_map:
                    cf_loop[idx][1] = data_file_name_map[row[1]]

            fileListId = self.__reg.file_path_list_len

            file_names = []

            for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:

                input_source = self.__reg.report.input_sources[fileListId]
                input_source_dic = input_source.get()

                fileListId += 1

                ar_file_type = input_source_dic['file_type']

                if not ar_file_type.startswith('nm-res') or ar_file_type == 'nm-res-mr':
                    continue

                if 'original_file_name' in ar and ar['original_file_name'] not in EMPTY_VALUE:
                    file_name = ar['original_file_name']
                else:
                    file_name = input_source_dic['file_name']

                file_names.append(retrieveOriginalFileName(file_name))

            if len(file_names) > 0:
                set_sf_tag(cst_sf, 'Data_file_name', ','.join(file_names))

        self.__mergeStrPk()

        # if self.__reg.merge_any_pk_as_is:  # DAOTHER-7407 enabled until Phase 2 release
        self.__mergeAnyPkAsIs()

        if self.__reg.bmrb_only and self.__reg.internal_mode:
            self.performBMRBjAnnTasks()

        try:

            content_subtype = 'entry_info'

            # update _Data_set/Datum loop

            sf_category = SF_CATEGORIES[file_type][content_subtype]

            self.__reg.sf_category_list, self.__reg.lp_category_list = self.__reg.nefT.get_inventory_list(master_entry)

            has_entry_info = sf_category in self.__reg.sf_category_list

            if has_entry_info:
                sf = master_entry.get_saveframes_by_category(sf_category)[0]

            else:
                sf_framecode = 'entry_information'

                sf = pynmrstar.Saveframe.from_scratch(sf_framecode)
                sf.set_tag_prefix('_Entry')
                sf.add_tag('Sf_category', sf_framecode)
                sf.add_tag('Sf_framecode', sf_framecode)
                sf.add_tag('ID', self.__reg.entry_id)

            # update _Data_set loop

            lp_category = '_Data_set'

            loop = next((loop for loop in sf.loops if loop.category == lp_category), None)

            if loop is not None:
                del sf[loop]

            lp = pynmrstar.Loop.from_scratch(lp_category)

            items = ['Type', 'Count', 'Entry_ID']

            tags = [lp_category + '.' + item for item in items]

            lp.add_tag(tags)

            for content_subtype in self.__reg.nmr_rep_content_subtypes:
                sf_category = SF_CATEGORIES[file_type][content_subtype]

                if sf_category.endswith('constraints'):  # ignore non-quantitative data set
                    continue

                count = sum(1 for sf in master_entry.frame_list if sf.category == sf_category)

                if count > 0:
                    row = [sf_category, count, self.__reg.entry_id]
                    lp.add_data(row)

            lp.sort_rows('Type')

            sf.add_loop(lp)

            # update _Datum loopa

            lp_category = '_Datum'

            loop = next((loop for loop in sf.loops if loop.category == lp_category), None)

            if loop is not None:
                del sf[loop]

            lp = pynmrstar.Loop.from_scratch(lp_category)

            tags = [lp_category + '.' + item for item in items]

            lp.add_tag(tags)

            datum_counter = self.__reg.dpV.getDatumCounter(master_entry)

            for k, v in datum_counter.items():
                row = [k, v, self.__reg.entry_id]
                lp.add_data(row)

            sf.add_loop(lp)

            if not has_entry_info:
                master_entry.add_saveframe(sf)

        except IndexError as e:
            self.__reg.report.error.appendDescription('internal_error',
                                                      f"+{self.__class_name__}.mergeLegacyData() ++ Error  - " + str(e))

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.mergeLegacyData() ++ Error  - {str(e)}\n")

        master_entry = self.__reg.c2S.normalize_str(master_entry)

        master_entry.write_to_file(self.__reg.dstPath,
                                   show_comments=(self.__reg.bmrb_only and self.__reg.internal_mode),
                                   skip_empty_loops=True, skip_empty_tags=False)

        self.__reg.list_id_counter = None
        self.__reg.mr_sf_dict_holder = None
        self.__reg.pk_sf_holder = None

        # check inventory again

        self.__reg.sf_category_list, self.__reg.lp_category_list = self.__reg.nefT.get_inventory_list(master_entry)

        lp_counts = {t: 0 for t in NMR_CONTENT_SUBTYPES}

        for lp_category in self.__reg.lp_category_list:
            if lp_category in LP_CATEGORIES[file_type].values():
                lp_counts[[k for k, v in LP_CATEGORIES[file_type].items() if v == lp_category][0]] += 1

        mr_loops = 0

        for content_subtype in self.__reg.mr_content_subtypes:
            if content_subtype in lp_counts:
                mr_loops += lp_counts[content_subtype]

        if mr_loops == 0 and not self.__reg.validation_server and not self.__reg.mr_has_valid_star_restraint:

            if 'other_data_types' not in self.__reg.sf_category_list:

                mr_file_names = []

                for fileListId in range(self.__reg.cs_file_path_list_len, self.__reg.file_path_list_len):

                    input_source = self.__reg.report.input_sources[fileListId]
                    input_source_dic = input_source.get()

                    file_type = input_source_dic['file_type']

                    if file_type != 'nmr-star':
                        continue

                    mr_file_names.append(input_source_dic['file_name'])

                if AR_FILE_PATH_LIST_KEY in self.__reg.inputParamDict:

                    fileListId = self.__reg.file_path_list_len

                    for ar in self.__reg.inputParamDict[AR_FILE_PATH_LIST_KEY]:

                        input_source = self.__reg.report.input_sources[fileListId]
                        input_source_dic = input_source.get()

                        file_type = input_source_dic['file_type']

                        fileListId += 1

                        if file_type == 'nm-res-mr':
                            continue

                        mr_file_names.append(input_source_dic['file_name'])

                if len(mr_file_names) > 0:

                    desc = 'uploaded restraint file'\
                        + (f's, {mr_file_names}, are' if len(mr_file_names) > 1 else f', {mr_file_names[0]!r}, is')\
                        + ' consistent with the coordinates'

                    err = "Deposition of restraints used for the structure determination is mandatory. "\
                        f"Please verify {desc} and re-upload valid restraint file(s)."

                    self.__reg.report.error.appendDescription('missing_mandatory_content',
                                                              {'file_name': os.path.basename(self.__reg.dstPath),
                                                               'description': err})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.mergeLegacyData() ++ Error  - {err}\n")

        return True

    def performBMRBjAnnTasks(self, enforce: bool = False) -> bool:
        """ Perform a series of BMRBj specific annotation tasks.
            @note: this method requires additional software packages, network access to PubMed, NCBI Taxonomy, BMRB-API, BMRB ETS, etc
        """

        if self.__reg.combined_mode or not self.__reg.remediation_mode or (self.__reg.dstPath is None and not enforce):
            return True

        if len(self.__reg.star_data) == 0 or self.__reg.star_data[0] is None:
            return False

        try:
            from wwpdb.utils.nmr.ann.BMRBjAnnTasks import BMRBjAnnTasks  # pylint: disable=import-outside-toplevel
        except ImportError:
            try:
                from nmr.ann.BMRBjAnnTasks import BMRBjAnnTasks  # pylint: disable=import-outside-toplevel
            except ImportError:
                return False

        ann = BMRBjAnnTasks(self.__reg)

        return ann.perform(self.__reg.star_data[0])
