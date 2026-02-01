##
# File: ChemCompReader.py
# Date: 31-May-2010  John Westbrook
#
# Update:
# 06-Aug-2010 - jdw - generalized construction of methods to apply to any category
#                     add accessors for lists of dictionaries
# 12-May-2011 - rps - added check for None when asking for category Object in __getDataList()
# 24-Oct-2012 - rps - updated to reflect reorganization of modules in pdbx packages
# 17-Jan-2025 - my  - added is_reserved_lig_code() from AlignUtil.py (DAOTHER-7204, 7388)
##
""" A collection of classes parsing CCD CIF files.
"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook, Masashi Yokochi"
__email__ = "jwest@rcsb.rutgers.edu, yokochi@protein.osaka-u.ac.jp"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "1.0.6"

import sys
import os

from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.PdbxReader import PdbxReader

from typing import IO, List, Optional

try:
    from wwpdb.utils.nmr.NmrDpConstant import (EMPTY_VALUE,
                                               RESERVED_LIG_CODE,
                                               CCD_ID_PAT)
except ImportError:
    from nmr.NmrDpConstant import (EMPTY_VALUE,
                                   RESERVED_LIG_CODE,
                                   CCD_ID_PAT)


# items of CCD category
CCD_ITEM_DICT = {'chem_comp': [('_chem_comp.id', 'id', 'str', ''),
                               ('_chem_comp.name', 'name', 'str', ''),
                               ('_chem_comp.type', 'type', 'str', ''),
                               ('_chem_comp.pdbx_type', 'pdb_type', 'str', ''),
                               ('_chem_comp.formula', 'formula', 'str', ''),
                               ('_chem_comp.mon_nstd_parent_comp_id', 'parent_comp_id', 'str', ''),
                               ('_chem_comp.pdbx_synonyms', 'synonyms', 'str', ''),
                               ('_chem_comp.pdbx_formal_charge', 'formal_charge', 'int', 0),
                               ('_chem_comp.pdbx_initial_date', 'initial_date', 'str', ''),
                               ('_chem_comp.pdbx_modified_date', 'modified_date', 'str', ''),
                               ('_chem_comp.pdbx_ambiguous_flag', 'ambiguous_flag', 'str', ''),
                               ('_chem_comp.pdbx_release_status', 'release_status', 'str', ''),
                               ('_chem_comp.pdbx_replaced_by', 'replaced_by', 'str', ''),
                               ('_chem_comp.pdbx_replaces', 'replaces', 'str', ''),
                               ('_chem_comp.formula_weight', 'formula_weight', 'float', None),
                               ('_chem_comp.one_letter_code', 'one_letter_code', 'str', ''),
                               ('_chem_comp.three_letter_code', 'three_letter_code', 'str', ''),
                               ('_chem_comp.pdbx_model_coordinates_details', 'model_coordinates_details', 'str', ''),
                               ('_chem_comp.pdbx_model_coordinates_missing_flag', 'model_coordinates_missing_flag', 'str', ''),
                               ('_chem_comp.pdbx_ideal_coordinates_details', 'ideal_coordinates_details', 'str', ''),
                               ('_chem_comp.pdbx_ideal_coordinates_missing_flag', 'ideal_coordinates_missing_flag', 'str', ''),
                               ('_chem_comp.pdbx_model_coordinates_db_code', 'model_coordinates_db_code', 'str', ''),
                               ('_chem_comp.pdbx_subcomponent_list', 'subcomponent_list', 'str', ''),
                               ('_chem_comp.pdbx_processing_site', 'processing_site', 'str', '')
                               ],
                 'chem_comp_atom': [('_chem_comp_atom.comp_id', 'comp_id', 'str', ''),
                                    ('_chem_comp_atom.atom_id', 'atom_id', 'str', ''),
                                    ('_chem_comp_atom.alt_atom_id', 'alt_atom_id', 'str', ''),
                                    ('_chem_comp_atom.type_symbol', 'type_symbol', 'str', ''),
                                    ('_chem_comp_atom.charge', 'charge', 'int', 0),
                                    ('_chem_comp_atom.pdbx_align', 'align', 'str', ''),
                                    ('_chem_comp_atom.pdbx_aromatic_flag', 'aromatic_flag', 'str', ''),
                                    ('_chem_comp_atom.pdbx_leaving_atom_flag', 'leaving_atom_flag', 'str', ''),
                                    ('_chem_comp_atom.pdbx_stereo_config', 'stereo_config', 'str', ''),
                                    ('_chem_comp_atom.model_Cartn_x', 'x', 'float', None),
                                    ('_chem_comp_atom.model_Cartn_y', 'y', 'float', None),
                                    ('_chem_comp_atom.model_Cartn_z', 'z', 'float', None),
                                    ('_chem_comp_atom.pdbx_model_Cartn_x_ideal', 'x_ideal', 'float', None),
                                    ('_chem_comp_atom.pdbx_model_Cartn_y_ideal', 'y_ideal', 'float', None),
                                    ('_chem_comp_atom.pdbx_model_Cartn_z_ideal', 'z_ideal', 'float', None),
                                    ('_chem_comp_atom.pdbx_component_atom_id', 'component_atom_id', 'str', ''),
                                    ('_chem_comp_atom.pdbx_component_comp_id', 'component_comp_id', 'str', ''),
                                    ('_chem_comp_atom.pdbx_ordinal', 'ordinal', 'int', None),
                                    ('_chem_comp_atom.pdbx_backbone_atom_flag', 'backbone_atom_flag', 'str', ''),
                                    ('_chem_comp_atom.pdbx_n_terminal_atom_flag', 'n_terminal_atom_flag', 'str', ''),
                                    ('_chem_comp_atom.pdbx_c_terminal_atom_flag', 'c_terminal_atom_flag', 'str', '')
                                    ],
                 'chem_comp_bond': [('_chem_comp_bond.comp_id', 'comp_id', 'str', ''),
                                    ('_chem_comp_bond.atom_id_1', 'atom_id_1', 'str', ''),
                                    ('_chem_comp_bond.atom_id_2', 'atom_id_2', 'str', ''),
                                    ('_chem_comp_bond.value_order', 'value_order', 'str', ''),
                                    ('_chem_comp_bond.pdbx_aromatic_flag', 'aromatic_flag', 'str', ''),
                                    ('_chem_comp_bond.pdbx_stereo_config', 'stereo_config', 'str', ''),
                                    ('_chem_comp_bond.pdbx_ordinal', 'ordinal', 'int', None)
                                    ],
                 'chem_comp_descriptor': [('_pdbx_chem_comp_descriptor.comp_id', 'comp_id', 'str', ''),
                                          ('_pdbx_chem_comp_descriptor.type', 'type', 'str', ''),
                                          ('_pdbx_chem_comp_descriptor.program', 'program', 'str', ''),
                                          ('_pdbx_chem_comp_descriptor.program_version', 'program_version', 'str', ''),
                                          ('_pdbx_chem_comp_descriptor.descriptor', 'descriptor', 'str', '')],
                 'chem_comp_identifier': [('_pdbx_chem_comp_identifier.comp_id', 'comp_id', 'str', ''),
                                          ('_pdbx_chem_comp_identifier.type', 'type', 'str', ''),
                                          ('_pdbx_chem_comp_identifier.program', 'program', 'str', ''),
                                          ('_pdbx_chem_comp_identifier.program_version', 'program_version', 'str', ''),
                                          ('_pdbx_chem_comp_identifier.identifier', 'identifier', 'str', '')
                                          ]
                 }


def is_reserved_lig_code(comp_id: str) -> bool:
    """ Return a given comp_id is reserved for new ligands. (DAOTHER-7204, 7388)
    """

    if comp_id in RESERVED_LIG_CODE:
        return True

    if len(comp_id) == 2 and comp_id[0].isdigit() and comp_id[1].isdigit() and comp_id != '00':
        return True

    return False


class ChemCompReader:
    """ Accessor methods for parsing CCD CIF files.
    """
    __slots__ = ('__class_name__',
                 '__version__',
                 '__verbose',
                 '__log',
                 '__debug',
                 '__dBlock',
                 '__topCachePath',
                 '__filePath',
                 '__compId',
                 '__lastCompId')

    def __init__(self, verbose: bool = True, log: IO = sys.stdout):
        self.__class_name__ = self.__class__.__name__
        self.__version__ = __version__

        self.__verbose = verbose
        self.__log = log
        self.__debug = False

        # the primary datablock
        self.__dBlock = None

        # the top file tree of CCD
        self.__topCachePath = None

        # the current file path
        self.__filePath = None

        # the current compId
        self.__compId = None

        # the compId of the current datablock
        self.__lastCompId = None

    def setCachePath(self, topCachePath: str = '/data/components/ligand-dict-v4'):
        """ Set the top file tree of CCD.
        """

        self.__topCachePath = topCachePath

    def setCompId(self, compId: str, ligand: bool = True) -> bool:
        """ Set compId and CCD CIF file path based on file tree of CCD.
        """

        if compId in EMPTY_VALUE:
            return False

        self.__compId = compId.upper()

        if not CCD_ID_PAT.match(self.__compId) or (not ligand and is_reserved_lig_code(self.__compId)):
            return False

        self.__filePath = os.path.join(self.__topCachePath,
                                       self.__compId[-2:] if len(self.__compId) > 3 else self.__compId[0],
                                       self.__compId,
                                       self.__compId + '.cif')

        if not os.access(self.__filePath, os.R_OK):
            if self.__verbose:
                self.__log.write(f"+{self.__class_name__}.setCompId() ++ Error  - Missing file {self.__filePath}\n")
            return False

        return True

    def setFilePath(self, filePath: str, compId: str) -> bool:
        """ Set compId and CCD CIF file path.
        """

        try:

            if compId in EMPTY_VALUE:
                return False

            self.__compId = compId.upper()

            if not CCD_ID_PAT.match(self.__compId) or is_reserved_lig_code(self.__compId):
                return False

            self.__filePath = filePath

            if not os.access(self.__filePath, os.R_OK):
                if self.__verbose:
                    self.__log.write(f"+{self.__class_name__}.setFilePath() ++ Error  - Missing file {self.__filePath}\n")
                return False

            return True

        except Exception as e:
            if self.__verbose:
                self.__log.write(f"+{self.__class_name__}.setFilePath() ++ Error  - Set {self.__filePath} failed {str(e)}\n")
            return False

    def getAtomList(self) -> List[list]:
        """ Get a list of list of data from the chem_comp_atom category.
        """

        self.__updateDataBlock()

        return self.__getRowList(catName='chem_comp_atom')

    def getAtomDictList(self) -> List[dict]:
        """ Get a list of dictionary of data from the chem_comp_atom category.
        """

        self.__updateDataBlock()

        return self.__getDictList(catName='chem_comp_atom')

    def getBondList(self) -> List[list]:
        """ Get a list of list of data from the chem_comp_bond category.
        """

        self.__updateDataBlock()

        return self.__getRowList(catName='chem_comp_bond')

    def getBondDictList(self) -> List[dict]:
        """ Get a list of dictionary of data from the chem_comp_bond category.
        """

        self.__updateDataBlock()

        return self.__getDictList(catName='chem_comp_bond')

    def getChemCompDict(self) -> dict:
        """ Get a dictionary of the chem_comp category.
        """

        try:

            self.__updateDataBlock()

            return self.__getDictList(catName='chem_comp')[0]

        except Exception:
            return {}

    def __updateDataBlock(self) -> bool:
        """ Update the definition data for the input compId.
            @return: True for success or False otherwise
        """

        if self.__compId == self.__lastCompId:
            return True

        try:

            if self.__setDataBlock(self.__getDataBlock()):
                self.__lastCompId = self.__compId
                return True

            return False

        except Exception as e:
            if self.__verbose:
                self.__log.write(f"+{self.__class_name__}.__updateDataBlock() ++ Error  - {str(e)}\n")
            return False

    def __getDataBlock(self, blockId: Optional[str] = None) -> Optional[DataContainer]:
        """ Worker method to read CCD CIF file and set the target datablock.
            @return: the first datablock if no blockId is provided
        """

        try:

            with open(self.__filePath, 'r', encoding='utf-8') as ifh:
                myBlockList = []
                pRd = PdbxReader(ifh)
                pRd.read(myBlockList)

            if blockId is not None:

                for block in myBlockList:
                    if (block.getType() == 'data' and block.getName() == blockId):
                        if self.__verbose and self.__debug:
                            block.printIt(self.__log)
                        return block

            else:

                for block in myBlockList:
                    if block.getType() == 'data':
                        if self.__verbose and self.__debug:
                            block.printIt(self.__log)
                        return block

        except Exception as e:
            if self.__verbose:
                self.__log.write(f"+{self.__class_name__}.__getDataBlock() ++ Error  - {str(e)}\n")

        return None

    def __setDataBlock(self, dataBlock: Optional[DataContainer]) -> bool:
        """ Assigns the input datablock as the active internal datablock.
        """

        if dataBlock is None:
            self.__dBlock = None
            return False

        try:

            if dataBlock.getType() == 'data':
                self.__dBlock = dataBlock
                return True

        except Exception:
            pass

        self.__dBlock = None

        return False

    def __getDictList(self, catName: str) -> List[dict]:
        """ Return a list of dictionaries of the input category.
        """

        catObj = self.__dBlock.getObj(catName)

        if catObj is None:
            return []

        def apply_type(ctype, default, val):
            if val in EMPTY_VALUE:
                return default
            if ctype == 'int':
                return int(val)
            if ctype == 'float':
                return float(val)
            return val

        itDict = {itName: idxIt for idxIt, itName in enumerate(catObj.getItemNameList())}

        colTupList = []
        for itTup in CCD_ITEM_DICT[catName]:
            colTupList.append((itDict[itTup[0]] if itTup[0] in itDict else -1, itTup[2], itTup[3], itTup[1]))

        dList = []
        for row in catObj.getRowList():
            uR = {}
            for cTup in colTupList:
                uR[cTup[3]] = apply_type(cTup[1], cTup[2], cTup[2] if cTup[0] < 0 else row[cTup[0]])
            dList.append(uR)

        return dList

    def __getRowList(self, catName: str) -> List[list]:
        """ Return a list a list of data from the input category including
            data types and default value replacement.
        """

        catObj = self.__dBlock.getObj(catName)

        if catObj is None:
            return []

        def apply_type(ctype, default, val):
            if val in EMPTY_VALUE:
                return default
            if ctype == 'int':
                return int(val)
            if ctype == 'float':
                return float(val)
            return val

        itDict = {itName: idxIt for idxIt, itName in enumerate(catObj.getItemNameList())}

        colTupList = []
        for itTup in CCD_ITEM_DICT[catName]:
            colTupList.append((itDict[itTup[0]] if itTup[0] in itDict else -1, itTup[2], itTup[3]))

        dList = []
        for row in catObj.getRowList():
            uR = []
            for cTup in colTupList:
                uR.append(apply_type(cTup[1], cTup[2], cTup[2] if cTup[0] < 0 else row[cTup[0]]))
            dList.append(uR)

        return dList
