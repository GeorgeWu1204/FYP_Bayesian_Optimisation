create_project EL2_Prj /home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/Vivado_Prj/rocket_chip -part xczu19eg-ffvc1760-2-i
add_files -norecurse /home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/rocket-chip/vsim/generated-src/freechips.rocketchip.system.DefaultFPGAConfig.v
update_compile_order -fileset sources_1
set_property top ExampleRocketSystem [current_fileset]
add_files -norecurse /home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/rocket-chip/vsim/generated-src/freechips.rocketchip.system.DefaultFPGAConfig/plusarg_reader.v
add_files -norecurse /home/hw1020/Documents/FYP_Bayesian_Optimisation/object_functions/rocket-chip/vsim/generated-src/freechips.rocketchip.system.DefaultFPGAConfig.behav_srams.v