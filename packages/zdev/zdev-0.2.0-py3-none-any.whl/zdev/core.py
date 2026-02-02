"""
Core development utilities (e.g. frequent checking & handling tasks).
"""
import os
import sys
import numpy as np
from functools import partial


# EXPORTED DATA
TYPES_INT = (int, np.int64, np.int32, np.int16, np.int8)
TYPES_FLOAT = (float, np.float64, np.float32, np.float16)
TYPES_COMPLEX = (complex, np.complex128, np.complex64)


def howmany(obj):
    """ Returns number of references inherent to PyObject 'obj' in CPython memory. """
    return sys.getrefcount(obj)


def isarray(x):
    """ Checks if 'x' is an array / iterable (i.e. if 'len()' is properly evaluated). """
    try:
        len(x)
        return True
    except:
        return False
   

def istype(x, mode, check_all=False):
    """ Returns an 'any-integer-type' indication (also works for arrays). 
    
    Args:
        x (:obj:):
        mode (type): Data type to probe for w/ options int|float.
        check_all (bool, optional): Switch to check all items (if 'x' is an iterable).

    Returns:
        res (bool): Result of the check(s).
    """
    
    # assign type variants 
    if (mode is int):
        types = TYPES_INT 
    elif (mode is float):
        types = TYPES_FLOAT 
    elif (mode is complex): 
        types = TYPES_COMPLEX
    else:
        raise ValueError(f"Unknown mode '{mode}' for type-checking")

    # type checking
    if (isarray(x)):
        if (check_all):
            chk = []
            for item in x:
                chk.append(type(item) in types)
            return all(chk)
        else:
            return (type(x[0]) in types)
    else: 
        return (type(x) in types)

isint = partial(istype, mode=int)
isfloat = partial(istype, mode=float)
iscomplex = partial(istype, mode=complex)


def anyfile(path, base, formats):
    """ Checks if folder 'path' contains a file 'base' in *any* of the acceptable 'formats'.

    Args:
        path (str): Folder location in which to look for files.
        base (str): Base of the filename to which the format/extension will be appended.
        formats (list of str): List of known formats to probe for. In order to robustify this
            helper function, leading '.' (if present) are automatically dealt with.

    Returns:
        fname_existing (str): Full filename of the 1st existing file that matched the
            combination of 'base' + a format from the list.
    """
    if (type(formats) is str):
        formats = [formats]
    for fmt in formats:
        if (fmt.startswith('.')):
            fmt = fmt[1:]
        fname_existing = os.path.join(path, base+'.'+fmt)
        if (os.path.isfile(fname_existing)):
            return fname_existing
    # Note: The same job is done by the following - using abbreviations ;)
    # [ os.path.join(p,b+'.'+f) for f in fmts if (os.path.isfile(os.path.join(p,b+'.'+f))) ][0]
    return None


def fileparts(the_file, relative=False):
    """ Returns path, filename and extension (mimic MATLAB function). """    
    fpath, fname, fext = None, None, None
    if (not relative):
        full_name = os.path.abspath(the_file)
    else:
        full_name = the_file
    if (os.path.isdir(full_name)):
        fpath = full_name
    else:
        fpath = os.path.dirname(full_name)
        filename = os.path.basename(full_name)
        tmp = filename.split('.')[:]    
        if (len(tmp) == 1):
            fname = tmp[0] # Note: 'the_file' was a mere string!
        else: # ...otherwise, ensure any '.' are kept & only last one is seen as extension!
            fname = '.'.join(tmp[:-1])
            fext = tmp[-1]
    return os.path.normpath(fpath), fname, fext


def filesize(bytes_, binary=True):
    """ Returns string w/ proper file size acc. to https://en.wikipedia.org/wiki/Byte

    Args:
        bytes_ (int): Number of bytes = file size.
        binary (bool, optional): Switch for having binary bases instead of decimal ones (i.e.
            calculating "MiB/GiB/..." instead of "MB/GB/..."). Defaults to 'True'.
    Returns:
        bytes_str (str): Proper string of the file size (to be inserted into text).
    """

    # init
    num_bytes = int(bytes_)
    unit = [ 'Bytes', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y' ]

    # select reference for computations
    if (binary):
        base = 1024
        addon = 'i'
    else:
        base = 1000
        addon = ''

    # create appropriate string representation
    if (num_bytes < base):
        bytes_str = f"{num_bytes} {unit[0]}"
    else:
        order = 0
        while (True):
            order += 1
            if (num_bytes < base**(order+1)):
                res = divmod(num_bytes, base**order)
                bytes_str = f"{res[0]+res[1]/(base**order):.2f} {unit[order]}{addon}B"
                break
            if (order >= len(unit)):
                bytes_str = "more_than_YiB"

    return bytes_str


def local_val(x, k, width, mode='avg'):
    """ Computes a local quantity of 'x' around index 'k' with 'width'.

    Args:
        x (list or np.array): Array of samples for which a "local" value should be computed.
        k (int): Current index within 'x' for which a "local" value should be computed.
        width (int): One-sided width of non-causal window around 'x[k]'.
        mode (str, optional): Filtering mode w/ options: 'avg'|'max'|'min'|'sum'|'median'.
            Defaults to 'avg' (= mean).

    Returns:
        val (float): Computed "local" quantity acc. to selected 'mode'.
    """

    # determine valid index range & gather local array
    nlo = max(0, k-width)
    nup = min(k+width, len(x)-1)
    tmp = [x[n] for n in range(nlo,nup+1)]

    # compute quantity
    if (mode == 'avg'):
        return np.mean(tmp)
    elif (mode == 'max'):
        return np.max(tmp)
    elif (mode == 'min'):
        return np.min(tmp)
    elif (mode == 'sum'):
        return np.sum(tmp)
    elif (mode == 'median'):
        return np.median(tmp)   
    else:
        raise NotImplementedError(f"Unknown quantity {mode}")


def merge_items(d1, d2, only_keys=[], strict_mode=True, sort_values=True):
    """ Merges items of dicts 'd1' and 'd2' acc. to value types and settings.
    
    Args:
        d1 (dict): First dict w/ arbitrary items.
        d2 (dict): Second dict w/ same keys as 'd1' (see 'strict_mode') and values of same type.
        only_keys (list, optional): List of keys onto which merge operation is restricted. 
            If this is used, any other keys will be removed from the result. Defaults to '[]'.
        strict_mode (bool, optional): Switch to enforce a "strict" operation where values in 'd1'
            will only be amended by 'd2' if the same keys are also existing there (i.e. in 'd2').
            Otherwise, the result will be a superposition of the items from both dicts. 
            Defaults to 'True'.
        sort_values (bool, optional): Switch to ensure that list or set values in the output 
            dict have sorted values. Defaults to 'True'.       

    Returns:
        merged (dict): Resulting dict w/ compatible values of 'd1' and 'd2' combined.
    """

    # init
    if (strict_mode):
        the_keys = set(d1.keys())
    else:
        the_keys = set(d1.keys()).union(d2.keys())
    merged = dict.fromkeys(the_keys)
    # Note: In "sets", items are always inherently sorted!

    # dict merge operation
    for key in the_keys:
        val1 = d1[key] if (key in d1.keys()) else None
        val2 = d2[key] if (key in d2.keys()) else None
        
        # handle key restrictions (if any)
        if (only_keys and (key not in only_keys)):
            if (key in d1.keys()):
                merged[key] = val1
            else:
                merged.pop(key)
            continue

        # handle compatible values
        if ((type(val1) is str) and (type(val2) is str)):
            merged[key] = val1 + val2

        elif ((type(val1) is list) and (type(val2) is list)):
            tmp = val1
            tmp.extend(val2)
            merged[key] = sorted(tmp) if sort_values else tmp

        elif ((type(val1) is set) and (type(val2) is set)):
            tmp = val1.union(val2)
            merged[key] = set(sorted(tmp)) if sort_values else tmp
        
        elif ((type(val1) is dict) and (type(val2) is dict)):
            merged[key] = merge_items(val1, val2, only_keys=[], strict_mode=False, sort_values=sort_values)
            # Note: For dict recursions, all keys and possible extensions are enabled!

        else: # Note: Keep 'd1' for any other type!
            merged[key] = val1 if (key in d1.keys()) else val2    

    return merged
