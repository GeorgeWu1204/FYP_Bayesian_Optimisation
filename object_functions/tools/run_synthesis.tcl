open_project d:/Imperial/Year4/MasterThesis/FYP_Bayesian_Optimisation/object_functions/NutShell_Prj/NutShell_Prj.xpr
reset_run synth_1
launch_runs synth_1 -jobs 32
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file d:/Imperial/Year4/MasterThesis/FYP_Bayesian_Optimisation/object_functions/Syn_Report/NutShell_utilization_synth.rpt
close_project