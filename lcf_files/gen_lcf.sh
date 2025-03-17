#!/bin/bash

ls /cvmfs/gwosc.osgstorage.org/gwdata/O3a/strain.4k/frame.v1/H1/*/*H1_GWOSC*gwf | lal_path2cache > h1_o3a_frames.lcf
ls /cvmfs/gwosc.osgstorage.org/gwdata/O3a/strain.4k/frame.v1/L1/*/*L1_GWOSC*gwf | lal_path2cache > l1_o3a_frames.lcf
ls /cvmfs/gwosc.osgstorage.org/gwdata/O3a/strain.4k/frame.v1/V1/*/*V1_GWOSC*gwf | lal_path2cache > v1_o3a_frames.lcf

ls /cvmfs/gwosc.osgstorage.org/gwdata/O3b/strain.4k/frame.v1/H1/*/*H1_GWOSC*gwf | lal_path2cache > h1_o3b_frames.lcf
ls /cvmfs/gwosc.osgstorage.org/gwdata/O3b/strain.4k/frame.v1/L1/*/*L1_GWOSC*gwf | lal_path2cache > l1_o3b_frames.lcf
ls /cvmfs/gwosc.osgstorage.org/gwdata/O3b/strain.4k/frame.v1/V1/*/*V1_GWOSC*gwf | lal_path2cache > v1_o3b_frames.lcf
