open_project rocket_chip.xpr
reset_run synth_1
launch_runs synth_1 -jobs 12
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ../../Syn_Report/rocket_utilization_synth.rpt
close_project