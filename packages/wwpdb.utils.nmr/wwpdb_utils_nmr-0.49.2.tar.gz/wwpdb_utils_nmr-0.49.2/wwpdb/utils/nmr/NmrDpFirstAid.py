##
# File: NmrDpFirstAid.py
# Date: 07-Jan-2026
#
# Updates:
##
""" First aid kit for NMR data processing.
    @author: Masashi Yokochi
"""
__docformat__ = "restructuredtext en"
__author__ = "Masashi Yokochi"
__email__ = "yokochi@protein.osaka-u.ac.jp"
__license__ = "Apache License 2.0"
__version__ = "5.0.0"

import os
import re
import shutil
import pynmrstar

from packaging import version
from typing import List, Union, Optional

try:
    from wwpdb.utils.nmr.NmrDpConstant import (CS_FILE_PATH_LIST_KEY,
                                               MR_FILE_PATH_LIST_KEY,
                                               NMR_CONTENT_SUBTYPES,
                                               READABLE_FILE_TYPE,
                                               SF_CATEGORIES,
                                               LP_CATEGORIES,
                                               INDEX_TAGS,
                                               NUM_DIM_ITEMS,
                                               ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG,
                                               SF_TAG_PREFIXES,
                                               AUX_LP_CATEGORIES,
                                               EMPTY_VALUE,
                                               NEF_VERSION,
                                               MAX_DIM_NUM_OF_SPECTRA,
                                               ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS,
                                               DATABLOCK_PAT,
                                               SF_ANONYMOUS_PAT,
                                               SAVE_PAT,
                                               LOOP_PAT,
                                               STOP_PAT,
                                               CIF_STOP_PAT,
                                               CATEGORY_PAT,
                                               TAGVALUE_PAT,
                                               SF_CATEGORY_PAT,
                                               SF_FRAMECODE_PAT)
    from wwpdb.utils.nmr.NmrDpRegistry import NmrDpRegistry
    from wwpdb.utils.nmr.CifToNmrStar import (get_first_sf_tag,
                                              set_sf_tag)
except ImportError:
    from nmr.NmrDpConstant import (CS_FILE_PATH_LIST_KEY,
                                   MR_FILE_PATH_LIST_KEY,
                                   NMR_CONTENT_SUBTYPES,
                                   READABLE_FILE_TYPE,
                                   SF_CATEGORIES,
                                   LP_CATEGORIES,
                                   INDEX_TAGS,
                                   NUM_DIM_ITEMS,
                                   ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG,
                                   SF_TAG_PREFIXES,
                                   AUX_LP_CATEGORIES,
                                   EMPTY_VALUE,
                                   NEF_VERSION,
                                   MAX_DIM_NUM_OF_SPECTRA,
                                   ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS,
                                   DATABLOCK_PAT,
                                   SF_ANONYMOUS_PAT,
                                   SAVE_PAT,
                                   LOOP_PAT,
                                   STOP_PAT,
                                   CIF_STOP_PAT,
                                   CATEGORY_PAT,
                                   TAGVALUE_PAT,
                                   SF_CATEGORY_PAT,
                                   SF_FRAMECODE_PAT)
    from nmr.NmrDpRegistry import NmrDpRegistry
    from nmr.CifToNmrStar import (get_first_sf_tag,
                                  set_sf_tag)


__pynmrstar_v3_3__ = version.parse(pynmrstar.__version__) >= version.parse("3.3.0")


PYNMRSTAR_LP_OBJ_PAT = re.compile(r"\<pynmrstar\.Loop '(.*)'\>")

ONEDEP_ANY_UPLOAD_FILE_NAME_PAT = re.compile(r'^(\S+)\-upload_(\S+)\.V(\d+)$')
ONEDEP_ANY_FILE_NAME_PAT = re.compile(r'^(\S+)\.V(\d+)$')


class NmrDpFirstAid:
    """ First aid kit for NMR data processing.
    """
    __slots__ = ('__class_name__',
                 '__version__',
                 '__reg')

    def __init__(self, registry: NmrDpRegistry):
        self.__class_name__ = self.__class__.__name__
        self.__version__ = __version__

        self.__reg = registry

    def fixFormatIssueOfInputSource(self, file_list_id: int, file_name: str, file_type: str,
                                    srcPath: Optional[str] = None, fileSubType: str = 'S',
                                    message: Optional[dict] = None, tmpPaths: Optional[List[str]] = None,
                                    allowEmpty: bool = False, hasLegacySfIssue: bool = False) -> bool:
        """ Fix format issue of NMR data.
        """

        if not self.__reg.fix_format_issue or srcPath is None or fileSubType not in ('A', 'S', 'R', 'O') or message is None:

            if message is not None:

                missing_loop = True

                err = f"{file_name!r} is not compliant with the {READABLE_FILE_TYPE[file_type]} dictionary."

                if len(message['error']) > 0:

                    if any(True for err_message in message['error'] if 'The mandatory loop' in err_message):

                        err = ''
                        for err_message in message['error']:
                            if 'No such file or directory' not in err_message:
                                err += re.sub('not in list', 'unknown item.', err_message) + ' '
                        err = err[:-1]

                    else:
                        missing_loop = False

                        for err_message in self.__reg.original_error_message[file_list_id]['error']:
                            if 'No such file or directory' not in err_message:
                                err += ' ' + re.sub('not in list', 'unknown item.', err_message)

                if not self.__reg.remediation_mode or not missing_loop or file_list_id > 0:

                    self.__reg.report.error.appendDescription('missing_mandatory_content' if missing_loop else 'format_issue',
                                                              {'file_name': file_name, 'description': err})

                    self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Error  - "
                                         f"{file_name} {err}\n")

                else:

                    self.__reg.has_star_chem_shift = False

                    self.__reg.suspended_errors_for_lazy_eval.append({'missing_mandatory_content':
                                                                      {'file_name': file_name, 'description': err}})

                    if self.__reg.verbose:
                        self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Error  - {err}\n")

            if not hasLegacySfIssue and fileSubType in ('S', 'R', 'O'):
                return False

        star_data_type = self.__reg.nefT.read_input_file(srcPath)[1] if hasLegacySfIssue else None

        _srcPath = srcPath
        if tmpPaths is None:
            tmpPaths = []

        len_tmp_paths = len(tmpPaths)

        msg_template = "Saveframe improperly terminated at end of file."

        if any(True for msg in message['error'] if msg_template in msg):
            warn = msg_template

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                    open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                for line in ifh:
                    ofh.write(line)

                ofh.write('save_\n')

                _srcPath = ofh.name
                tmpPaths.append(_srcPath)

        msg_template = "Loop improperly terminated at end of file."

        if any(True for msg in message['error'] if msg_template in msg):
            warn = msg_template

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                    open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                for line in ifh:
                    ofh.write(line)

                ofh.write('save_\n')

                _srcPath = ofh.name
                tmpPaths.append(_srcPath)

        msg_template = "Invalid file. NMR-STAR files must start with 'data_' followed by the data name. "\
            "Did you accidentally select the wrong file?"

        if any(True for msg in message['error'] if msg_template in msg) or (hasLegacySfIssue and star_data_type == 'Saveframe'):
            warn = 'The datablock must hook saveframe(s).'

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Warning  - {warn}\n")

            with open(_srcPath, 'r', encoding='utf-8') as ifh:
                lines = ifh.read().splitlines()
                total = len(lines)

                j = total - 1

                while total - j < 10:
                    if SAVE_PAT.match(lines[j]) or STOP_PAT.match(lines[j]):
                        break
                    j -= 1

            j += 1
            i = 0

            with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                    open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                ofh.write('data_' + os.path.basename(srcPath) + '\n\n')
                for line in ifh:
                    if i < j:
                        ofh.write(line)
                    i += 1

                _srcPath = ofh.name
                tmpPaths.append(_srcPath)

            # fix single loop file without datablock (D_1300055931)
            if self.__reg.c2S.convert(_srcPath, _srcPath + '~'):
                _srcPath = _srcPath + '~'
                tmpPaths.append(_srcPath)

        msg_template = "Only 'save_NAME' is valid in the body of a NMR-STAR file. Found 'loop_'."

        if any(True for msg in message['error'] if msg_template in msg):
            warn = 'A saveframe, instead of the datablock, must hook the loop.'

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Warning  - {warn}\n")

            pass_datablock = False

            with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                    open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                for line in ifh:
                    if pass_datablock:
                        ofh.write(line)
                    elif DATABLOCK_PAT.match(line):
                        pass_datablock = True
                    else:
                        ofh.write(line)

                _srcPath = ofh.name
                tmpPaths.append(_srcPath)

        msg_template = "Cannot use keywords as data values unless quoted or semi-colon delimited. "\
            "Perhaps this is a loop that wasn't properly terminated"

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = 'Loops must properly terminated.'

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            msg_pattern = re.compile(r'^.*' + msg_template + r".*on line (\d+).*$")

            try:

                g = msg_pattern.search(msg).groups()

                line_num = int(g[0])

                i = 0

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    for line in ifh:
                        if i == line_num:
                            ofh.write('stop_\n')
                        ofh.write(line)
                        i += 1
                    if i == line_num:
                        ofh.write('stop_\n')

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

            except AttributeError:
                pass

        except StopIteration:
            pass

        msg_template = "Cannot have a tag value start with an underscore unless the entire value is quoted. "\
            "You may be missing a data value on the previous line"

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = "Loops must start with the 'loop_' keyword."

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            msg_pattern = re.compile(r'^.*' + msg_template + r".*on line (\d+).*$")

            try:

                g = msg_pattern.search(msg).groups()

                line_num = int(g[0])

                i = 0

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    for line in ifh:
                        if i == line_num - 1:
                            ofh.write('loop_\n')
                        ofh.write(line)
                        i += 1

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

            except AttributeError:
                pass

        except StopIteration:
            pass

        msg_template = "Only 'save_NAME' is valid in the body of a NMR-STAR file. Found"

        try:

            is_cs_cif = False

            if self.__reg.op == 'nmr-cs-str-consistency-check':

                is_cs_cif = True

                try:

                    with open(_srcPath, 'r', encoding='utf-8') as ifh:
                        for line in ifh:
                            if SAVE_PAT.match(line) or STOP_PAT.match(line):
                                is_cs_cif = False
                                break

                    if is_cs_cif:

                        loop_count = 0
                        has_sf_category = has_sf_framecode = False

                        with open(_srcPath, 'r', encoding='utf-8') as ifh:
                            for line in ifh:
                                if LOOP_PAT.match(line):
                                    loop_count += 1
                                elif SF_CATEGORY_PAT.match(line):
                                    has_sf_category = True
                                elif SF_FRAMECODE_PAT.match(line):
                                    has_sf_framecode = True

                        if not has_sf_category and not has_sf_framecode:

                            in_lp = False

                            with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                                    open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                                for line in ifh:
                                    if DATABLOCK_PAT.match(line):
                                        g = DATABLOCK_PAT.search(line).groups()
                                        if loop_count < 2:
                                            ofh.write(f"save_{g[0]}\n")
                                    elif CIF_STOP_PAT.match(line):
                                        if in_lp:
                                            if loop_count < 2:
                                                ofh.write('stop_\nsave_\n')
                                            else:
                                                ofh.write('stop_\n')
                                        else:
                                            ofh.write(line)
                                        in_lp = False
                                    elif LOOP_PAT.match(line):
                                        in_lp = True
                                        ofh.write(line)
                                    else:
                                        if in_lp or loop_count < 2:
                                            ofh.write(line)

                                _srcPath = ofh.name
                                tmpPaths.append(_srcPath)

                        else:

                            if self.__reg.c2S.convert(_srcPath, _srcPath + '~'):
                                _srcPath += '~'
                                tmpPaths.append(_srcPath)

                except AttributeError:
                    pass

            if not is_cs_cif:

                msg = next(msg for msg in message['error'] if msg_template in msg)
                warn = "Loops must start with the 'loop_' keyword."

                self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                            {'file_name': file_name, 'description': warn})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

                msg_pattern = re.compile(r'^.*' + msg_template + r" '(.*)'.*$")

                try:

                    g = msg_pattern.search(msg).groups()

                    tag_name = g[0]

                    tag_name_pattern = re.compile(r'\s*' + tag_name + r'\s*')

                    with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                            open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                        for line in ifh:
                            if tag_name_pattern.match(line) is None:
                                ofh.write(line)
                            else:
                                ofh.write('loop_\n')

                        _srcPath = ofh.name
                        tmpPaths.append(_srcPath)

                except AttributeError:
                    pass

        except StopIteration:
            pass

        msg_template = "'save_' must be followed by saveframe name. You have a 'save_' tag "\
            "which is illegal without a specified saveframe name."

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = "The saveframe must have a specified saveframe name."

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            msg_pattern = re.compile(r'^.*' + msg_template + r".*on line (\d+).*$")

            try:

                g = msg_pattern.search(msg).groups()

                line_num = int(g[0])

                i = 0

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    for line in ifh:
                        if i != line_num:
                            ofh.write(line)
                        else:
                            ofh.write(f"save_{os.path.basename(srcPath)}\n")
                        i += 1

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

            except AttributeError:
                pass

        except StopIteration:
            pass

        msg_template = "The tag prefix was never set! Either the saveframe had no tags, "\
            "you tried to read a version 2.1 file, or there is something else wrong with your file. "\
            "Saveframe error occurred within:"

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = 'The saveframe must have NMR-STAR V3.2 tags. Saveframe error occured:'\
                + msg[len(msg_template):].replace('<pynmrstar.', '').replace("'>", "'")

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            msg_pattern = re.compile(r'^' + msg_template + r" '(.*)'$")

            targets = []

            for msg in message['error']:

                if msg_template not in msg:
                    continue

                try:

                    target = {}

                    g = msg_pattern.search(msg).groups()
                    sf_framecode = str(g[0])

                    target = {'sf_framecode': sf_framecode}

                    pass_sf_framecode = pass_sf_loop = False

                    sf_named_pattern = re.compile(r'\s*save_' + sf_framecode + r'\s*')

                    with open(_srcPath, 'r', encoding='utf-8') as ifh:
                        for line in ifh:
                            if pass_sf_framecode:
                                if pass_sf_loop:
                                    if CATEGORY_PAT.match(line):
                                        target['lp_category'] = '_' + CATEGORY_PAT.search(line).groups()[0]
                                        content_subtype = next((k for k, v in LP_CATEGORIES[file_type].items()
                                                                if v == target['lp_category']), None)
                                        if content_subtype is not None:
                                            target['sf_category'] = SF_CATEGORIES[file_type][content_subtype]
                                            target['sf_tag_prefix'] = SF_TAG_PREFIXES[file_type][content_subtype]
                                        break
                                elif LOOP_PAT.match(line):
                                    pass_sf_loop = True
                            elif sf_named_pattern.match(line):
                                pass_sf_framecode = True

                    targets.append(target)

                except AttributeError:
                    pass

            for target in targets:

                sf_framecode = target['sf_framecode']

                pass_sf_framecode = pass_sf_loop = False

                sf_named_pattern = re.compile(r'\s*save_' + sf_framecode + r'\s*')

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    for line in ifh:
                        if pass_sf_loop:
                            ofh.write(line)
                        elif pass_sf_framecode:
                            if LOOP_PAT.match(line):
                                pass_sf_loop = True
                                if 'sf_category' in target:
                                    ofh.write(target['sf_tag_prefix'] + '.' + ('sf_framecode' if file_type == 'nef' else 'Sf_framecode')
                                              + '   ' + sf_framecode + '\n')
                                    ofh.write(target['sf_tag_prefix'] + '.' + ('sf_category' if file_type == 'nef' else 'Sf_category')
                                              + '    ' + target['sf_category'] + '\n')
                                    ofh.write('#\n')
                                ofh.write(line)
                        elif sf_named_pattern.match(line):
                            pass_sf_framecode = True
                            ofh.write(line)
                        elif not pass_sf_framecode:
                            ofh.write(line)

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

        except StopIteration:
            pass

        msg_template = "You attempted to parse one loop but the source you provided had more than one loop. "\
            "Please either parse all loops as a saveframe or only parse one loop. Loops detected:"

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = 'Saveframe(s), instead of the datablock, must hook more than one loop. Loops detected:'\
                + msg[len(msg_template):].replace('<pynmrstar.', '').replace("'>", "'")

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            msg_pattern = re.compile(r'^' + msg_template + r" \[(.*)\]$")

            targets = []

            for msg in message['error']:

                if msg_template not in msg:
                    continue

                try:

                    g = msg_pattern.search(msg).groups()

                    for lp_obj in g[0].split(', '):

                        lp_category = str(PYNMRSTAR_LP_OBJ_PAT.search(lp_obj).groups()[0])

                        if lp_category == 'None':
                            continue

                        target = {'lp_category': lp_category}

                        pass_loop = False

                        lp_loc = -1
                        i = 0

                        with open(_srcPath, 'r', encoding='utf-8') as ifh:
                            for line in ifh:
                                if pass_loop:
                                    if CATEGORY_PAT.match(line):
                                        _lp_category = '_' + CATEGORY_PAT.search(line).groups()[0]
                                        if lp_category == _lp_category:
                                            target['loop_location'] = lp_loc
                                            content_subtype = next((k for k, v in LP_CATEGORIES[file_type].items()
                                                                    if v == target['lp_category']), None)
                                            if content_subtype is not None:
                                                target['sf_category'] = SF_CATEGORIES[file_type][content_subtype]
                                                target['sf_tag_prefix'] = SF_TAG_PREFIXES[file_type][content_subtype]
                                                target['sf_framecode'] = target['sf_category'] + '_1'
                                        pass_loop = False
                                elif LOOP_PAT.match(line):
                                    pass_loop = True
                                    lp_loc = i
                                elif STOP_PAT.match(line):
                                    if 'loop_location' in target and 'stop_location' not in target:
                                        target['stop_location'] = i
                                        break

                                i += 1

                        targets.append(target)

                except AttributeError:
                    pass

            if len(targets) > 0:
                target_loop_locations = [target['loop_location'] for target in targets]
                target_stop_locations = [target['stop_location'] for target in targets]
                ignored_loop_locations = []
                for target in targets:
                    if 'sf_category' not in target:
                        ignored_loop_locations.extend(list(range(target['loop_location'], target['stop_location'] + 1)))

                i = 0

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    ofh.write('data_' + os.path.basename(srcPath) + '\n\n')
                    for line in ifh:
                        if i in target_loop_locations:
                            target = next(target for target in targets if target['loop_location'] == i)
                            if 'sf_category' in target:
                                ofh.write('save_' + target['sf_framecode'] + '\n')
                                ofh.write(target['sf_tag_prefix'] + '.' + ('sf_framecode' if file_type == 'nef' else 'Sf_framecode')
                                          + '   ' + target['sf_framecode'] + '\n')
                                ofh.write(target['sf_tag_prefix'] + '.' + ('sf_category' if file_type == 'nef' else 'Sf_category')
                                          + '    ' + target['sf_category'] + '\n')
                                ofh.write('#\n')
                        if i not in ignored_loop_locations:
                            ofh.write(line)
                        if i in target_stop_locations:
                            target = next(target for target in targets if target['stop_location'] == i)
                            if 'sf_category' in target:
                                ofh.write('save_\n')

                        i += 1

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

        except StopIteration:
            pass

        msg_template = "One saveframe cannot have tags with different categories (or tags that don't match the set category)!"

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = msg

            _msg_template = r"One saveframe cannot have tags with different categories \(or tags that don't match the set category\)!"

            msg_pattern = re.compile(r'^' + _msg_template + r" '(.*)' vs '(.*)'.$")

            targets = []

            for msg in message['error']:

                if msg_template not in msg:
                    continue

                try:

                    target = {}

                    g = msg_pattern.search(msg).groups()

                    try:
                        category_1 = str(g[0])
                        category_2 = str(g[1])
                    except IndexError:
                        continue

                    target = {'category_1': category_1, 'category_2': category_2}

                    pass_sf_framecode = pass_category_1 = pass_category_2 = pass_sf_loop = False

                    i = 0

                    with open(_srcPath, 'r', encoding='utf-8') as ifh:
                        for line in ifh:
                            if pass_sf_framecode:
                                if SAVE_PAT.match(line):
                                    if 'category_1_begin' in target and 'category_2_begin' in target:
                                        targets.append(target)
                                        break
                                    pass_sf_framecode = pass_category_1 = pass_category_2 = pass_sf_loop = False
                                elif LOOP_PAT.match(line):
                                    pass_sf_loop = True
                                elif not pass_sf_loop:
                                    if CATEGORY_PAT.match(line):
                                        category = '_' + CATEGORY_PAT.search(line).groups()[0]
                                        if category == category_1:
                                            if not pass_category_1:
                                                target['category_1_begin'] = i
                                                content_subtype = next((k for k, v in SF_TAG_PREFIXES[file_type].items()
                                                                        if v == category), None)
                                                if content_subtype is not None:
                                                    target['content_subtype_1'] = content_subtype
                                                content_subtype = next((k for k, v in LP_CATEGORIES[file_type].items()
                                                                        if v == category), None)
                                                if content_subtype is not None:
                                                    target['content_subtype_1'] = content_subtype
                                            pass_category_1 = True
                                            target['category_1_end'] = i
                                        elif category == category_2 and pass_category_1:
                                            if not pass_category_2:
                                                target['category_2_begin'] = i
                                                content_subtype = next((k for k, v in SF_TAG_PREFIXES[file_type].items()
                                                                        if v == category), None)
                                                if content_subtype is not None:
                                                    target['category_type_2'] = 'saveframe'
                                                    target['content_subtype_2'] = content_subtype
                                                    target['sf_tag_prefix_2'] = SF_TAG_PREFIXES[file_type][content_subtype]
                                                    target['sf_category_2'] = SF_CATEGORIES[file_type][content_subtype]
                                                    target['sf_framecode_2'] = target['sf_category_2'] + '_1'
                                                content_subtype = next((k for k, v in LP_CATEGORIES[file_type].items()
                                                                        if v == category), None)
                                                if content_subtype is not None:
                                                    target['category_type_2'] = 'loop'
                                                    target['content_subtype_2'] = content_subtype
                                                    target['sf_tag_prefix_2'] = SF_TAG_PREFIXES[file_type][content_subtype]
                                                    target['sf_category_2'] = SF_CATEGORIES[file_type][content_subtype]
                                                    target['sf_framecode_2'] = target['sf_category_2'] + '_1'
                                                if 'category_type_2' not in target:
                                                    content_subtype = target['content_subtype_1']
                                                    target['category_type_2'] = 'loop'
                                                    target['content_subtype_2'] = content_subtype
                                            pass_category_2 = True
                                            target['category_2_end'] = i
                                elif LOOP_PAT.match(line):
                                    pass_sf_loop = True
                            elif SF_ANONYMOUS_PAT.match(line):
                                pass_sf_framecode = True
                                pass_category_1 = pass_category_2 = pass_sf_loop = False

                            i += 1

                except AttributeError:
                    pass

            if len(targets) > 0:

                self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                            {'file_name': file_name, 'description': warn})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

                target_category_begins = [target['category_2_begin'] for target in targets]
                target_category_ends = [target['category_2_end'] for target in targets]

                loop_category_locations = []
                for target in targets:
                    _range = list(range(target['category_2_begin'], target['category_2_end'] + 1))
                    if target['category_type_2'] == 'loop':
                        loop_category_locations.extend(_range)

                i = 0

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    for line in ifh:
                        if i in target_category_begins:
                            target = next(target for target in targets if target['category_2_begin'] == i)
                            if target['content_subtype_1'] != target['content_subtype_2']:
                                ofh.write('save_\n')
                                if target['category_type_2'] == 'saveframe':
                                    ofh.write('save_' + target['sf_framecode_2'] + '\n')
                                else:
                                    ofh.write('save_' + target['sf_framecode_2'] + '\n')
                                    ofh.write(target['sf_tag_prefix_2'] + '.' + ('sf_framecode' if file_type == 'nef' else 'Sf_framecode')
                                              + '   ' + target['sf_framecode_2'] + '\n')
                                    ofh.write(target['sf_tag_prefix_2'] + '.' + ('sf_category' if file_type == 'nef' else 'Sf_category')
                                              + '    ' + target['category_2'] + '\n')
                                    ofh.write('loop_\n')
                                    lp_tags = lp_vals = ''
                            elif target['category_type_2'] == 'loop':
                                ofh.write('loop_\n')
                                lp_tags = lp_vals = ''
                        if i not in loop_category_locations:
                            ofh.write(line)
                        else:
                            g = TAGVALUE_PAT.search(line).groups()
                            try:
                                lp_tags += f"_{g[0]}.{g[1]}\n"
                                lp_vals += f" {g[2].strip(' ')} "
                            except IndexError:
                                continue
                        if i in target_category_ends:
                            target = next(target for target in targets if target['category_2_end'] == i)
                            if target['content_subtype_1'] != target['content_subtype_2']:
                                if target['category_type_2'] == 'saveframe':
                                    pass
                                else:
                                    ofh.write(lp_tags)
                                    ofh.write(lp_vals.rstrip(' ') + '\n')
                                    ofh.write('stop_\n')
                            elif target['category_type_2'] == 'loop':
                                ofh.write(lp_tags)
                                ofh.write(lp_vals.rstrip(' ') + '\n')
                                ofh.write('stop_\n')

                        i += 1

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

        except StopIteration:
            pass

        msg_template = 'The Sf_framecode tag cannot be different from the saveframe name.'

        try:

            msg = next(msg for msg in message['error'] if msg_template in msg)
            warn = "Sf_framecode tag value should match with the saveframe name."

            self.__reg.report.warning.appendDescription('corrected_format_issue',
                                                        {'file_name': file_name, 'description': warn})

            if self.__reg.verbose:
                self.__reg.log.write(f"+{self.__class_name__}.__validateInputSource() ++ Warning  - {warn}\n")

            if __pynmrstar_v3_3__:
                msg_pattern = re.compile(r'^.*' + msg_template
                                         + r" Error occurred in tag _\S+ with value ([\S ]+) "
                                         r"which conflicts with the saveframe name (\S+)\. "
                                         r"Error detected on line (\d+).*$")
            else:
                msg_pattern = re.compile(r'^.*' + msg_template
                                         + r" Error occurred in tag _\S+ with value ([\S ]+) "
                                         r"which conflicts with.* the saveframe name (\S+)\. "
                                         r"Error detected on line (\d+).*$")

            try:

                g = msg_pattern.search(msg).groups()

                sf_framecode = g[0]
                saveframe_name = g[1]
                line_num = int(g[2])

                i = 0

                with open(_srcPath, 'r', encoding='utf-8') as ifh, \
                        open(_srcPath + '~', 'w', encoding='utf-8') as ofh:
                    for line in ifh:
                        if i == line_num:
                            if sf_framecode not in EMPTY_VALUE:
                                ofh.write(re.sub(r'["\']?' + sf_framecode + r'["\']?\s*$', saveframe_name + r'\n', line))
                            else:
                                ofh.write(re.sub(rf'\{sf_framecode}\s*$', saveframe_name + r'\n', line))
                        else:
                            ofh.write(line)
                        i += 1

                    _srcPath = ofh.name
                    tmpPaths.append(_srcPath)

            except AttributeError:
                pass

        except StopIteration:
            pass

        if len(tmpPaths) > len_tmp_paths:

            is_valid, _message = self.__reg.nefT.validate_file(_srcPath, fileSubType, allowEmpty)

            if not is_valid:

                retry = len(message['error']) != len(_message['error']) or message['error'] != _message['error']

                if not retry:

                    for msg, _msg in zip(message['error'], _message['error']):
                        if msg != _msg:
                            retry = True
                            break

                if retry and len_tmp_paths < 40:
                    return self.fixFormatIssueOfInputSource(file_list_id, file_name, file_type, _srcPath, fileSubType,
                                                            _message, tmpPaths, allowEmpty, hasLegacySfIssue)

        is_done = True

        is_valid, message = self.__reg.nefT.validate_file(_srcPath, fileSubType, allowEmpty)

        _file_type = message['file_type']  # nef/nmr-star/unknown

        if not self.__reg.combined_mode:

            if file_list_id < self.__reg.cs_file_path_list_len:

                if CS_FILE_PATH_LIST_KEY in self.__reg.outputParamDict:
                    if file_list_id < len(self.__reg.outputParamDict[CS_FILE_PATH_LIST_KEY]):
                        dstPath = self.__reg.outputParamDict[CS_FILE_PATH_LIST_KEY][file_list_id]
                        if dstPath is not None and dstPath not in self.__reg.inputParamDict[CS_FILE_PATH_LIST_KEY]:
                            shutil.copyfile(_srcPath, dstPath)

            else:

                if MR_FILE_PATH_LIST_KEY in self.__reg.outputParamDict:
                    if file_list_id - self.__reg.cs_file_path_list_len < len(self.__reg.outputParamDict[MR_FILE_PATH_LIST_KEY]):
                        dstPath = self.__reg.outputParamDict[MR_FILE_PATH_LIST_KEY][file_list_id - self.__reg.cs_file_path_list_len]
                        if dstPath is not None and dstPath not in self.__reg.inputParamDict[MR_FILE_PATH_LIST_KEY]:
                            shutil.copyfile(_srcPath, dstPath)

        if is_valid:

            if _file_type != file_type:

                err = f"{file_name!r} was selected as {READABLE_FILE_TYPE[file_type]} file, "\
                    f"but recognized as {READABLE_FILE_TYPE[_file_type]} file. Please re-upload the file."

                if len(message['error']) > 0:
                    for err_message in message['error']:
                        if 'No such file or directory' not in err_message:
                            err += ' ' + re.sub('not in list', 'unknown item.', err_message)

                self.__reg.report.error.appendDescription('content_mismatch',
                                                          {'file_name': file_name, 'description': err})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Error  - {err}\n")

            else:

                # NEFTranslator.validate_file() generates this object internally, but not re-used.
                is_done, star_data_type, star_data = self.__reg.nefT.read_input_file(_srcPath)

                rescued = hasLegacySfIssue and is_done and star_data_type == 'Entry'

                if len(self.__reg.star_data_type) > file_list_id:
                    self.__reg.star_data_type[file_list_id] = star_data_type
                    self.__reg.star_data[file_list_id] = star_data
                else:
                    self.__reg.star_data_type.append(star_data_type)
                    self.__reg.star_data.append(star_data)

                self.rescueFormerNef(file_list_id)
                self.rescueImmatureStr(file_list_id)

                if rescued:
                    if ONEDEP_ANY_UPLOAD_FILE_NAME_PAT.match(srcPath):
                        g = ONEDEP_ANY_UPLOAD_FILE_NAME_PAT.search(srcPath).groups()
                        srcPath = g[0] + '-upload-convert_' + g[1] + '.V' + g[2]
                    else:
                        if ONEDEP_ANY_FILE_NAME_PAT.match(srcPath):
                            g = ONEDEP_ANY_FILE_NAME_PAT.search(srcPath).groups()
                            srcPath = g[0] + '.V' + str(int(g[1]) + 1)

                    self.__reg.star_data[file_list_id].write_to_file(srcPath,
                                                                     show_comments=False, skip_empty_loops=True, skip_empty_tags=False)

        else:

            missing_loop = True

            err = f"{file_name!r} is not compliant with the {READABLE_FILE_TYPE[file_type]} dictionary."

            if len(message['error']) > 0:

                if any(True for err_message in message['error'] if 'The mandatory loop' in err_message):

                    err = ''
                    for err_message in message['error']:
                        if 'No such file or directory' not in err_message:
                            err += re.sub('not in list', 'unknown item.', err_message) + ' '
                    err = err[:-1]

                else:
                    missing_loop = False

                    for err_message in self.__reg.original_error_message[file_list_id]['error']:
                        if 'No such file or directory' not in err_message:
                            err += ' ' + re.sub('not in list', 'unknown item.', err_message)

            if not self.__reg.remediation_mode or not missing_loop or file_list_id > 0:

                self.__reg.report.error.appendDescription('missing_mandatory_content' if missing_loop else 'format_issue',
                                                          {'file_name': file_name, 'description': err})

                self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Error  - "
                                     f"{file_name} {err}\n")

                is_done = False

            else:

                self.__reg.has_star_chem_shift = False

                self.__reg.suspended_errors_for_lazy_eval.append({'missing_mandatory_content':
                                                                  {'file_name': file_name, 'description': err}})

                if self.__reg.verbose:
                    self.__reg.log.write(f"+{self.__class_name__}.fixFormatIssueOfInputSource() ++ Error  - {err}\n")

        try:

            if self.__reg.release_mode and len(tmpPaths) > 0:
                self.__reg.srcPath = tmpPaths[-1]
                for tmpPath in tmpPaths[:-1]:
                    if os.path.exists(tmpPath):
                        os.remove(tmpPath)
            else:
                for tmpPath in tmpPaths:
                    if os.path.exists(tmpPath):
                        os.remove(tmpPath)

        except OSError:
            pass

        return is_done

    def rescueFormerNef(self, file_list_id: int) -> bool:
        """ Rescue former NEF version prior to 1.0.
        """

        input_source = self.__reg.report.input_sources[file_list_id]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']
        file_type = input_source_dic['file_type']

        if file_type != 'nef' or file_list_id >= len(self.__reg.star_data) or self.__reg.star_data[file_list_id] is None:
            return True

        if self.__reg.combined_mode or self.__reg.star_data_type[file_list_id] == 'Entry':

            for content_subtype in NMR_CONTENT_SUBTYPES:

                sf_category = SF_CATEGORIES[file_type][content_subtype]

                if sf_category is None:
                    continue

                for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):
                    sf_framecode = get_first_sf_tag(sf, 'sf_framecode')

                    if self.getSaveframeByName(file_list_id, sf_framecode) is None:

                        itName = '_' + sf_category + '.sf_framecode'

                        if self.__reg.resolve_conflict:
                            warn = f"{itName} {sf_framecode!r} should be matched "\
                                f"with saveframe name {sf.name!r}. {itName} will be overwritten."

                            self.__reg.report.warning.appendDescription('missing_saveframe',
                                                                        {'file_name': file_name, 'sf_framecode': sf.name,
                                                                         'description': warn})

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.rescueFormerNef() ++ Warning  - {warn}\n")

                            set_sf_tag(sf, 'sf_framecode', sf.name)

                        else:
                            err = f"{itName} {sf_framecode!r} must be matched with saveframe name {sf.name!r}."

                            self.__reg.report.error.appendDescription('format_issue',
                                                                      {'file_name': file_name, 'sf_framecode': sf.name,
                                                                       'description': err})

                            self.__reg.log.write(f"+{self.__class_name__}.rescueFormerNef() ++ Error  - "
                                                 f"{file_name} {sf.name} {err}\n")

        if not self.__reg.rescue_mode:
            return True

        if self.__reg.combined_mode or self.__reg.star_data_type[file_list_id] == 'Entry':

            content_subtype = 'entry_info'

            sf_category = SF_CATEGORIES[file_type][content_subtype]

            for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):
                format_version = get_first_sf_tag(sf, 'format_version')

                if not format_version.startswith('0.'):
                    sf.format_version = NEF_VERSION

            for content_subtype in NMR_CONTENT_SUBTYPES:

                sf_category = SF_CATEGORIES[file_type][content_subtype]
                lp_category = LP_CATEGORIES[file_type][content_subtype]

                if None in (sf_category, lp_category):
                    continue

                for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):
                    sf_framecode = get_first_sf_tag(sf, 'sf_framecode')

                    if not any(True for loop in sf.loops if loop.category == lp_category):
                        continue

                    self.__rescueFormerNef__(file_name, file_type, content_subtype, sf, sf_framecode, sf_category, lp_category)

            return True

        self.__reg.sf_category_list, self.__reg.lp_category_list = self.__reg.nefT.get_inventory_list(self.__reg.star_data[file_list_id])

        # initialize loop counter
        lp_counts = {t: 0 for t in NMR_CONTENT_SUBTYPES}

        # increment loop counter of each content subtype
        for lp_category in self.__reg.lp_category_list:
            if lp_category in LP_CATEGORIES[file_type].values():
                lp_counts[[k for k, v in LP_CATEGORIES[file_type].items() if v == lp_category][0]] += 1

        content_subtypes = {k: lp_counts[k] for k in lp_counts if lp_counts[k] > 0}

        for content_subtype in NMR_CONTENT_SUBTYPES:

            sf_category = SF_CATEGORIES[file_type][content_subtype]
            lp_category = LP_CATEGORIES[file_type][content_subtype]

            if None in (sf_category, lp_category):
                continue

            if self.__reg.star_data_type[file_list_id] == 'Loop':

                if content_subtype not in content_subtypes:
                    continue

                sf = self.__reg.star_data[file_list_id]
                sf_framecode = ''

                self.__rescueFormerNef__(file_name, file_type, content_subtype, sf, sf_framecode, sf_category, lp_category)

            else:

                if content_subtype not in content_subtypes:
                    continue

                sf = self.__reg.star_data[file_list_id]
                sf_framecode = get_first_sf_tag(sf, 'sf_framecode')

                self.__rescueFormerNef__(file_name, file_type, content_subtype, sf, sf_framecode, sf_category, lp_category)

        return True

    def __rescueFormerNef__(self, file_name: str, file_type: str, content_subtype: str,
                            sf: Union[pynmrstar.Entry, pynmrstar.Saveframe, pynmrstar.Loop],
                            sf_framecode: str, sf_category: str, lp_category: str):
        """ Rescue former NEF version prior to 1.0.
        """

        if isinstance(sf, pynmrstar.Loop):
            loop = sf
        else:
            loop = sf.get_loop(lp_category)

        try:

            index_tag = INDEX_TAGS[file_type][content_subtype]

            if index_tag is not None:

                try:
                    tag_pos = next(loop.tags.index(tag) for tag in loop.tags if tag == 'ordinal')
                    loop.tags[tag_pos] = 'index'
                except StopIteration:
                    pass

                try:
                    tag_pos = next(loop.tags.index(tag) for tag in loop.tags if tag == 'index_id')
                    loop.tags[tag_pos] = 'index'
                except StopIteration:
                    pass

            if content_subtype == 'poly_seq':

                try:
                    tag_pos = next(loop.tags.index(tag) for tag in loop.tags if tag == 'residue_type')
                    loop.tags[tag_pos] = 'residue_name'
                except StopIteration:
                    pass

                if 'index' not in loop.tags:

                    lp_tag = lp_category + '.index'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueFormerNef() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        for idx, row in enumerate(loop, start=1):
                            row.append(idx)

                        loop.add_tag(lp_category + '.index')

                    except ValueError:
                        pass

            elif content_subtype == 'chem_shift':

                if any(True for tag in sf.tags if tag[0] == 'atom_chemical_shift_units'):
                    sf.remove_tag('atom_chemical_shift_units')

                try:
                    tag_pos = next(loop.tags.index(tag) for tag in loop.tags if tag == 'residue_type')
                    loop.tags[tag_pos] = 'residue_name'
                except StopIteration:
                    pass

                if 'element' not in loop.tags:

                    lp_tag = lp_category + '.element'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueFormerNef() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        atom_name_col = loop.tags.index('atom_name')

                        for row in loop:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row.append(atom_type)

                        loop.add_tag(lp_category + '.element')

                    except ValueError:
                        pass

                elif not self.__reg.combined_mode:

                    atom_type_col = loop.tags.index('element')
                    atom_name_col = loop.tags.index('atom_name')

                    for row in loop:
                        if row[atom_type_col] in EMPTY_VALUE:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row[atom_type_col] = atom_type

                if 'isotope_number' not in loop.tags:

                    lp_tag = lp_category + '.isotope_number'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueFormerNef() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        atom_name_col = loop.tags.index('atom_name')

                        for row in loop:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row.append(str(ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[atom_type][0]))

                        loop.add_tag(lp_category + '.isotope_number')

                    except ValueError:
                        pass

                elif not self.__reg.combined_mode:

                    iso_num_col = loop.tags.index('isotope_number')
                    atom_name_col = loop.tags.index('atom_name')

                    for row in loop:
                        if row[iso_num_col] in EMPTY_VALUE:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row[iso_num_col] = str(ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[atom_type][0])

            elif content_subtype == 'dihed_restraint':

                if 'name' not in loop.tags:

                    lp_tag = lp_category + '.name'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueFormerNef() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        loop.add_tag(lp_category + '.name', update_data=True)

                    except ValueError:
                        pass

            elif content_subtype == 'rdc_restraint':

                try:

                    tag = next(tag for tag in sf.tags if tag[0] == 'tensor_residue_type')
                    sf.add_tag(sf_category + '.tensor_residue_name', tag[1])
                    sf.remove_tag('tensor_residue_type')

                except StopIteration:
                    pass
                except ValueError:
                    pass

            if content_subtype in ('dist_restraint', 'rdc_restraint'):
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

            else:
                return

            for j in range(1, max_dim):

                _residue_type = 'residue_type_' + str(j)

                try:
                    tag_pos = next(loop.tags.index(tag) for tag in loop.tags if tag == _residue_type)
                    loop.tags[tag_pos] = 'residue_name_' + str(j)
                except StopIteration:
                    pass

        except KeyError:
            pass

    def rescueImmatureStr(self, file_list_id: int) -> bool:
        """ Rescue immature NMR-STAR.
        """

        input_source = self.__reg.report.input_sources[file_list_id]
        input_source_dic = input_source.get()

        file_name = input_source_dic['file_name']
        file_type = input_source_dic['file_type']

        if file_type != 'nmr-star' or file_list_id >= len(self.__reg.star_data) or self.__reg.star_data[file_list_id] is None:
            return True

        if self.__reg.combined_mode or self.__reg.star_data_type[file_list_id] == 'Entry':

            for content_subtype in NMR_CONTENT_SUBTYPES:

                if content_subtype == 'entry_info':
                    continue

                sf_category = SF_CATEGORIES[file_type][content_subtype]

                if sf_category is None:
                    continue

                for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):
                    sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                    if self.getSaveframeByName(file_list_id, sf_framecode) is None:

                        itName = '_' + sf_category + '.Sf_framecode'

                        if self.__reg.resolve_conflict:
                            warn = f"{itName} {sf_framecode!r} should be matched "\
                                f"with saveframe name {sf.name!r}. {itName} will be overwritten."

                            self.__reg.report.warning.appendDescription('missing_saveframe',
                                                                        {'file_name': file_name, 'sf_framecode': sf.name,
                                                                         'description': warn})

                            if self.__reg.verbose:
                                self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ Warning  - {warn}\n")

                            tagNames = [t[0] for t in sf.tags]

                            if 'Sf_framecode' in tagNames:
                                set_sf_tag(sf, 'Sf_framecode', sf.name)
                            elif 'sf_framecode' in tagNames:
                                set_sf_tag(sf, 'sf_framecode', sf.name)

                        else:
                            err = f"{itName} {sf_framecode!r} must be matched with saveframe name {sf.name!r}."

                            self.__reg.report.error.appendDescription('format_issue',
                                                                      {'file_name': file_name, 'sf_framecode': sf.name,
                                                                       'description': err})

                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ Error  - "
                                                 f"{file_name} {sf.name} {err}\n")

        if not self.__reg.rescue_mode:
            return True

        self.__reg.sf_category_list, self.__reg.lp_category_list = self.__reg.nefT.get_inventory_list(self.__reg.star_data[file_list_id])

        # initialize loop counter
        lp_counts = {t: 0 for t in NMR_CONTENT_SUBTYPES}

        # increment loop counter of each content subtype
        for lp_category in self.__reg.lp_category_list:
            if lp_category in LP_CATEGORIES[file_type].values():
                lp_counts[[k for k, v in LP_CATEGORIES[file_type].items() if v == lp_category][0]] += 1

        content_subtypes = {k: lp_counts[k] for k in lp_counts if lp_counts[k] > 0}

        for content_subtype in NMR_CONTENT_SUBTYPES:

            sf_category = SF_CATEGORIES[file_type][content_subtype]
            lp_category = LP_CATEGORIES[file_type][content_subtype]

            if content_subtype.startswith('spectral_peak'):
                lp_category = AUX_LP_CATEGORIES[file_type][content_subtype][0]  # _Spectral_dim

            if None in (sf_category, lp_category):
                continue

            if self.__reg.star_data_type[file_list_id] == 'Loop':

                if content_subtype not in content_subtypes:
                    continue

                sf = self.__reg.star_data[file_list_id]
                sf_framecode = ''

                self.__rescueImmatureStr__(file_name, file_type, content_subtype, sf, sf_framecode, lp_category)

            elif self.__reg.star_data_type[file_list_id] == 'Saveframe':

                if content_subtype not in content_subtypes:
                    continue

                sf = self.__reg.star_data[file_list_id]
                sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                self.__rescueImmatureStr__(file_name, file_type, content_subtype, sf, sf_framecode, lp_category)

            else:

                for sf in self.__reg.star_data[file_list_id].get_saveframes_by_category(sf_category):
                    sf_framecode = get_first_sf_tag(sf, 'Sf_framecode')

                    if not any(True for loop in sf.loops if loop.category == lp_category):
                        continue

                    self.__rescueImmatureStr__(file_name, file_type, content_subtype, sf, sf_framecode, lp_category)

        return True

    def __rescueImmatureStr__(self, file_name: str, file_type: str, content_subtype: str,
                              sf: Union[pynmrstar.Entry, pynmrstar.Saveframe, pynmrstar.Loop],
                              sf_framecode: str, lp_category: str):
        """ Rescue immature NMR-STAR.
        """

        if isinstance(sf, pynmrstar.Loop):
            loop = sf
        else:
            loop = sf.get_loop(lp_category)

        try:

            if content_subtype == 'chem_shift':

                if 'Atom_type' not in loop.tags:

                    lp_tag = lp_category + '.Atom_type'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        atom_name_col = loop.tags.index('Atom_ID')

                        for row in loop:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row.append(atom_type)

                        loop.add_tag(lp_category + '.Atom_type')

                    except ValueError:
                        pass

                elif not self.__reg.combined_mode:

                    atom_type_col = loop.tags.index('Atom_type')
                    atom_name_col = loop.tags.index('Atom_ID')

                    for row in loop:
                        if row[atom_type_col] in EMPTY_VALUE:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row[atom_type_col] = atom_type

                if 'Atom_isotope_number' not in loop.tags:

                    lp_tag = lp_category + '.Atom_isotope_number'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        atom_name_col = loop.tags.index('Atom_ID')

                        for row in loop:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row.append(str(ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[atom_type][0]))

                        loop.add_tag(lp_category + '.Atom_isotope_number')

                    except ValueError:
                        pass

                elif not self.__reg.combined_mode:

                    iso_num_col = loop.tags.index('Atom_isotope_number')
                    atom_name_col = loop.tags.index('Atom_ID')

                    for row in loop:
                        if row[iso_num_col] in EMPTY_VALUE:
                            atom_type = row[atom_name_col][0]
                            if atom_type in ('Q', 'M'):
                                atom_type = 'H'
                            row[iso_num_col] = str(ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[atom_type][0])

            elif content_subtype == 'dist_restraint':  # backward compatibility

                original_items = ['Original_PDB_strand_ID', 'Original_PDB_residue_no', 'Original_PDB_residue_name']

                for i in range(1, 3):
                    for original_item in original_items:
                        tag = original_item + '_' + str(i)
                        if tag in loop.tags:
                            loop.remove_tag(tag)

                    tag = 'Original_PDB_atom_name_' + str(i)
                    if tag in loop.tags:

                        _tag = 'Auth_atom_name_' + str(i)
                        if _tag not in loop.tags:
                            _dat = loop.get_tag([tag])

                            for idx, row in enumerate(loop):
                                row.append(_dat[idx])

                            loop.add_tag(_tag)

                        loop.remove_tag(tag)

            elif content_subtype == 'dihed_restraint':

                if 'Torsion_angle_name' not in loop.tags:

                    lp_tag = lp_category + '.Torsion_angle_name'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        loop.add_tag(lp_category + '.Torsion_angle_name', update_data=True)

                    except ValueError:
                        pass

            elif content_subtype.startswith('spectral_peak'):

                if 'Atom_type' not in loop.tags:

                    lp_tag = lp_category + '.Atom_type'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        axis_code_name_col = loop.tags.index('Axis_code')

                        for row in loop:
                            atom_type = re.sub(r'\d+', '', row[axis_code_name_col])
                            row.append(atom_type)

                        loop.add_tag(lp_category + '.Atom_type')

                    except ValueError:
                        pass

                if 'Atom_isotope_number' not in loop.tags:

                    lp_tag = lp_category + '.Atom_isotope_number'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        axis_code_name_col = loop.tags.index('Axis_code')

                        for row in loop:
                            atom_type = re.sub(r'\d+', '', row[axis_code_name_col])
                            row.append(str(ISOTOPE_NUMBERS_OF_NMR_OBS_NUCS[atom_type][0]))

                        loop.add_tag(lp_category + '.Atom_isotope_number')

                    except ValueError:
                        pass

                if 'Axis_code' not in loop.tags:

                    lp_tag = lp_category + '.Axis_code'
                    err = ERR_TEMPLATE_FOR_MISSING_MANDATORY_LP_TAG % (lp_tag, file_type.upper())

                    if self.__reg.check_mandatory_tag and self.__reg.nefT.is_mandatory_tag(lp_tag, file_type):
                        self.__reg.report.error.appendDescription('missing_mandatory_item',
                                                                  {'file_name': file_name, 'sf_framecode': sf_framecode,
                                                                   'category': lp_category, 'description': err})

                        if self.__reg.verbose:
                            self.__reg.log.write(f"+{self.__class_name__}.rescueImmatureStr() ++ LookupError  - "
                                                 f"{file_name} {sf_framecode} {lp_category} {err}\n")

                    try:

                        atom_type_name_col = loop.tags.index('Atom_type')
                        iso_num_name_col = loop.tags.index('Atom_isotope_number')

                        for row in loop:
                            atom_type = row[atom_type_name_col]
                            iso_num = row[iso_num_name_col]
                            row.append(iso_num + atom_type)

                        loop.add_tag(lp_category + '.Axis_code')

                    except ValueError:
                        pass

                # _Spectral_dim.Encoded_source_dimension_ID should be _Spectral_dim.Encoded_reduced_dimension_ID
                if 'Encoded_source_dimension_ID' in loop.tags:
                    if 'Encoded_reduced_dimension_ID' in loop.tags:
                        loop.remove_tag('Encoded_source_dimension_ID')
                    else:
                        col = loop.tags.index('Encoded_source_dimension_ID')
                        loop.tags[col] = 'Encoded_reduced_dimension_ID'

        except KeyError:
            pass

    def getSaveframeByName(self, file_list_id: int, sf_framecode: str) -> Optional[pynmrstar.Saveframe]:
        """ Retrieve saveframe content from a given name.
        """

        try:

            return self.__reg.star_data[file_list_id].get_saveframe_by_name(sf_framecode)

        except KeyError:  # DAOTHER-7389, issue #4

            if file_list_id < len(self.__reg.sf_name_corrections) and sf_framecode in self.__reg.sf_name_corrections[file_list_id]:

                try:
                    return self.__reg.star_data[file_list_id].get_saveframe_by_name(self.__reg.sf_name_corrections[file_list_id][sf_framecode])  # noqa: E501, pylint:disable=line-too-long
                except KeyError:
                    return None

            else:

                # pattern for guessing original saveframe name DAOTHER-7389, issue #4
                chk_unresolved_sf_name_pattern = re.compile(r'^(.*)_\d+$')

                try:
                    g = chk_unresolved_sf_name_pattern.search(sf_framecode).groups()
                    return self.__reg.star_data[file_list_id].get_saveframe_by_name(g[0])
                except AttributeError:
                    return None
                except KeyError:
                    return None
