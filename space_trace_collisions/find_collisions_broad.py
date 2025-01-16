import time
from .satellite_trajectories import SatelliteTrajectories
from .cluster_group import ClusterGroup
from typing import List, Callable, Union, Tuple, Set, Dict
from .config import Config
from .utils import load_json, save_json, save_pickle
from concurrent.futures import ProcessPoolExecutor


def find_broad_collisions(sat_trajectories: SatelliteTrajectories, config: Config) -> Dict[Tuple[float, float], Set[Tuple[str, str]]]:
  res: Dict[Tuple[float, float], Set[Tuple[str, str]]] = {}

  for i in range(len(sat_trajectories.times)):
    at_time = sat_trajectories.times[i]
    cluster_group = ClusterGroup(at_time, sat_trajectories, config)
    res[at_time] = cluster_group.get_collision_pairs()

  return res

# def find_broad_collisions(sat_trajectories: SatelliteTrajectories, config: Config) -> Dict[Tuple[float, float], Set[Tuple[str, str]]]:
#     res: Dict[Tuple[float, float], Set[Tuple[str, str]]] = {}

#     def process_time(i):
#         at_time = sat_trajectories.times[i]
#         cluster_group = ClusterGroup(at_time, sat_trajectories, config)
#         return at_time, cluster_group.get_collision_pairs()

#     with ProcessPoolExecutor(max_workers=8) as executor:
#         results = executor.map(process_time, range(len(sat_trajectories.times)))

#     for at_time, collision_pairs in results:
#         res[at_time] = collision_pairs

#     return res

# def process_time(i, sat_trajectories, config):
#     at_time = sat_trajectories.times[i]
#     cluster_group = ClusterGroup(at_time, sat_trajectories, config)
#     return at_time, cluster_group.get_collision_pairs()

# def find_broad_collisions(sat_trajectories: SatelliteTrajectories, config: Config) -> Dict[Tuple[float, float], Set[Tuple[str, str]]]:
#     res: Dict[Tuple[float, float], Set[Tuple[str, str]]] = {}

#     with ProcessPoolExecutor() as executor:
#         results = executor.map(lambda i: process_time(i, sat_trajectories, config), range(len(sat_trajectories.times)))

#     for at_time, collision_pairs in results:
#         res[at_time] = collision_pairs

#     return res

# {"2460687_0.5": [["2007-026A", "2010-030A"]],
def build_collision_out(rough_collisions: Dict[Tuple[float, float], Set[Tuple[str, str]]], sat_trajectories: SatelliteTrajectories) -> Dict[str, List[List[str]]]:
                 
  result: Dict[str, List[List[str]]] = {}

  for time in rough_collisions:
    if len(rough_collisions[time]) == 0:
      continue
    time_key = str(time[0]) + "_" + str(time[1])
    result[time_key] = []
    for sat_id_1, sat_id_2 in rough_collisions[time]:
      result[time_key].append([sat_id_1, sat_id_2])
  return result
  

def run_script() -> None:
  start_time = time.time()

  config = Config()

  satellite_data = load_json(config.SAT_JSON_PATH)

  sat_trajectories = SatelliteTrajectories(config)
  sat_trajectories.build_satellite_trajectories(satellite_data)
  print ('Time to build satellite trajectories: ', time.time() - start_time)

  collision_start_time = time.time()
  rough_collisions = find_broad_collisions(sat_trajectories, config)
  print ('Time to calculate collisions: ', time.time() - collision_start_time)
    
  collisions_out = build_collision_out(rough_collisions, sat_trajectories)
  save_json(config.COLLISIONS_PATH, collisions_out)
  save_pickle(config.COLLISIONS_PATH_PICKLE, collisions_out)



  all_pairs: Set[Tuple[str, str]] = set()
  for t in rough_collisions:
    all_pairs.update(rough_collisions[t])

  end_time = time.time()
  print ("Total satellites: ", len(satellite_data))
  print ("Time Interval in minutes: ", config.RUN_INTERVAL_MINUTES)
  print ("Time Steps", len(sat_trajectories.times))
  print ('Total collisions: ', sum(len(rough_collisions[time]) for time in rough_collisions))
  print ("Total pairs: ", len(all_pairs))
  print (f"Time taken: {end_time - start_time} seconds")

if __name__ == '__main__':
  run_script()
