# Space Trace Collisions

Python project that powers the UI at: https://github.com/csenn/space-trace

Uses [SGP4](https://pypi.org/project/sgp4/) library to find potential satellite collisions that would need to be examined more carefully using date from [space-track.org](https://www.space-track.org/).

How the algorithm works:
- Step 1 - Load json data and pre-compute all satellite positions 
every 3 minutes for 24 hours using SGP4 library. With around 30,000 satellites this operation takes around 30 seconds on my machine.
- Step 2 - For each time step, build a local "cluster" of satellites. For instance, find all satellites within a 1000 km area (at each 3 minute period). 
- Step 3 - Find all satellites within the clusters immediately next to current cluster to take care of satellites in different clusters but close to each other
- Step 4 - Use the prune and sweep algorithm to find satellites that are close to each other by checking each individual dimension is with 100km of each other, and then doing a set intersection to ensure all 3 dimensions are close
- Step 5 clean up 0 distance satellites because these are likely duplicated data points

