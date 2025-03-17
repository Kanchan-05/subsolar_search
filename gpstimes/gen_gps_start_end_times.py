from pycbc import dq 
from pycbc.events.veto import segments_to_start_end   
from ligo.segments import *  

# Define the start and end GPS times for querying data
start_time = 1253977218
end_time = 1338166018

# Query active data segments for H1 and L1 detectors
hsegs = dq.query_flag('H1', 'DATA', start_time, end_time)
lsegs = dq.query_flag('L1', 'DATA', start_time, end_time)

# Print the duration of active segments for H1 and L1
print("H1 Active Duration:", abs(hsegs))
print("L1 Active Duration:", abs(lsegs))

# Create a full time span segment and calculate inactive segments
span = segmentlist([(start_time, end_time)])
hoff = span - hsegs  
loff = span - lsegs 
# Placeholder for additional vetoes, set to loff for now
voff = loff  

# Combine inactive periods
off = hoff & loff & voff

# Define target duration (e.g., 2 days in seconds)
target_duration = 86400 * 2
# Initialize index and list for valid data bounds
j, bounds = 0, []  
start = start_time

# Partition data into valid chunks of approximately `target_duration`
while start < end_time:
    dur = 0
    tspan = None

    # Accumulate active segment duration within the target range
    while dur < target_duration and j < len(off):
        stop = off[j][1]  # Current off-segment stop time
        tspan = segmentlist([segment(start, stop)])
        # Active duration within the span
        dur = abs(hsegs & lsegs & tspan)  
        j += 1

    # Store the valid segment and update start for the next iteration
    if tspan:
        bounds.append(tspan)
        start = off[j-1][1] if j > 0 else end_time  # Avoid index errors

        # Print segment details
        print(
            f"Segment: {tspan}, Active Duration: {dur / 86400:.2f} days, "
            f"Span Duration: {abs(tspan) / 86400:.2f} days"
        )

# Merge the last segment with the previous one to ensure continuity
if len(bounds) > 1:
    bounds[-2] = bounds[-1] | bounds[-2]
    bounds.pop()  # Remove the last segment after merging

# Template for output configuration files
config_template = """
[workflow]
start-time = {}
end-time = {}
"""

# Write valid segments to configuration files
for idx, bound in enumerate(bounds):
    start, stop = bound[0]
    with open(f'gps_times_O3b_analysis_{idx}.ini', 'w') as f:
        f.write(config_template.format(start, stop))