#!/bin/bash

# Base directories
SOURCE="/mnt/hgfs/MasterThesis/FYP_Bayesian_Optimisation/object_functions/NutShell/"
DESTINATION="/home/george/Documents/FYP/NutShell/"

# File to be copied
SETTINGS="src/main/scala/top/Settings.scala"

GENERATE_DESIGN="build"
# Copy the file, overwriting if necessary
cp -f "${SOURCE}${SETTINGS}" "${DESTINATION}${SETTINGS}"


cd Documents/FYP/NutShell
make clean
make verilog BOARD=PXIe

cp -f "${DESTINATION}${GENERATE_DESIGN}" "${SOURCE}"

