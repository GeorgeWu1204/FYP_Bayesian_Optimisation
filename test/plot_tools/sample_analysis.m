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
iteration_num = 25;
X = A(:, 3); % Third last column
% END: ed8c6549bwf9
Y = A(:, 4); % Second last column
Z = A(:, 2); % Last column
% C = A(:, 2); % Second column (objective value)

Index_array = 1:1:iteration_num + 1;


% texts
X_text = loaded_data.textdata(1, 3);
Y_text = loaded_data.textdata(1, 4);
Z_text = loaded_data.textdata(1, 2);
% plot initial points
scatter3(X(1:end - iteration_num), Y(1:end - iteration_num), Z(1:end - iteration_num), 36, 'black', 'filled');

hold on; 


% Plot the rest of the 3-D points according to the scalar C
% scatter3(X(start_position+1:end), Y(start_position+1:end), Z(start_position+1:end), 36, C(start_position+1:end), 'filled');


% % Create the 3D scatter plot
% scatter3(X, Y, Z, 36, Index_array', 'filled');
scatter3(X(end - iteration_num+1:end), Y(end - iteration_num+1:end), Z(end - iteration_num+1:end), 36, Index_array(end - iteration_num+1:end), 'filled');

% Add color bar to indicate the scale of the objective values
colorbar;

% Label the axes
xlabel(X_text);
ylabel(Y_text);
zlabel(Z_text);
% title('3D Scatter Plot of Objective Value by Input Variables');