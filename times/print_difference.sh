end=$(awk '{print $3}' $1 | sed -n '3p')
start=$(awk '{print $3}' $1 | sed -n '2p')

diff=$((end-start))
result=$(bc -l <<< "$diff/86400")
echo "Time in days $result"
