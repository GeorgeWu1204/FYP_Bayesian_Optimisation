open_project NutShell_Prj.xpr
reset_run synth_1
launch_runs synth_1 -jobs 32
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ../Syn_Report/NutShell_utilization_synth.rpt
close_project