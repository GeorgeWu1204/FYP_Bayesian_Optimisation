# The environment and steps to generate customised processors

## FPGA Board Name

xczu19eg-ffvc1760-2-i (active)

## Environment Requirement

Ubuntu 22.04

## NutShell Core

### Prerequisites

run ```sudo vmhgfs-fuse .host:/Year4 /mnt/hgfs -o allow_other``` to mount the shared folder

java

```sudo apt install openjdk-11-jre-headless```\
```sudo apt install openjdk-11-jdk-headless```

mill

```sudo sh -c "curl -L https://github.com/com-lihaoyi/mill/releases/download/0.6.3/0.6.3 > /usr/local/bin/mill && chmod +x /usr/local/bin/mill"```

Clone Project

```git clone https://github.com/OSCPU/NutShell.git```\
```git checkout -q release-211228```

### Steps

``` make bitstream BOARD=PXIe ```

## VeeR EL2 RISC-V Core

### Prerequisites

- Verilator (4.106 or later)
- RISC-V GNU Compiler Toolchain
- ```export RV_ROOT=/home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/Cores-VeeR-EL2```
- TODO: Have not came up with a better method to handle this. The current method is to modify the ```configs/veer.config``` line 373 to ```$build_path = "/home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/Cores-VeeR-EL2/snapshots/$snapshot" ;```
- TODO2: To run the dhry benchmark, need to modify the ```tb_top.sv``` to delete the selection of ```verilator```
### Steps

```make -f $RV_ROOT/tools/Makefile```


