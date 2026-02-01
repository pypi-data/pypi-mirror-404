##
# File: BMRBCsStatUpdater.py
# Date: 18-Dec-2025
#
# Updates:
##
""" BMRB chemical shift statistics updater
    @author: Masashi Yokochi
"""
__docformat__ = "restructuredtext en"
__author__ = "Masashi Yokochi"
__email__ = "yokochi@protein.osaka-u.ac.jp"
__license__ = "Apache License 2.0"
__version__ = "1.0.0"


try:
    from wwpdb.utils.nmr.BMRBChemShiftStat import BMRBChemShiftStat
except ImportError:
    from nmr.BMRBChemShiftStat import BMRBChemShiftStat


if __name__ == '__main__':
    cs_stat = BMRBChemShiftStat()

    cs_stat.updateStatCsvFiles()

    cs_stat.loadStatFromCsvFiles()

    assert cs_stat.testAtomNomenclatureOfLibrary()

    cs_stat.writeStatAsPickleFiles()
