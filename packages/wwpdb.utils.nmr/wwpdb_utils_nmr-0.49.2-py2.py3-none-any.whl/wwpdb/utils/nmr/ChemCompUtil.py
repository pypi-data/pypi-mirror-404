##
# File: ChemCompUtil.py
# Date: 18-Feb-2022
#
# Updates:
# 27-Apr-2022  M. Yokochi - enable to use cached data for standard residues
# 11-Nov-2022  M. Yokochi - add getProtonsInSameGroup() (NMR restraint remediation)
# 13-Jun-2023  M. Yokochi - add getEffectiveFormulaWeight()
# 07-Dec-2023  M. Yokochi - add support for PTM items (backbone, n_terminal, c_terminal atom flags)
# 13-Dec-2023  M. Yokochi - add getAtomsBasedOnGreekLetterSystem(), peptideLike() and getTypeOfCompId() (DAOTHER-8945)
# 19-Apr-2024  M. Yokochi - add getRepMethyleneOrAminoProtons() and getNonRepMethyleneOrAminoProtons() (DAOTHER-9317)
# 24-Jun-2025  M. Yokochi - add hasIntervenedAtom() (DAOTHER-7829, 2ky8, D_1300056761)
# 19-Nov-2025  M. Yokochi - add getBondSignature() (DATAQUALITY-2178, NMR data remediation)
##
""" Wrapper class for retrieving chemical component dictionary.
    @author: Masashi Yokochi
"""
__docformat__ = "restructuredtext en"
__author__ = "Masashi Yokochi"
__email__ = "yokochi@protein.osaka-u.ac.jp"
__license__ = "Apache License 2.0"
__version__ = "1.0.2"

import os
import sys
import pickle
import functools

from rmsd.calculate_rmsd import NAMES_ELEMENT, ELEMENT_WEIGHTS  # noqa: F401 pylint: disable=no-name-in-module, import-error, unused-import
from typing import IO, List, Tuple, Optional


try:
    from wwpdb.utils.nmr.NmrDpConstant import (EMPTY_VALUE,
                                               STD_MON_DICT,
                                               PROTON_BEGIN_CODE,
                                               CCD_ID_PAT)
    from wwpdb.utils.config.ConfigInfo import getSiteId
    from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc
    from wwpdb.utils.nmr.io.ChemCompReader import (ChemCompReader,
                                                   is_reserved_lig_code)
    cICc = ConfigInfoAppCc(getSiteId())
    CC_CVS_PATH = cICc.get_site_cc_cvs_path()
except ImportError:
    from nmr.NmrDpConstant import (EMPTY_VALUE,
                                   STD_MON_DICT,
                                   PROTON_BEGIN_CODE,
                                   CCD_ID_PAT)
    from nmr.io.ChemCompReader import (ChemCompReader,
                                       is_reserved_lig_code)
    CC_CVS_PATH = os.path.dirname(__file__) + '/ligand_dict'  # need to setup 'ligand_dict' CCD resource for NMR restraint processing


class ChemCompUtil:
    """ Wrapper class for retrieving chemical component dictionary.
    """
    __slots__ = ('__cacheFile',
                 '__ccR',
                 'lastCompId',
                 'lastStatus',
                 'lastChemCompDict',
                 'lastAtomDictList',
                 'lastBondDictList',
                 '__cachedDict',
                 '__failedCompId')

    def __init__(self, verbose: bool = False, log: IO = sys.stderr):
        # pickle file name of cached dictionary for standard residues
        self.__cacheFile = os.path.dirname(__file__) + '/chem_comp_util/std_chem_comp.pkl'

        self.__ccR = ChemCompReader(verbose, log)
        self.__ccR.setCachePath(CC_CVS_PATH)

        self.lastCompId = None
        self.lastStatus = False
        self.lastChemCompDict = None
        self.lastAtomDictList = None
        self.lastBondDictList = None

        def load_dict_from_pickle(file_name):
            """ Load cached dictionary from pickle file.
            """

            if os.path.exists(file_name):

                with open(file_name, 'rb') as ifh:
                    return pickle.load(ifh)

            return {}

        self.__cachedDict = load_dict_from_pickle(self.__cacheFile)
        self.__failedCompId = []

    def updateChemCompDict(self, compId: str, ligand: bool = True) -> bool:
        """ Update CCD information for a given comp_id.
            @return: True for successfully update CCD information or False for the case a given comp_id does not exist in CCD
        """

        if compId in EMPTY_VALUE:
            return False

        compId = compId.upper()

        if not CCD_ID_PAT.match(compId) or (not ligand and is_reserved_lig_code(compId)):
            return False

        if compId in self.__failedCompId:
            return False

        if compId != self.lastCompId:
            self.lastStatus = False if '_' in compId else self.__ccR.setCompId(compId, ligand)
            self.lastCompId = compId

            if self.lastStatus:
                if compId in self.__cachedDict:
                    self.lastChemCompDict = self.__cachedDict[compId]['chem_comp']
                    self.lastAtomDictList = self.__cachedDict[compId]['chem_comp_atom']
                    self.lastBondDictList = self.__cachedDict[compId]['chem_comp_bond']
                else:
                    self.lastChemCompDict = self.__ccR.getChemCompDict()
                    self.lastAtomDictList = self.__ccR.getAtomDictList()
                    self.lastBondDictList = self.__ccR.getBondDictList()
                    self.__cachedDict[compId] = {'chem_comp': self.lastChemCompDict,
                                                 'chem_comp_atom': self.lastAtomDictList,
                                                 'chem_comp_bond': self.lastBondDictList}

            else:
                self.__failedCompId.append(compId)

        return self.lastStatus

    @functools.lru_cache(maxsize=128)
    def getMethylAtoms(self, compId: str) -> List[str]:
        """ Return atoms in methyl group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        carbons = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'C')

        for carbon in carbons:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != carbon else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == carbon and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == carbon and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 3:
                continue
            atmList.append(carbon)
            atmList.extend(protons)

        return atmList

    @functools.lru_cache(maxsize=128)
    def getMethylProtons(self, compId: str) -> List[str]:
        """ Return all protons in methyl group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        carbons = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'C')

        for carbon in carbons:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != carbon else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == carbon and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == carbon and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 3:
                continue
            atmList.extend(protons)

        return atmList

    @functools.lru_cache(maxsize=128)
    def getRepMethylProtons(self, compId: str) -> List[str]:
        """ Return representative protons in methyl group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        carbons = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'C')

        for carbon in carbons:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != carbon else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == carbon and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == carbon and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 3:
                continue
            atmList.append(protons[0])

        return atmList

    @functools.lru_cache(maxsize=128)
    def getNonRepMethylProtons(self, compId: str) -> List[str]:
        """ Return non-representative protons in methyl group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        carbons = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'C')

        for carbon in carbons:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != carbon else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == carbon and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == carbon and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 3:
                continue
            atmList.extend(protons[1:])

        return atmList

    @functools.lru_cache(maxsize=128)
    def getRepMethyleneOrAminoProtons(self, compId: str) -> List[str]:
        """ Return representative protons in methylene/amino group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        corns = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] in ('C', 'N'))

        for corn in corns:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != corn else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == corn and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == corn and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 2:
                continue
            atmList.append(protons[0])

        return atmList

    @functools.lru_cache(maxsize=128)
    def getNonRepMethyleneOrAminoProtons(self, compId: str) -> List[str]:
        """ Return non-representative protons in methylene/amino group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        corns = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] in ('C', 'N'))

        for corn in corns:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != corn else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == corn and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == corn and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 2:
                continue
            atmList.extend(protons[1:])

        return atmList

    @functools.lru_cache(maxsize=128)
    def getRepAminoProtons(self, compId: str) -> List[str]:
        """ Return representative protons in amino group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        ns = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'N')

        for n in ns:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != n else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == n and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == n and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 2:
                continue
            atmList.append(protons[0])

        return atmList

    @functools.lru_cache(maxsize=128)
    def getNonRepAminoProtons(self, compId: str) -> List[str]:
        """ Return non-representative protons in amino group of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        ns = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'N')

        for n in ns:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != n else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == n and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == n and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 2:
                continue
            atmList.extend(protons[1:])

        return atmList

    @functools.lru_cache(maxsize=128)
    def getImideProtons(self, compId: str) -> List[str]:
        """ Return imide protons of a given comp_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        atmList = []

        ns = (a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'N')

        for n in ns:
            protons = [(b['atom_id_1'] if b['atom_id_1'] != n else b['atom_id_2'])
                       for b in self.lastBondDictList
                       if (b['atom_id_1'] == n and b['atom_id_2'][0] in PROTON_BEGIN_CODE)
                       or (b['atom_id_2'] == n and b['atom_id_1'][0] in PROTON_BEGIN_CODE)]
            if len(protons) != 1:
                continue
            acyl_c = [(b['atom_id_1'] if b['atom_id_1'] != n else b['atom_id_2'])
                      for b in self.lastBondDictList
                      if (b['atom_id_1'] == n and b['atom_id_2'][0] == 'C')
                      or (b['atom_id_2'] == n and b['atom_id_1'][0] == 'C')]
            if len(acyl_c) != 2:
                continue
            acyl_o = [(b['atom_id_1'] if b['atom_id_1'] not in acyl_c else b['atom_id_2'])
                      for b in self.lastBondDictList if b['value_order'] == 'DOUB'
                      and ((b['atom_id_1'] in acyl_c and b['atom_id_2'][0] == 'O')
                           or (b['atom_id_2'] in acyl_c and b['atom_id_1'][0] == 'O'))]
            if len(acyl_o) != 2:
                continue
            atmList.append(protons[0])

        return atmList

    @functools.lru_cache(maxsize=256)
    def getBondedAtoms(self, compId: str, atomId: str, exclProton: bool = False, onlyProton: bool = False) -> List[str]:
        """ Return bonded atoms to a given atom.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        bondedAtoms = [(b['atom_id_1'] if b['atom_id_1'] != atomId else b['atom_id_2'])
                       for b in self.lastBondDictList if atomId in (b['atom_id_1'], b['atom_id_2'])]

        if not exclProton and not onlyProton:
            return bondedAtoms

        allProtons = [a['atom_id'] for a in self.lastAtomDictList if a['type_symbol'] == 'H']

        return [a for a in bondedAtoms if (exclProton and a not in allProtons) or (onlyProton and a in allProtons)]

    @functools.lru_cache(maxsize=256)
    def getProtonsInSameGroup(self, compId: str, atomId: str, exclSelf: bool = False) -> List[str]:
        """ Return protons in the same group of a given comp_id and atom_id.
        """

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        bondedTo = self.getBondedAtoms(compId, atomId)

        if len(bondedTo) == 0:
            return []

        attached = self.getBondedAtoms(compId, bondedTo[0], onlyProton=True)

        return [p for p in attached if (exclSelf and p != atomId) or not exclSelf]

    def getAtomsBasedOnGreekLetterSystem(self, compId: str, atomId: str) -> List[str]:
        """ Return atoms match with greek letter system of a given comp_id.
        """

        if len(atomId) < 2:
            return []

        elem = atomId[0]

        if elem not in ('H', 'C', 'N', 'O', 'S', 'P'):
            return []

        greekLetter = atomId[1]

        if greekLetter not in ('A', 'B', 'G', 'D', 'E', 'Z', 'H'):
            return []

        if compId != self.lastCompId and not self.updateChemCompDict(compId):
            return []

        touched = ['N', 'C', 'O', 'OXT']
        parents = ['CA']

        if not any(a['atom_id'] == 'CA' for a in self.lastAtomDictList):
            if not any(a['atom_id'] == 'C' for a in self.lastAtomDictList):  # ACA:QA -> H21, H22 (5nwu)
                return []
            bonded = [(b['atom_id_1'] if b['atom_id_1'] != 'C' else b['atom_id_2'])
                      for b in self.lastBondDictList if 'C' in (b['atom_id_1'], b['atom_id_2'])]
            if len(bonded) == 0:
                return []
            parents = [b for b in bonded if b not in touched]
            if len(parents) == 0:
                return []

        for letter in ['A', 'B', 'G', 'D', 'E', 'Z', 'H']:

            if greekLetter == letter:
                atoms = parents
                for p in parents:
                    atoms.extend(self.getBondedAtoms(compId, p, onlyProton=True))
                return sorted(list(set(a for a in atoms if a[0] == elem)))

            touched.extend(parents)

            _parents = []
            for p in parents:
                _parents.extend([a for a in self.getBondedAtoms(compId, p, exclProton=True) if a not in touched])

            if len(_parents) == 0:
                return []

            parents = list(set(_parents))

        return []

    def getBondSignature(self, compId: str, atomId: str) -> Tuple[List[str], List[str]]:
        """ Return abstract covalent bond pattern of a given comp_id and atom_id.
        """

        bondedTo = self.getBondedAtoms(compId, atomId)

        first, second = [a[0] for a in bondedTo], []

        for a in bondedTo:
            second.extend([b[0] for b in self.getBondedAtoms(compId, a, exclProton=True)])

        return sorted(first), sorted(second)

    def hasBond(self, compId: str, atomId1: str, atomId2: str) -> bool:
        """ Return whether given two atoms are connected by a covalent bond.
        """

        return atomId2 in self.getBondedAtoms(compId, atomId1)

    def hasIntervenedAtom(self, compId: str, atomId1: str, atomId2: str) -> bool:
        """ Return whether given two atoms are connected through an intervened atom.
        """

        return len(set(self.getBondedAtoms(compId, atomId1)) & set(self.getBondedAtoms(compId, atomId2))) == 1

    @functools.lru_cache(maxsize=128)
    def peptideLike(self, compId: Optional[str] = None) -> bool:
        """ Return whether a given comp_id is peptide-like component.
        """

        if compId is not None:
            if not self.updateChemCompDict(compId):
                return False

        ctype = self.lastChemCompDict['type'].upper()

        if 'PEPTIDE' in ctype:
            return True

        if 'DNA' in ctype or 'RNA' in ctype or 'SACCHARIDE' in ctype:
            return False

        peptide_like = len([a for a in self.lastAtomDictList
                            if a['atom_id'] in ("C", "CA", "H", "HA", "HA2", "HA3", "N", "O")])

        nucleotide_like = len([a for a in self.lastAtomDictList
                               if a['atom_id'] in ("C1'", "C2'", "C3'", "C4'", "C5'",
                                                   "H1'", "H2'", "H2''", "H3'", "H4'", "H5'", "H5''", "HO2'",
                                                   "P", "OP1", "OP2", "O5'", "O3'")])

        carbohydrate_like = len([a for a in self.lastAtomDictList
                                 if a['atom_id'] in ("C1", "C2", "C3", "C4", "C5", "C6",
                                                     "H1", "H2", "H3", "H4", "H5", "H61", "H62",
                                                     "O1", "O4", "O6")])

        return peptide_like > nucleotide_like and peptide_like > carbohydrate_like

    @functools.lru_cache(maxsize=128)
    def getTypeOfCompId(self, compId: Optional[str] = None) -> Tuple[bool, bool, bool]:
        """ Return type of a given comp_id.
            @return: array of bool: peptide, nucleotide, carbohydrate
        """

        if compId is not None:
            if not self.updateChemCompDict(compId):
                return (False, False, False)

        results = [False] * 3

        ctype = self.lastChemCompDict['type'].upper()

        if 'PEPTIDE' in ctype:
            results[0] = True
            return tuple(results)

        if 'DNA' in ctype or 'RNA' in ctype:
            results[1] = True
            return tuple(results)

        if 'SACCHARIDE' in ctype:
            results[2] = True
            return tuple(results)

        peptide_like = len([a for a in self.lastAtomDictList
                            if a['atom_id'] in ("C", "CA", "H", "HA", "HA2", "HA3", "N", "O")])

        nucleotide_like = len([a for a in self.lastAtomDictList
                               if a['atom_id'] in ("C1'", "C2'", "C3'", "C4'", "C5'",
                                                   "H1'", "H2'", "H2''", "H3'", "H4'", "H5'", "H5''", "HO2'",
                                                   "P", "OP1", "OP2", "O5'", "O3'")])

        carbohydrate_like = len([a for a in self.lastAtomDictList
                                 if a['atom_id'] in ("C1", "C2", "C3", "C4", "C5", "C6",
                                                     "H1", "H2", "H3", "H4", "H5", "H61", "H62",
                                                     "O1", "O4", "O6")])

        results[0] = peptide_like > nucleotide_like and peptide_like > carbohydrate_like
        results[1] = nucleotide_like > peptide_like and nucleotide_like > carbohydrate_like
        results[2] = carbohydrate_like > peptide_like and carbohydrate_like > nucleotide_like

        return tuple(results)

    @functools.lru_cache(maxsize=128)
    def getEffectiveFormulaWeight(self, compId: str) -> float:
        """ Return effective formula weight of a given comp_id.
        """

        if not self.updateChemCompDict(compId):
            return 0.0

        if 'formula_weight' not in self.lastChemCompDict:
            return 0.0

        try:

            fw = float(self.lastChemCompDict['formula_weight'])

        except ValueError:
            return 0.0

        peptide_like = self.peptideLike()

        leavingTypeSymbols = [a['type_symbol'] for a in self.lastAtomDictList
                              if not (a['leaving_atom_flag'] != 'Y'
                                      or (peptide_like
                                          and a['n_terminal_atom_flag'] == 'N'
                                          and a['c_terminal_atom_flag'] == 'N'))]

        try:

            for symbol in leavingTypeSymbols:
                fw -= ELEMENT_WEIGHTS[NAMES_ELEMENT[symbol.title()]]

        except KeyError:
            return 0.0

        return fw

    def write_std_dict_as_pickle(self):
        """ Write dictionary for standard residues as pickle file.
        """

        for compId in STD_MON_DICT:
            self.updateChemCompDict(compId)

        def write_dict_as_pickle(obj, file_name):
            """ Write dictionary as pickle file.
            """

            if isinstance(obj, dict):

                with open(file_name, 'wb') as ofh:
                    pickle.dump(obj, ofh)

        write_dict_as_pickle(self.__cachedDict, self.__cacheFile)
