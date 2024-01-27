clear;
close all;
clc;

%% Load data
filename = '../test_results/estimated_clock_period_ncycles_dijkstra_record_input.txt';
delimiterIn = ',';
headerlinesIn = 1;
loaded_data = importdata(filename,delimiterIn,headerlinesIn);
A = loaded_data.data;

% Assuming A is your data matrix
% FILEPATH: /d:/Imperial/Year4/MasterThesis/FYP_Bayesian_Optimisation/test/plot_tools/sample_analysis.m
% BEGIN: ed8c6549bwf9
start_position = 1;
X = A(start_position:end, 3); % Third last column
% END: ed8c6549bwf9
Y = A(start_position:end, 4); % Second last column
Z = A(start_position:end, 5); % Last column
C = A(start_position:end, 2); % Second column (objective value)

Index_array = start_position:1:length(X)+start_position-1;


% texts
X_text = loaded_data.textdata(1, 3);
Y_text = loaded_data.textdata(1, 4);
Z_text = loaded_data.textdata(1, 5);

scatter3(X(1:start_position), Y(1:start_position), Z(1:start_position), 36, 'r', 'filled');

hold on; % Hold on to plot more data on the same figure
% Plot the rest of the points according to the scalar C
scatter3(X(start_position+1:end), Y(start_position+1:end), Z(start_position+1:end), 36, C(start_position+1:end), 'filled');


% % Create the 3D scatter plot
% scatter3(X, Y, Z, 36, Index_array', 'filled');

% Add color bar to indicate the scale of the objective values
colorbar;

% Label the axes
xlabel(X_text);
ylabel(Y_text);
zlabel(Z_text);
% title('3D Scatter Plot of Objective Value by Input Variables');