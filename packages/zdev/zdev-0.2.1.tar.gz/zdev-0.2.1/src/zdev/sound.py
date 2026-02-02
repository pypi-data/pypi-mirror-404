"""
Some handy audio utilities.
"""
import numpy as np
import sounddevice as sd
from functools import partial


def quickplay(x, fs=48000, dtype=np.int16, normalise=True, device='default'):
    """ Quickly plays 'x' as an audio signal.

    Args:
        x (array-type): Any array type, will be converted to 'ndarray'.
        fs (float, optional): Sampling rate for playback.
        normalise (bool, optional): Switch for normalising volume. Defaults to 'True'.
        device (str, optional): Playback device. Defaults to 'default'.

    Returns:
        --
    """    
    if (type(x) is not np.ndarray):
        x = np.array(x)

    if (normalise):
        x_peak = np.max(np.abs(x))
        xn = x / x_peak
    else:
        xn = x

    if (dtype is None):
        dtype = xn.dtype
        xs = xn
    elif (dtype == np.int16):
        xs = xn * 32767 # 16-bit signed integer
        xs = xs.astype(dtype)

    # PortAudio
    player = sd.OutputStream(samplerate=fs, channels=1, dtype=dtype, device=device)
    player.start()
    player.write(xs)

    return

qplay = partial(quickplay, device='default')
