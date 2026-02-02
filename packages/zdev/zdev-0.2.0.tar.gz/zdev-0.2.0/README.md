# zdev

Versatile collection of helper functions for common development tasks.

## Synopsis

The ```zdev``` library hosts a versatile collection of functions that enable quick & easy algorithmic development. This is structured into several modules acc. to their area of use. Note that some of these will incur a significant number of dependencies; however, many of these may be considered "standard" ones for Python anyway (e.g. ```numpy```, ```matplotlib``` or ```pandas```).

## Contents

All tests are located in the "\test" folder. The majority of these test is "unit test" in nature such that it specifically adresses functions in each module - hence the name structure.

*Note: Some of these functions do also require additional packages such as ```zynamon``` and ```dsap```!*

Besides, some larger demo applications are given in the "\app" folder, e.g. the

- **DataFeeder_GUI**: app for illustrating both static & animated plots
- **DataBroker_GUI**: app to try connections to various databases (e.g. Postgres or InfluxDB)

Furthermore, the BAT-file **auto_deploy.bat** is intended to provide a "single-click" solution for deployment of an operational project from the (development) host to another machine. In this process, a virtual Python environment and all requirements shall be installed in one go.

*Note: All of these scripts are still highly in (ALPHA) state and not yet ready for productive use!*

## Package

The essence of the tools is given by the package **zdev** which is located in the respective subfolder. It contains the following main modules:

- base
- core
- indexing
- parallel
- plot
- testing
- validio
- colors
- searchstr

For more info, see the respective [package info](README_pkg.md).

[ Dr. Marcus Zeller | dsp4444@gmail.com | Erlangen, Germany | 2019-2025 ]
