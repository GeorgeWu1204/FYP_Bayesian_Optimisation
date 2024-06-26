open_project EL2_Prj.xpr
reset_run synth_1
launch_runs synth_1 -jobs 12
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ../../Syn_Report/EL2_utilization_synth.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10 -input_pins -routable_nets -name timing_1 -file ../../Syn_Report/EL2_time_summary.rpt
close_project