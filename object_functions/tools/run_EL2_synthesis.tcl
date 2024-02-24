open_project EL2_Prj.xpr
reset_run synth_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ../../Syn_Report/EL2_utilization_synth.rpt
close_project