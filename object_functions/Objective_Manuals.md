# The environment and steps to generate customised cores

## FPGA Board Name

xczu19eg-ffvc1760-2-i (active)

## Environment Requirement

Ubuntu 22.04

java

```sudo apt install openjdk-11-jre-headless```\
```sudo apt install openjdk-11-jdk-headless```

mill

```sudo sh -c "curl -L https://github.com/com-lihaoyi/mill/releases/download/0.6.3/0.6.3 > /usr/local/bin/mill && chmod +x /usr/local/bin/mill"```

## Nutshell

```git clone https://github.com/OSCPU/NutShell.git```\

```git checkout -q release-211228```
