# Space Trace Collisions

Python project that powers the UI at: https://github.com/csenn/space-trace

Uses [SGP4](https://pypi.org/project/sgp4/) library to find potential satellite collisions that would need to be examined more carefully using date from [space-track.org](https://www.space-track.org/).

How the algorithm works:
- Step 1 - Load json data and pre-compute all satellite positions 
every 3 minutes for 24 hours using SGP4 library. Default to around 30,000 every 4 minutes for 24 hours. Use numpy ND array to store computations.
- Step 2 - For each time step, build a "cluster" of satellites. For instance, find all satellites within a 1000 km 3D region (at each 4 minute period). Parallelize computation for speed.
- Step 3 - Find all satellites within the clusters immediately next to current cluster to take care of satellites located near cluster boundaries
- Step 4 - Use the prune and sweep algorithm to find satellites that are close to each other within each cluster by checking each individual dimension, and then doing a set intersection to ensure all 3 dimensions are close
- Step 5 clean up 0 distance satellites because these are likely duplicated data points
- Step 6 - after doing the "broad" stage and finding the possible set of collisions, we can then filter down more. We take each target satellite pair at each time, and then use a binary search technique to find the local minimum of distance between the two satellites. 
- Step 7 - Sort by closest collision distance and export in convenient JSON format.

Possible Improvements
- Make a cli tool and make arguments configurable outside changing the config object
- Investigate using newer sgp4-x algorithm hosted on space-track.org 
- Could be parallelized using Dask or equivalent at even larger scale (https://www.dask.org/)