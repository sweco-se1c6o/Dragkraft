function export_matlab_baseline(outputDir, legacyDir)
%EXPORT_MATLAB_BASELINE Run the legacy default scenario and write CSV fixtures.
%
% This is intentionally non-invasive: it runs old/dragkraft.m in MATLAB's
% workspace and exports the resulting arrays without modifying legacy files.

if nargin < 1 || isempty(outputDir)
    thisFile = mfilename('fullpath');
    repoRoot = fileparts(fileparts(thisFile));
    outputDir = fullfile(repoRoot, 'tests', 'fixtures', 'matlab_nyprofil_default');
else
    repoRoot = fileparts(fileparts(mfilename('fullpath')));
end

if nargin < 2 || isempty(legacyDir)
    legacyDir = fullfile(repoRoot, 'old');
end
if ~exist(legacyDir, 'dir')
    error('Legacy source directory not found: %s', legacyDir);
end
if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end

previousDir = pwd;
cleanup = onCleanup(@() cd(previousDir));
cd(legacyDir);
set(0, 'DefaultFigureVisible', 'off');
run('dragkraft.m');
close all;

write_summary(fullfile(outputDir, 'summary.csv'), tid, hastighetsprofil, timingPoint, mbTid);
write_timing_points(fullfile(outputDir, 'timing_points.csv'), timingPoint, timingPointName, tidc);
write_speed_profile(fullfile(outputDir, 'speed_profile.csv'), hastighetsprofil, tid, tidc, ekvLutning, kurvKraft);
write_block_occupation(fullfile(outputDir, 'block_occupation.csv'), mbName, mbPos, mbTid);
end

function write_summary(path, tid, hastighetsprofil, timingPoint, mbTid)
fid = fopen(path, 'w');
if fid < 0
    error('Could not open %s', path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'key,value\n');
fprintf(fid, 'total_time_s,%.15g\n', sum(tid));
fprintf(fid, 'route_length_m,%d\n', numel(hastighetsprofil));
fprintf(fid, 'timing_point_count,%d\n', numel(timingPoint));
fprintf(fid, 'block_count,%d\n', size(mbTid, 1));
end

function write_timing_points(path, timingPoint, timingPointName, tidc)
fid = fopen(path, 'w');
if fid < 0
    error('Could not open %s', path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'position_m,name,time_s\n');
for index = 1:numel(timingPoint)
    fprintf(fid, '%d,%s,%.15g\n', timingPoint(index), csv_text(timingPointName{index}), tidc(timingPoint(index)));
end
end

function write_speed_profile(path, hastighetsprofil, tid, tidc, ekvLutning, kurvKraft)
fid = fopen(path, 'w');
if fid < 0
    error('Could not open %s', path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'position_m,speed_mps,time_s_per_m,cumulative_time_s,equivalent_gradient,curve_force_n\n');
for position = 1:numel(hastighetsprofil)
    fprintf(fid, '%d,%.15g,%.15g,%.15g,%.15g,%.15g\n', ...
        position, hastighetsprofil(position), tid(position), tidc(position), ekvLutning(position), kurvKraft(position));
end
end

function write_block_occupation(path, mbName, mbPos, mbTid)
fid = fopen(path, 'w');
if fid < 0
    error('Could not open %s', path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'name,signal_position_m,speed_difference_mps,intersection_position_m,booking_time_s,arrival_time_s,release_time_s\n');
for index = 1:size(mbTid, 1)
    fprintf(fid, '%s,%d,%.15g,%.15g,%.15g,%.15g,%.15g\n', ...
        csv_text(mbName{index}), mbPos(index), mbTid(index, 1), mbTid(index, 2), mbTid(index, 3), mbTid(index, 4), mbTid(index, 5));
end
end

function text = csv_text(value)
text = char(value);
text = strrep(text, '"', '""');
if ~isempty(strfind(text, ',')) || ~isempty(strfind(text, '"'))
    text = ['"', text, '"'];
end
end
