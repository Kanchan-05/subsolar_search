#!/bin/bash

# Read in the times from the input file
times=()
while read -r line; do
  times+=("$line")
done < $2

# Initialize the start and end times
start_time=${times[0]}
end_time=""

# Create an array to hold the start-time and end-time key-value pairs
time_pairs=()

# Loop through the remaining times and group them into pairs
for (( i=1; i<${#times[@]}; i++ )); do
  if [[ -z "$end_time" ]]; then
    # This is the first time in a pair, so just store it as the start time
    start_time=${times[$i]}
  else
    # This is the second time in a pair, so create a new key-value pair
    # with the previous time as the start time and this time as the end time
    time_pairs+=("start-time = $start_time")
    time_pairs+=("end-time = ${times[$i]}")

    # Clear the end_time variable so we start a new pair
    end_time=""
  fi

  # Check if the current time is consecutive with the previous time
  if (( ${times[$i]} == $((end_time + 1)) )); then
    end_time=${times[$i]}
  else
    # The current time is not consecutive with the previous time, so
    # store the previous time as the end time and start a new pair
    if [[ -n "$end_time" ]]; then
      time_pairs+=("start-time = $start_time")
      time_pairs+=("end-time = $end_time")
    fi

    start_time=${times[$i]}
    end_time=""
  fi
done

# If we still have an end time left over, create a final key-value pair
if [[ -n "$end_time" ]]; then
  time_pairs+=("start-time = $start_time")
  time_pairs+=("end-time = $end_time")
fi

# Write out the time pairs to the output file
printf '%s\n' "${time_pairs[@]}" > $1 

