"""
Development utilities for quick & easy handling of regular tasks.
"""
import os
import re
import csv
import time
import shutil
import numpy as np
import inspect
import datetime as dt
import importlib

from zdev.core import fileparts, merge_items
from zdev.indexing import file_goto
from zdev.validio import valid_encoding
from zdev.searchstr import S_IDENT_W_DOT_HYP, S_DOC_STR_QUOTES


# EXPORTED DATA
DEP_FILE_TYPES = ('.py', '.pyw') # file types to include for dependency search
DEP_PKG_TYPES = ('builtin', 'known', 'user')  # categories for sorting dependencies
DEP_PKG_BUILTIN = [ # definition of "builtin" packages -> sorted acc. to # chars
    'io', 'os', 're',
    'csv', 'sys',
    'json', 'math', 'stat', 'time', 'uuid',
    #5
    'base64', 'ctypes', 'pickle', 'pprint', 'shutil', 'typing',
    'asyncio', 'inspect', 'logging', 'zipfile',
    'datetime', 'requests', 'winsound',
    'functools', 'importlib', 'itertools', 'threading',    
    'concurrent', 'statistics', 'subprocess', 
    #11
    'configparser',
    #12, #13, #14,
    'multiprocessing',
    #16
    #specials:
    '__future__'
    ]
DEP_PKG_KNOWN = [ # definition of "known" packages -> sorted acc. to # chars
    #2
    'PIL', # pip -> pillow
    'dash', 'h5py',
    'flask', 'numpy', 'pydub', 'PyQt5', 'scipy', 'typer',
    'pandas', 'plotly', 'psutil',
    'pyarrow', 'skimage', # pip -> scikit-image
    'openpyxl', 'psycopg2', 'pydantic', 'tifffile', 
    'soundfile', 'streamlit',
    'matplotlib',
    'sounddevice',
    #12 #13 #14
    'influxdb_client',
    #16
    ]

# INTERNAL PARAMETERS & DEFAULTS
_DEP_REQ_FILE = 'requirements.txt'
_DEP_ANALYSIS_FILE = 'requirements_analysis.txt'
_RX_IMPORT = re.compile(r'(?P<tag>import )(?P<module>'+S_IDENT_W_DOT_HYP+r')')
_RX_IMPORT_FROM = re.compile(r'(?P<tag1>from )(?P<module>'+S_IDENT_W_DOT_HYP+r')(?P<tag2> import )')
_RX_WHITESPACE = re.compile(r'\s*')
_RX_QUOTES = re.compile(r'["\']')


def show_time(t_slow, t_fast, labels=['slow','fast'], show_factor=True, indent=None):
    """ Compares two processing durations (e.g. 'slow' Python vs. 'fast' C implementation). """

    # compute metrics
    speed_fac = t_slow / t_fast
    gain = 100.0 * (speed_fac-1.0)

    # configure formatting
    L = max([len(labels[0]), len(labels[1])])
    if (indent is not None):
        shift = " "*int(indent)
    else:
        shift = ""
    if (not show_factor):
        if (gain >= 0.0):
            qualifier = "faster"
        else:
            qualifier = "slower"

    # print comparison (speed factor or gain in %)
    if (indent is None):
        print("-"*64)
    print(f"{shift}{labels[0]:{L}} ~ {t_slow:.3e} sec")
    if (show_factor):
        print(f"{shift}{labels[1]:{L}} ~ {t_fast:.3e} sec  ==> speed factor ~ {speed_fac:.2f}")
    else:
        print(f"{shift}{labels[1]:{L}} ~ {t_fast:.3e} sec  ==> {qualifier} by {gain:.0f}%")
    if (indent is None):
        print("-"*64)

    return


def storage_size(payload, num_days=1, downsample=0):
    """ Computes required number of bytes to store 'payload' for a given reference interval.

    The "payload" structure may refer to a set of monitoring data for CBM (condition-based
    maintenance) purposes and is given as dict indicating the number of recorded signals for
    each data type and acquisition rate. In addition, a 'downsample' step can be specified to
    move all signals from their original rate by this amount of intervals w/ lower acquisition
    rate. In this way, a less densly-sampled or aggregated data set (e.g. for more "historic"
    phasess in the past) can be modeled & computed.

    Args:
        payload (dict): Payload of different data types, sampled at different rates.
            Available rates are 'ms'|'sec'|'min'|'hour'|'day'.
            Available dtypes are 'bit'|'byte'|'short'|'int'|'float'|'long'|'double'.
        num_days (int, optional): Reference interval for computations. Defaults to 1 day.
        downsample (int, optional): If desired, specifies the number of sampling intervals to
            shift data acquisition frequency (for all entries). Defaults to 0.

    Returns:
        num_bytes (int): Total number of bytes required for 'payload' within 'num_days'.

    Examples: The following illustrates the computation for a given payload. If desired, the
        result may be converted to a string by using "filesize_str(num_bytes, binary=True)".

        payload = { 'byte':  {'sec': 75, 'min': 250, 'hour': 2000},
                    'int':   {'min': 150, 'hour': 800},
                    'double': {'min': 30, 'hour': 200, 'day': 500} }

        (default, per day)       --> num_bytes =   8216800 ~ 7.84 MiB
        (default, per year)     --> num_bytes = 2999132000 ~ 2.79 GiB
        (downsample=1, per day)  --> num_bytes =    144960 ~ 141.56 KiB
        (downsample=1, per month) --> num_bytes =  52910400 ~ 4.15 MiB

        Note: Since the daily rates for the 'double' data could not be further reduced, the
        latter two examples correspond to the following modified payload:

        payload_downsampled = { 'byte':  {'min': 75, 'hour': 250, 'day': 2000},
                                'int':   {'hour': 150, 'day': 800},
                                'double': {'hour': 30, 'day': 700} }
    """

    # internal settings (all values refer to a daily perspective)
    _RATE = {
        'ms':   1000*60*60*24,
        'sec':  60*60*24,
        'min':  60*24,
        'hour': 24,
        'day':   1 
    }
    _TIMEBASE = list(_RATE.keys())
    _SIZEOF = { 
        'bit': (1/8),
        'byte': 1,
        'short': 2,
        'int': 4,
        'long': 8,
        'float': 4,
        'double': 8
    }
    # Note: A 'bit' is treated separately since it can be "stacked" (i.e. 1 byte = 8 bits)!

    # parse payload & compute daily storage
    all_data = 0
    for dtype in payload.keys():

        for rate in payload[dtype].keys():
            if (payload[dtype][rate] == 0): # ignore/skip empty fields
                continue

            # reduce frequency of data acquisition?
            aq = rate
            if (downsample):
                 idx = _TIMEBASE.index(rate) + downsample
                 if (idx < len(_TIMEBASE)):
                     aq = _TIMEBASE[idx]
                 else:
                     print(f"Warning: Could NOT reduce rate for data '{dtype}' @ '{rate}' (keeping original)")

            # compute storage
            if (dtype == 'bit'):
                req = np.ceil(payload[dtype][rate]*_SIZEOF['bit']) * _SIZEOF['byte'] * _RATE[aq]
            else:
                req = payload[dtype][rate] * _SIZEOF[dtype] * _RATE[aq]
            all_data += req

    # scale to reference interval
    num_bytes = all_data * num_days

    return num_bytes


def csv_splitter(path, sub_folders=None, split_lines=int(5e5), delete_orig=True, verbose=True):
    """ Parses all 'sub_folders' in 'path' for CSV-files and creates single files (if required).

    This helper may be used in order to make CSV-files created as database dumps more "usable",
    since text editors usually have a size limit for working w/ large files.

    Args:
        path (str): Location of main folder, i.e. where to start the search for CSV-files.
        sub_folders (list of str): Names of all sub-folders to search for CSV-files. Defaults to
            'None', i.e. all subfolders will be traversed.
        split_lines (int, optional): Number of lines after which the CSV-files will be split
            into "parts" , i.e. separate CSV-files with endings "_ptN.csv" (where N indicates a
            running index). Defaults to 500000.
        delete_orig (bool, optional): Switch to remove original (large) CSV-file after
            successful spliting. Defaults to 'True'.
        verbose (bool optional): Switch to show progress information on traversed folders/files.
            Defaults to 'True'.

    Returns:
        --
    """
    back = os.getcwd()
    os.chdir(path)

    # collect available subfolders
    if (sub_folders is None):
        sub_folders = []
        for item in os.listdir(os.getcwd()):
            if (os.path.isdir(item)):
                sub_folders.append(item)

    print(sub_folders)
    print(path)

    # parse all folders
    for sub in sub_folders:
        path_sub = os.path.join(path, sub)
        print(path_sub)
        if (not os.path.isdir(path_sub)):
            continue # skip non-existing folders
        elif (verbose):
            print(f"o Sub-folder '{sub}'")

        # parse all files
        for fname in os.listdir(path_sub):
            if ((not fname.endswith('csv')) or (re.search('_pt[0-9]*.csv', fname) is not None)):
                continue # skip non-CSV files or files that have already been split
            else:
                if (verbose):
                    print(f"  - File: '{fname}'")
                csv_file = os.path.join(path_sub, fname)
                enc = valid_encoding(csv_file)

                # read CSV-file in proper encoding
                with open(csv_file, mode='r', encoding=enc) as tf:

                    # parse format & configuration
                    first_line = tf.readline()
                    tf_format = csv.Sniffer().sniff(first_line)
                    fields = first_line.split(tf_format.delimiter)
                    for n, item in enumerate(fields):
                        fields[n] = item.strip() # clean whitespaces (incl. newline)

                    # if (num_header_lines > 2): #todo: have this as another argument?
                    #     #
                    #     #todo: get also "second_line = tf.readline()"
                    #     #         --> see "ts_import_csv" with "meta = xtools"

                    # create header line
                    line_header = ''
                    for item in fields:
                        line_header += f'{item}{tf_format.delimiter}'
                    line_header = line_header[:-1]+'\n'

                    # copy data of all time-series from file...
                    lines_for_next_split = []
                    num_lines, num_splits = 0, 0
                    m = 1
                    while (True):
                        try:
                            line = tf.readline()
                            if (line == ''): # regular break condition
                                raise

                            # export split file?
                            lines_for_next_split.append(line)
                            if (m == split_lines):
                                num_lines += m
                                num_splits += 1
                                with open(os.path.abspath(csv_file[:-4]+f'_pt{num_splits}.csv'), mode='wt') as sf:
                                    sf.write(line_header)
                                    sf.writelines(lines_for_next_split)
                                # reset
                                lines_for_next_split = []
                                m = 1
                            else:
                                m += 1
                        except:
                            break

                    # write last file (w/ remaining lines)
                    if (num_splits):
                        num_splits += 1
                        with open(os.path.abspath(csv_file[:-4]+f'_pt{num_splits}.csv'), mode='wt') as sf:
                            sf.write(line_header)
                            sf.writelines(lines_for_next_split)
                        if (verbose):
                            print(f"    (split into {num_splits} files)")
                    else:
                        if (verbose):
                            print(f"    (no split necessary, only {m} lines)")

                # remove original file? (only in case of splitting!)
                if ((num_splits >= 1) and delete_orig):
                     os.remove(csv_file)

    return


def file_clear_strings(text_file, symbol='"', verbose=True):
    """ Clear all strings in all lines of 'text_file' from 'symbol' (i.e. replace by '').

    Since this operation may be quite time consuming for large files (> 100MiB), it operates in
    a "smart" mode, i.e. actual processing is only done if 'symbol' is found in the first line
    of the file. If the screening operation breaks, only the "healthy" part of the file is
    written-back under the original filename, whereas the (corrupted) original is also retained
    for further analysis.

    Args:
        text_file (str): Filename of text-file to be cleaned.
        symbol (str, optional): Symbol that should bve removed through "cleaning". Defaults to
            '"' (double-quotes) as these are the most annoying from CSV-files.
        verbose (bool, optional): Switch to throw status messages & warnings if necessary.
            Defaults to 'True'.

    Returns:
        --
    """
    clean_lines = []
    enc = valid_encoding(text_file)

    # read data from file & clear
    with open(os.path.abspath(text_file), mode='r', encoding=enc) as tf:

        # probe 1st line
        line = tf.readline()
        chk = line.replace(symbol, '')
        if (len(chk) == len(line)):
            if (verbose):
                print(f"Warning: No symbol '{symbol}' found in 1st line of file! (skipping)")
            return

        # screen whole file
        clean_lines.append(chk)
        broken = False
        num_lines = 1
        while (True):
            if ((not num_lines%100000) and verbose):
                print(f"(read {num_lines} lines)")
            try:
                line = tf.readline()
                if (line != ''):
                    clean_lines.append(line.replace(symbol, ''))
                else:
                    break
                num_lines += 1
            except: # !! something is strange in the file :( !!
                broken = True
                print(f'Warning: Error @ line {num_lines-1}!! (writing until "last good")')

    # overwrite file (safely!)
    if (verbose):
        print(f"Overwriting '{text_file}' safely! (using temporary file copy)")
    with open(os.path.abspath(text_file+'_temp'), mode='wt') as tf:
        tf.writelines(clean_lines)
    if (broken):
        os.rename(text_file, text_file+'_ORIG_BROKEN') # keep original for analysis!
    else:
        os.remove(text_file)
    os.rename(text_file+'_temp', text_file)

    return


def file_bulk_op(root, pattern, mode='count', params=[], max_depth=99, dry=True, verbose=0):
    """ Performs mass file operations in 'root' using 'pattern' in a certain 'mode'.

    Args:
        root (str): Base location where to start traversing all subfolders for 'pattern'. Note
            that this requires intermediate and trailing '\\' (e.g. 'C:\\Windows\\').
        pattern (str): Filename or regex pattern to be used for operation.
        mode (str): Operation to be applied to all files matching the search pattern.
            Available options are:
                'count':    simply counts the number of matches (will overwrite 'verbose=0')
                'chmod':    change file's attributes (i.e. read/write permissions)
                'stamp':    update file's time information by "touching" it
                'remove':   delete all matched files (CAUTION: "Dry" run is highly recommended!)
                'rename':   rename filenames of matches acc. to specification in 'params'
                'replace':  replace text in files acc. to specification in 'params'
        params (2-tuple): Additional parameters required, depending on mode of operation, i.e.
                if 'rename':    params = [ orig_fname_part, new_fname_part ]
                if 'replace':   params = [ orig_line_tag, new_line ]
            Defaults to '[]' (i.e. unused).
        max_depth (int, optional): Maximum level of subfolder search, Default to '99'.
        dry (bool, optional): Switch for performing a "dry run" w/o actual changes to the files.
            Defaults to 'True'.
            Note: This should always be used first for testing, such that no harm is done! For
            the more advanced file operations checks on feasibility will still become apparent.
        verbose (int, optional): Mode of status messages where '0 = off', '1 = files' and '2 =
            track all visited folders'. Defaults to '0'.

    Returns:
        result (int/list/None): Depends on 'mode' of operation. Will be an integer if 'count',
            a list of files if 'collect' and 'None' in all other cases.

    Examples: (make sure to set 'dry_run=True' to test first!)

        (1) Some typical use may be to get rid of all 'desktop.ini' files on Windows systems:
            >>> massfileop(r'C:\', 'desktop.ini', mode='remove', dry_run=True)

        (2) Replace parts of header/comment lines in all Python files of a project:
            >>> massfileop('C:\\MyProject', '\\.py', mode='replace', params=['#*old*','#*new*'])

        (3) Replace (parts of the) filename, but only for matching CSV-files:
            >>> massfileop('C:\\MyProject', '\\.csv', mode='rename',
                           params=['#*old*','#*new*'])
    """

    # init
    rx = re.compile(pattern)
    results = []
    num_found = 0
    num_modified = 0

    # feedback on progress
    if (verbose):
        print("-"*64)
        print("Starting MASS-FILE-OPERATION @ "+time.strftime("%H:%M:%S (%Y-%m-%d):"))
        print(f"Looking for '{pattern}' under <{root}>")
        print("")
        print(f"Applying operation '{mode}'...")
        print("")

    # traverse all folders under given root...
    for path, folders, files in os.walk(root): #[:-1]): # Note: remove trailing '\\'?

        path_ = path[:-1] + os.sep
        depth = path_[len(root):].count(os.sep)

        # ... as long as maximum depth is not yet reached...
        if (depth >= (max_depth+1)):
            if (verbose > 1): print(f"Skipping <{os.path.join(path)}> (MAX DEPTH reached!)")
            continue
        else:
            the_folder = os.path.join(path)
            if (verbose > 1): print(f"Entering <{the_folder}>")
            for fname in files:

                # step 1: check if file matches pattern
                if (rx.search(fname) is not None):
                    the_file = os.path.join(the_folder, fname)

                    # register file
                    num_found += 1
                    results.append( the_file )
                    if (verbose > 1): 
                        print(f"  -> Found '{fname}'")
                    elif (verbose):  
                        print(f"  -> Found '{the_file}'")

                    # step 2: (try to) apply selected file operation
                    # simple
                    if (mode in ('count','chmod','stamp','remove')):
                        if (not dry):
                            try:
                                if (mode == 'count'):
                                    pass # do nothing ;)
                                elif (mode == 'chmod'):
                                    os.chmod(the_file, params[0])
                                elif (mode == 'stamp'):
                                    mytime = dt.datetime.now().timestamp()
                                    os.utime(the_file, (mytime,mytime))
                                elif (mode == 'remove'):
                                    os.remove(the_file)
                                num_modified += 1
                            except:
                                print(f"Warning: Could NOT {mode} '{the_file}'!")
                        else:
                            pass # do nothing

                    # advanced (check feasibility)
                    elif (mode in ('rename','replace')):

                        if (mode == 'rename'):
                            try:
                                if (type(params[0]) is re.Pattern): # RegEx replacement
                                    str_old = params[0].search(fname).group()
                                    str_new = params[1]
                                    fname_re = re.sub(str_old, str_new, fname)
                                    # print(str_old, str_new, fname_re)
                                else: # assume simple string replacement
                                    fname_re = re.sub(params[0], params[1], fname)
                                if (fname_re != fname):
                                    if (not dry):
                                        shutil.move(the_file, os.path.join(the_folder,fname_re))
                                        num_modified += 1
                            except:
                                print(f"     Warning: Could NOT {mode} '{the_file}'!")

                        elif (mode == 'replace'):

                            #
                            # TODO: apply 'dry_run' scheme for feasibility testing!
                            #

                            if (not dry):
                                with open(the_file, mode='rt+') as tf:
                                    pos = file_goto(tf, params[0], mode='tag', nextline=False)
                                    if (pos is not None):
                                        tf.seek(pos[0]-1, 0) # -1 / otherwise 1st char is eaten
                                        #time.sleep(0.100)
                                        print(f"tell = {tf.tell()}")
                                        text = tf.readlines()
                                        # breakpoint()
                                        # text[0] = params[1]+'\n'
                                        tmp = text[0]
                                        print(f"pos = {pos} // found tmp as: {tmp}")
                                        text[0] = re.sub(params[0], params[1], tmp)
                                        print(f" --> now it is: {text[0]}")
                                        tf.seek(pos[0], 0)
                                        tf.writelines(text)
                                        num_modified += 1
                            else:
                                pass # do nothing

    # print short summary
    if (verbose):
        print("")
        print(f"Found {num_found} files")
        print(f"Modified {num_modified} files")
        print("-"*64)

    return results


def get_dependencies(
    root: str,
    save_req_file: bool = True,
    save_analysis: bool = True, 
    with_version: bool = True,    
    incl_tracing: bool = True,
    incl_imports: bool = True,
    optionals_are_required: bool = False,
    excludes: list = ['venv', '.venv', '__pycache__'],
    trace_level: int = 3,    
    verbose: bool = True,
):
    """ Analyses all dependencies & required packages for sources in a given 'root' folder.

    This routine parses all files in the folder and will investigate user-scope dependencies 
    recursively down to 'trace_level'. All required packages of type 'known' and 'user' can be
    provided by a 'requirements.txt' file for ease of batch installation (e.g. using 'pip').
    Note that the special case of import statements found in an encompassing "try ... except" 
    branch are marked as "optional" and may be treated as such (unless enforced otherwise).

    Args:
        root (str): Base location for dependency search (e.g project folder).
        save_req_file (bool, optional): Switch for saving 'requirements.txt' for batch 
            processing (e.g. by 'pip install -r %FILE%'. Defaults to 'True'.
        save_analysis (bool, optional): Switch for saving the whole in-depth dependency 
            analysis to an additional file for investigations. Defaults to 'True'.
        with_version (bool, optional): Switch for adding versions to all required packages.
            Note: Dependencies will be in compatibility mode using '~=". Defaults to 'True'.
        incl_tracing (bool, optional): Switch to provide a list of source files calling each 
            required module. Defaults to 'True'.
        incl_imports (bool, optional): Switch to provide a list of all import statements in the
            source files. Defaults to 'True'.
        optionals_are_required (bool, optional): Switch to map optional requirements onto the
            standard package type categories and,thus, enforcing them. Defaults to 'False'.
        excludes (list, optional): Subfolders in 'root' that should be excluded from the search.
            Defaults to ['venv', '__pycache__'].
        trace_level (int, optional): Analysis level for recursive dependency scanning on added
            requirements. Defaults to '3' (ususally sufficient for user-created modules).
            Note: 1 = only direct tracking
                  2 = also analyse DIRECT dependencies of required files
                  3 = also analyse INDIRECT dependencies of required files     
        verbose (bool, optional): Switch for status messages on the search. Defaults to 'False'.

    Returns:
        --
    """

    # init
    D = _init_dep_dict()
    project_path, _, __ = fileparts(root)
    project_name = os.sep.join( project_path.split(os.sep)[-2:] )
    project = project_name if project_name else os.path.basename(project_path)
    # Note: Last two path items are assumed to be name-defining!
    
    if (verbose): print("-"*64 + "\n"+ f"Starting DEPENDENCY ANALYSIS for <{project}>..." + "\n")

    # traverse all folders & files in project
    num_folders, num_files = 0, 0
    for path, _, files in os.walk(root):
        path_norm = os.path.normpath(path)
        sub = path_norm.replace(root+os.path.sep, '')

        # respect excludes
        checks = [sub.startswith(tree) for tree in excludes]
        if (any(checks)):
            if (verbose): print(f"o Excluded <{sub}>")
            continue
        else:
            if (verbose): print(f"o Traversing FOLDER <{sub}>")
            num_folders += 1

        # check all relevant files
        for fname in files:
            if (fname.endswith(DEP_FILE_TYPES)):
                src_file = os.path.abspath(os.path.join(path_norm, fname))
                if (verbose): print(f"  + Checking file '{fname}'")
                D_src = dep_of_file(src_file, incl_tracing, incl_imports, False)                
                D = merge_items(D, D_src)
    
    # trace recursively to 2nd level (= DIRECT dependencies of required files)
    if (trace_level >= 2): 
        if (verbose): print("\n" + f"o Back-tracking USER modules to 2nd level... \n  (DIRECT dependencies of required files)" + "\n")
        
        # analyse by (temporary) import of direct dependency files
        D2 = _init_dep_dict()
        for dep_file in sorted(D['user']):
            if (verbose): print(f"  + Checking own dependencies of '{dep_file}'")
            try:
                tmp_module = importlib.import_module(dep_file)
                tmp_file = inspect.getsourcefile(tmp_module)
                D_tmp = dep_of_file(tmp_file, incl_tracing, incl_imports, False)
                D2 = merge_items(D2, D_tmp)
                del tmp_module, tmp_file, D_tmp
            except:
                print(f"Warning: In-directly required module {dep_file} not found")
        D = merge_items(D, D2)         

    # 3rd level = INDIRECT dependencies of required files
    if (trace_level >= 3): 
        if (verbose): print("\n" + f"o Back-tracking USER modules to 3rd level... \n  (INDIRECT dependencies of required files)" + "\n")        
        
        # further analyse by (temporary) import of indirect dependency files
        D3 = _init_dep_dict()
        for dep_file in sorted(D2['user']):
            if (verbose): print(f"  + Checking further dependencies of '{dep_file}'")
            try:
                tmp_module = importlib.import_module(dep_file)
                tmp_file = inspect.getsourcefile(tmp_module)
                D_tmp = dep_of_file(tmp_file, incl_tracing, incl_imports, False)
                D3 = merge_items(D3, D_tmp)
                del tmp_module, tmp_file, D_tmp
            except:
                print(f"Warning: In-In-directly required module {dep_file} not found")
        D = merge_items(D, D3)

    
    if (verbose): print("\n" + "o Sorting module dependencies..." + "\n")

    # treat optionals as required? (otherwise keep as separate category)
    if (optionals_are_required):
        for mod_name in D['optional']:
            if (mod_name.split('.')[0] in DEP_PKG_BUILTIN):
                D['builtin'].add(mod_name)
            elif (mod_name.split('.')[0] in DEP_PKG_KNOWN):
                D['known'].add(mod_name)
            else:
                D['user'].add(mod_name)
        dep_pkg_types = DEP_PKG_TYPES
    else:
        dep_pkg_types = list(DEP_PKG_TYPES)
        dep_pkg_types.append('optional')

    # sort dependencies (will be converted back to lists ;)
    for pkg_type in dep_pkg_types:
        D[pkg_type] = sorted(D[pkg_type], key=lambda x: x.lower())

    # sort trace-back and import information (if any)
    if (incl_tracing):
        D['tracing'] = dict( sorted(D['tracing'].items(), key=lambda x: x[0].lower()) )
        for mod_name, values in D['tracing'].items():
            D['tracing'][mod_name] = sorted(list(values), key=lambda x: x[0].lower())
    if (incl_imports):
        D['imports'] = dict( sorted(D['imports'].items(), key=lambda x: x[0].lower()) )
        for src_file, values in D['imports'].items():
            D['imports'][src_file] = sorted(list(values), key=lambda x: x[1])

    if (verbose): print("\n"+ f"o Deriving required packages..." + "\n")

    R = {} 
    for pkg_type in dep_pkg_types:
        R[pkg_type] = []
        for mod_name in D[pkg_type]:
            pkg_name = mod_name.split('.')[0]
            if (pkg_name not in R[pkg_type]):
                R[pkg_type].append(pkg_name)   
        
    # print summary
    if (verbose):
        print("\n" + "...finished DEPENDENCY analysis!" + "\n")
        print("-"*64)

        print(f"{len(D['builtin'])} BUILTIN modules from {len(R['builtin'])} packages required:")
        print(f"{D['builtin']}" + "\n")
        print(f"{len(D['known'])} KNOWN modules from {len(R['known'])} packages required:")
        print(f"{D['known']}" + "\n")
        print(f"{len(D['user'])} USER modules from {len(R['user'])} packages required:")
        print(f"{D['user']}" + "\n")
        if (not optionals_are_required):
            print(f"...and {len(D['optional'])} OPTIONAL modules from {len(R['optional'])} packages required:" + "\n")
            print(f"{D['optional']}" + "\n")   
    
    # save list of dependencies to file (e.g. for batch install by 'pip install -r requirements.txt' in a 'venv')
    if (save_req_file): 
        with open(os.path.join(project_path, _DEP_REQ_FILE), mode='wt') as rf:
            for req in [*R['known'], *R['user']]:
                rf.write(f"{req}")
                if (with_version):
                    try:
                        xyz = eval(f"__import__('{req}')")
                        rf.write(f"~={xyz.__version__}")
                        del xyz
                    except:
                        pass
                rf.write(f"\n")
            if (not optionals_are_required):
                for req_opt in R['optional']:
                    rf.write(f"({req_opt}) //optional")

    # save dependency analysis infos to file?
    if (save_analysis):
        with open(os.path.join(project_path, _DEP_ANALYSIS_FILE), mode='wt') as df:
            df.write("================================================================================\n")
            df.write(f"DEPENDENCY Analysis for <{project}> @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            df.write("================================================================================\n")
            df.write("\n")
            df.write("--------------------------------------------------------------------------------\n")
            df.write("SUMMARY:\n")
            df.write(f" o Searched in {num_folders} folders / {num_files} files\n")
            df.write(f" o Found {len(D['builtin'])} builtin modules from {len(R['builtin'])} packages\n")
            df.write(f" o Found {len(D['known'])} known modules from {len(R['known'])} packages\n")
            df.write(f" o Found {len(D['user'])} user modules from {len(R['user'])} packages\n")
            if (not optionals_are_required):
                df.write(f" o ...and {len(D['optional'])} optional modules from {len(R['optional'])} packages\n")
            df.write("--------------------------------------------------------------------------------\n")
            df.write("\n")
            df.write("---- BUILTIN modules ------------\n")
            df.write("\n")
            for item in D['builtin']:
                df.write(f"+ {item}\n")
            df.write("\n")
            df.write("---- KNOWN modules --------------\n")
            df.write("\n")
            for item in D['known']:
                df.write(f"+ {item}\n")
            df.write("\n")
            df.write("---- USER modules ---------------\n")
            df.write("\n")
            for item in D['user']:
                df.write(f"+ {item}\n")
            if (not optionals_are_required):
                df.write("\n")
                df.write("---- (optional modules) ---------------\n")
                df.write("\n")
                for item in D['optional']:
                    df.write(f"+ {item}\n")
            df.write("\n\n\n")
            if (incl_tracing):
                df.write("--------------------------------------------------------------------------------\n")
                df.write(f"---- TRACE-BACK OF DEPENDENCIES (for each required module, level = {trace_level}) ----------\n")
                df.write("--------------------------------------------------------------------------------\n")
                for dep_file in D['tracing']:
                    df.write("\n")
                    df.write(f"<{dep_file}>\n")
                    for idx in range(len(D['tracing'][dep_file])):                       
                        df.write(f"    {D['tracing'][dep_file][idx][0]} @ {D['tracing'][dep_file][idx][1]}\n")
            else:
                df.write("NO BACK-TRACING of dependencies (as required by source files) has been performed.\n")
            df.write("\n\n\n")
            if (incl_imports):
                df.write("--------------------------------------------------------------------------------\n")
                df.write("---- LIST OF IMPORT LINES (for each source file) -------------------------------\n")
                df.write("--------------------------------------------------------------------------------\n")               
                for src_file in D['imports']:
                    df.write("\n")
                    df.write(f"<{src_file}>\n")
                    for idx in range(len(D['imports'][src_file])):
                        df.write(f"    {D['imports'][src_file][idx][1]:-4d}: {D['imports'][src_file][idx][0]}\n")
            else:
                df.write("NO LISTING of imports (from each source file) has been performed.\n")
            df.write("\n")

    return


def dep_of_file(
    src_file: str, 
    incl_tracing: bool = True,
    incl_imports: bool = False,
    verbose: bool = False
) -> dict:
    """ Analyses dependencies of a single Python 'src_file'.
    
    Args:
        src_file (str): Python file to be analysed for its dependencies.
        incl_tracing (bool, optional): Switch to provide list "requesting" source files for all
            dependencies. Defaults to 'True'.
        incl_imports (bool, optional): Switch to provide list of all import statements in the
            source files. Defaults to 'False'.       
        verbose (bool, optional): Switch for status messages on the search. Defaults to 'False'.

    Returns:
        D (dict): Dict w/ all requirements of 'src_file' and additional details (if selected).
    """
    
    if (verbose): print(f"Analysing dependencies of file {src_file}")
  
    # analyse dependencies found in file
    D = _init_dep_dict()
    _, fname, fext = fileparts(src_file)
    with open(src_file, mode='rt') as sf:
        inside_doc_string = False
        inside_try_statement = False

        for n, line in enumerate(sf.readlines(), start=1):

            # determine indentation level & remove whitespace
            whitespace = _RX_WHITESPACE.match(line)
            indent_level = int(whitespace.end()/4) if whitespace else 0
            line = line.strip()
            
            # handle & skip doc-strings
            chkdoc = line.split(S_DOC_STR_QUOTES)
            if (chkdoc[0] != line):
                if (not inside_doc_string) and (len(chkdoc) == 2):
                    inside_doc_string = True # entering...
                    if (verbose): print(f"line #{n:-4d}: entering DOC-string...")
                elif (inside_doc_string):
                    inside_doc_string = False # ...leaving  
                    if (verbose): print(f"line #{n:-4d}: ...leaving DOC-string")
                # Note: If doc-string is entered & left on the same line, len(chkdoc) would
                # be >= 2 and therefore passed on as well...
            if (inside_doc_string):
                continue # w/ next line
            
            # handle imports within 'try ... except' branches 
            if (line.find("try:") >= 0):
                inside_try_statement = True # entering...
                if (verbose): print(f"line #{n:-4d}: entering TRY-statement...")
            elif (line.find("except:") >= 0):
                inside_try_statement = False # ...leaving
                if (verbose): print(f"line #{n:-4d}: ...leaving TRY-statement")

            # handle comments
            if (line.find('#') >= 0):
                line = line.split('#')[0] # Note: Comment might be only after some code?
                
            # check for dependency
            dep_type = None
            if (not indent_level): # @ top level
                if (not dep_type):
                    chk = _RX_IMPORT_FROM.match(line)
                    if (chk): dep_type = 'from_import'
                if (not dep_type):
                    chk = _RX_IMPORT.match(line)
                    if (chk): dep_type = 'import'
            else: # @ function/class definitions
                if (not dep_type):
                    chk = _RX_IMPORT_FROM.search(line)
                    if (chk): dep_type = 'from_import_in_func'
                if (not dep_type):
                    chk = _RX_IMPORT.search(line)
                    if (chk): dep_type = 'import_in_func'
            if (not dep_type):
                continue # w/ next line

            # discard hit if it is within another string!
            before = line[:chk.span()[0]]
            after = line[chk.span()[1]:]
            if (_RX_QUOTES.search(before)):
                if (verbose): print(f"line #{n:-4d}: discarding hit! (since *within* string expression)")
                continue

            # record new dependency
            mod_name = chk.groupdict()['module']
            package = mod_name.split('.')[0]
            if (not inside_try_statement):
                if (package in DEP_PKG_BUILTIN):
                    D['builtin'].add(mod_name)
                elif (package in DEP_PKG_KNOWN):
                    D['known'].add(mod_name)
                else: # unknown, must be user-specific
                    D['user'].add(mod_name)
            else:
                D['optional'].add(mod_name)
            # Note: If an import is within a "try ... except" statement it will be considered 
            # optional as it is not absolutely required for operation!

            # add to list of module-requesting files?
            if (incl_tracing):
                if (mod_name not in D['tracing'].keys()):
                    D['tracing'][mod_name] = {(src_file, n)}
                else:
                    D['tracing'][mod_name].add((src_file, n))

            # extract import statement as in file?
            if (incl_imports):
                line_cleaned = line.split('#')[0].strip()
                src_fname = fname+'.'+fext
                if (src_fname not in  D['imports'].keys()):
                    D['imports'][src_fname] = {(line_cleaned, n)}
                else:
                    D['imports'][src_fname].add((line_cleaned, n))

            # print info about analysis progress
            if (verbose):
                opt = ' (OPTION)' if inside_try_statement else ''
                if (dep_type == 'import'):
                    print(f"line #{n:-4d}: depends on module <{mod_name}>"+opt)
                elif (dep_type == 'from_import'):
                    print(f"line #{n:-4d}: depends on (parts of) module <{mod_name}>"+opt)
                elif (dep_type == 'import_in_func'):
                    print(f"line #{n:-4d}: some function depends on module <{mod_name}>"+opt)
                else: # (dep_type == 'from_import_in_func')
                    print(f"line #{n:-4d}: some function depends on (parts of) module <{mod_name}>"+opt)

    return D



#-----------------------------------------------------------------------------------------------
# PRIVATE FUNCTIONS (only to be used from internal methods, but not to be exposed!)
#-----------------------------------------------------------------------------------------------

def _init_dep_dict() -> dict:
    """ Initializes the keys for dependency analysis calls. 
    
    Created dict has keys from '_DEP_PKG_TYPES' w/ 'set' values, as well as keys 'tracing' and 
    'imports' w/ 'dict' values. Note that the latter will only be populated if the respective 
    switches are activated (see 'dependencies()' and 'dep_of_file()').
    """    
    D = {}
    for key in DEP_PKG_TYPES:
        D[key] = set()
    D['optional'] = set() # special case for import statements within 'try ... except'
    D['tracing'] = dict() # only required for tracing-back requirements to source files
    D['imports'] = dict() # only required if showing import statements
    # Notes: Both 'tracing' and 'imports' will be composed as dicts w/ following meaning:
    #   keys: str           -> names of modules (for 'tracing') or files (for 'imports')
    #   values: (str, int)  -> where the 2nd index refers to the line number but the 1st is
    #                           - either the source file (for 'tracing') 
    #                           - or the exact line from the file (for 'imports')
    return D

