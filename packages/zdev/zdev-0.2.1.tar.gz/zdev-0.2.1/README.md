# zdev

Versatile collection of helper functions for common development tasks.

## Synopsis

This library provides handy functions for frequent tasks during development as well as for productive use in Python programs (e.g. stripping fileparts). Application focus is to support **automation scripts** as well as development of **algorithmic functions**.

## Contents

The package is structured into the following modules:  

- **colors**: Default color definitions w/ semantic names, e.g. 'cRed' or 'cDodgerBlue'

- **core**: Basic type & file checking helpers.

- **display**: Handy convenience functions for a one-line, yet sophisticated, control of figures based on ```matplotlib``` and ```plotly``` calls. *Note: For support on plotting ```zynamon.zeit.TimeSeries``` the underlying package must be installed as well! (optional requirement)*

- **indexing**: Helpers related to all kinds of "find-something" tasks (e.g. file-goto, runlength sections etc)

- **parallel**: Convenience functions for Python's builtin ```multiprocessing``` package and custom classes for controllable dispatching of jobs onto N cores.

- **searchstr**: Regular expressions to find common strings (e.g. identifiers w/ or w/o hyphens, numbers etc)
  
- **sound**: Audio-related helpers (e.g. interpret any array and play as sound w/ defined fs)

- **testing**: Set of dummy functions w/ and w/o arguments and possible writing of "flag-files" that can be used for testing of e.g. routines in ```zdev.parallel```

- **utils**: Main collection of frequently used dev utilitites (e.g. dependency analysis, bulk file operations, infos on storage/time/etc)

- **validio**: Functions to check & convert for a robust I/O behaviour (e.g. auto-replace "problematic" characters etc)

[ Dr. Marcus Zeller | dsp4444@gmail.com | Erlangen, Germany | 2019-2026 ]