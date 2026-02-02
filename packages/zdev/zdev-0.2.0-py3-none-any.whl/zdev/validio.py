"""
Validation and user I/O-related functions for convenience.
"""
import os
import re
import sys
import stat

from zdev.core import isarray
from zdev.indexing import expand_index_str, find_index_str
from zdev.searchstr import S_SEP_W_DOT, S_BRACKETS, S_SPECIAL


# INTERNAL PARAMETERS & DEFAULTS
_ENCODINGS = ('ascii', 'utf_8', 'utf_16', 'utf_32')


def valid_array(x):
    """ Ensures that 'x' is a valid array such that 'len(x)' evaluates properly. 
    
    Args:
        x (:obj:): Any object, i.e. scalar or array.

    Returns:
        x_iter (:obj:): Iterable object.
    """
    return x if isarray(x) else [x,]


def valid_prec(x, p):
    """ Returns float 'x' with a valid, i.e. fixed, precision 'p'.

    Args:
        x (float): Floating-point number
        p (int): Desired precision w.r.t. number of digits after '.'.

    Returns:
        xf (float): Floating-point number truncated to 'p' fractional digits.
    """
    return float(f'{x:.{p}f}')


def valid_path(path_in):
    """ Validates that proper path separators are applied for 'path_in'.

    Args:
        path_in (str): Original path location string (may contain '\' and/or '/').

    Returns:
        path_out (str): Output path string w/ system-dependent separators.
    """
    if (sys.platform.startswith == 'win'):
        path_out = path_in.replace('/', '\\')
    elif (sys.platform.startswith == 'linux'):
        path_out = path_in.replace('\\', '/')
    else:
        path_out = path_in
    return path_out


def valid_str_string(str_in):
    """ Validates 'str_in' is cleaned of dual quotes (either single ' or double ").

    This function validates that only a single pair of quotes (either ' or ") remains in the
    output 'str_out'. This may be required in circumstances of repeated im-/exporting of data
    to/from files where strings may exhibit a "cluttering" and mixture of quotes. If the input
    is not of type 'str' it will just be passed through.

    Args:
        str_in (str): Input string, possibly w/ multiple-stage quotes.

    Returns:
        str_out (str): Output string w/ clean quotes.
    """
    str_out = str_in
    while ((type(str_in) is str) and ((str_in[0] in ("'",'"')) and (str_in[-1] in ("'",'"')))):
        str_out = str_in[1:-1]
        str_in = str_out
    return str_out


def valid_str_number(s):
    """ Validates input string 's' is *always* mapped to a number.

    Args:
        s (str): Input string that should refer to a number, e.g. "4.77".

    Returns:
        x (float): Output number as 'float'. Will be '0.0' conversion fails, or if 's' is empty.
    """
    try:
        x = float(s)
    except:
        x = 0.0
    return x


def valid_str_name(name, repl_str='_', repl_dict=None, repl_defaults=True, compact=False):
    """ Validates 'name' is "safe" for using as filename (i.e. removes "problematic" chars).

    Args:
        name (str): Original name / identifier string (incl. problematic chars).
        repl_str (str): Replacement string (typically one char) for "problematic" parts of the 
            original. Defaults to underscore, i.e. '_'.
        repl_dict (dict): Dictionary with 'key: value' pairs for fine-tuning of replacements.
            If this is given, this will be executed first, in order to gain precedence.
            Defaults to 'None'.
        repl_defaults (bool, optional): Switch to replace all known, special chars (e.g. dots,
            slahes, brackets etc). Defaults to 'True'.
            Note: In case only the provided 'repl_dict' shall be used, this has to be disabled!
        compact (bool, optional): Switch to delete all remaining whitespace, otherwise 
            'repl_str' will be applied again. Defaults to 'False'.
        

    Returns:
        name_safe (str): Modified name / identifier that can "safely" be used as e.g. filename.

    Examples: For usage w/ replacement by '_' and dict {'°C': 'deg'} and active 'compact':
                input:  "This [is] my/your 100°C hot+stuff;  {extra space}"
                output: "This_is_my_your100deghot_stuff__extraspace_"
    """
    tmp = name
    
    # replace "problematic" (but information-bearing) chars by equivalent strings?
    if (repl_dict is not None):
        for key in repl_dict.keys():
            tmp = tmp.replace(key, repl_dict[key])
    # Note: Examples for this might be {'>=': 'gte'}, {'+': 'plus'} or {'°C': 'degC'}.
    
    # replace default special chars
    if (repl_defaults):        
        tmp = re.sub(S_BRACKETS+'|'+ S_SEP_W_DOT+'|'+S_SPECIAL, repl_str, tmp)
        tmp = tmp.replace('/',repl_str)   # forward dashes "/"
        tmp = tmp.replace('\\',repl_str)  # backward dashes "\"

    # replace any remaining whitespace
    if (compact):
        name_safe = tmp.replace(' ', '')
    else:
        name_safe = tmp.replace(' ', repl_str)

    return name_safe


def valid_elements(collection, prefix='v_', postfix='', tkinter=False):
    """ Extracts only elements w/ valid names from a 'collection'.

    The 'validation' criteria are thereby given by both 'prefix' and/or 'postfix' strings. If
    one or both of these are set to 'None' they are essentially disregarded. In cases where the
    collection refers to tkinter variables (i.e. Boolean/Int/Double/StringVar()), the respective
    '.get()' method is used in order to return the plain values only.

    Args:
        collection (dict): Input data set to be matched against pre-/postfix conditions.
        prefix (str, optional): Required prefix for 'validated' elements. Defaults to 'v_'.
        postfix (str, optional): Required postfix for 'validated' elements. Defaults to ''.
        tkinter (bool, optional): Flag indicating that collection contains tkinter variables.
            Defaults to 'False'.

    Returns:
        elements (dict): Output data set w/ possibly reduced number of 'validated' entries.
    """
    M = len(prefix)
    ## TODO?  N = len(postfix)

    # extraction process
    elements = {}
    for item in collection.keys():
        if (item.startswith(prefix)):
            # TODO: add the postfix requirement!
            #   (how to use 'N'? --> [ :-1-(N-1)]? but then: N=0 --> [ :0] --> will crash!!)
            if (tkinter):
                elements[item[M:]] = collection[item].get()
            else:
                elements[item[M:]] = collection[item]

    return elements


def valid_encoding(text_file):
    """ Checks a 'text_file' for used encoding (by trial & error).

    Args:
        text_file (str): Filename of text-tile to be tested for encoding.

    Returns:
        enc ('str'): Encoding as found in file (i.e. 'utf-8' or else). Defaults to 'None'.
    """

    # check proper encoding ("trial & error")
    matched = False
    for enc in _ENCODINGS:
        fh = open(text_file, mode='rt', encoding=enc)
        try:
            fh.readline()
            fh.seek(0)
            matched = True
            break
        except:
            fh.close()
            continue

    # return only if matched
    if (matched):
        return enc
    else:
        return None


def valid_args(inputs, force_int=False, resolve_idx_str=True):
    """ Validates arguments for function calls.

    This function probes if the input string(s) can be interpreted as float, integer or boolean
    values. The resulting output list contains the same number of elements, however, the
    types of all elements may vary.

    Args:
        inputs (list): List of entries, all of type 'str' (single inputs are promoted to list).
        force_int (bool): Switch for enforcing 'float' to 'int' conversion whenever possible.
            Defaults to 'False'.
        resolve_idx_str (bool): Switch for expanding index strings to sets of integer indices.
            Defaults to 'True'.

    Returns:
        outputs (list): Validated arguments (for function calls) w/ possibly converted types.
    """

    # ensure 'list' type
    if (type(inputs) != list):
        inputs = [inputs]

    # clean strings & map to types (where possible)
    outputs = []
    for item in inputs:
        chk = valid_str_string(item)

        # try to resolve index string?
        if (resolve_idx_str and (find_index_str(chk) != [])):
            arg = expand_index_str(chk)

        else: # try to map all items to standard types

            if (chk == 'True'):
                arg = True
            elif (chk == 'False'):
                arg = False
            elif (chk == 'None'):
                arg = None
            else:
                try:
                    arg = float(chk)
                    if (force_int and arg.is_integer()):
                        arg = int(arg)
                except:
                    try:
                        arg = int(chk)
                    except:
                        arg = chk

        outputs.append( arg )

    return outputs


def force_remove(func, path, excinfo):
    """ Forcibly removes folders even if they are set to "read only".

    Set this function as 'onerror' handling when calling to 'shutil.rmtree()', i.e.:
        > shutil.rmtree(myfolder, onerror=force_remove)

    [ https://stackoverflow.com/questions/1889597/deleting-read-only-directory-in-python ]
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)
    return
