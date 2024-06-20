# all-in-one-build-environment
scripts and files for the all-in-one-build environment setups, containing scripts and 3rd party binaries, that help to easily get a self-compiled version of itom.

## Introduction
In order to simplify the compilation of **itom** under Windows, build packages, denoted as **all-in-one-build-environment** are provided for different versions of necessary 3rd party libraries and Visual Studio versions under [https://sourceforge.net/projects/itom/files/all-in-one-build-setup/]. 

These packages mainly contain the following features:

* relevant 3rd party packages for a basic build of itom, designerplugins and plugins
* additional 3rd party packages to also compile itom with support of point clouds and polygon meshes
* a setup script that pulls the relevant git repositories from [github.com/itom-project], configure the CMake configurations and make an initial debug and release build with your pre-installed version of Visual Studio.

## Purpose of this repository
This repository will be used to also develop versioned files of the setup scripts and other important files of the packages. It will not contain all the 3rd party binaries. In case of minor bugfixes, we also think about fetching parts of the setup scripts from this repository, such that the resources, obtained from [https://sourceforge.net/projects/itom/files/all-in-one-build-setup] must not be changed for a smaller bugfix, but will automatically download the most important setup scripts from this repository and its corresponding branches.
