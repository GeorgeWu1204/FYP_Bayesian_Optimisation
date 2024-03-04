# Cores-VeeR-EL2 Report

## 1. Parameter Selection

To briefly go through all the impacts of the parameters, experiments based on different benchmarks were conducted. Each trial only changes one parameter while keeping the others as the default values. The ratio of (max - min) / (number of instructions retired) for benchmarks results of each parameter and represented this data in the bar chart below. Parameters that showed no impact across all benchmarks were excluded.

![Parameter Selection](Core_Design_Space/Performance_of_Benchmarks_across_Different_Parameters.png)

## 2. Optimisation Set 1

For the first optimisation set. This optimisation set mainly focuses on the BTB and LSU parts. The corresponding design space size is 2x5x3x3 = 90 and the following parameters were selected:


| Parameter | Range | Description |
| --- | --- | --------------------------------------- |
| btb enabled | 0, 1 | Branch Target Buffer |
| btb size | 32, 64, 128, 256, 512 | Branch Target Buffer Size |
| lsu_num_nbload | 2, 4, 8 | Num of Non-blocking loads executed by the Load Store Unit (LSU) |
| lsu_stbuf_depth | 2, 4, 8 | Depth of the store buffer within the LSU |

The output objective is 
| Objective | Optimisation Direction | Range |
| --- | --- | --- |
| mcycle for cmark | Minimise | 400000 - 420000 |
| mcycle for dhrystone | Minimise | 350000 - 370000 |
| LUT as Logic | Constraints | 30000 - 33000 |



BTB Impact Analysis:

<p>
  <img src="Core_Design_Space/Figures/BTB_Size_analysis.png" alt="BTB Size" style="width: 48%; display: inline-block;" />
  <img src="Core_Design_Space/Figures/BTB_Enable_analysis.png" alt="BTB Enable" style="width: 48%; display: inline-block;" />
</p>

LSU Impact Analysis:

<p>
  <img src="Core_Design_Space/Figures/LSU_num_nbload_analysis.png" alt="BTB Size" style="width: 48%; display: inline-block;" />
  <img src="Core_Design_Space/Figures/LSU_stbuf_depth_analysis.png" alt="BTB Enable" style="width: 48%; display: inline-block;" />
</p>


## 3. Optimisation Set 2

For the second optimisation set. This optimisation set mainly focuses on the ICCM and DCCM parts. The corresponding design space size is 2x5x3x3 = 90 and the following parameters were selected:
