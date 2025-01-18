import time
from typing import List, Tuple, Set, Dict
from .config import Config
from .utils import load_json, save_json, save_pickle
from sgp4.api import Satrec # type: ignore
import numpy as np
from numpy.typing import NDArray
from .julian_dates import add_time
from multiprocessing import Pool, shared_memory
from .cluster_pair_analyzer import ClusterPairAnalyzer

def precompute_sat_locations(sat_data: List[Dict[str, str]], config: Config) -> Tuple[NDArray[np.float64], Dict[int, str], Dict[int, Tuple[float, float]]]:
  num_times = int(config.RUN_TIME_MINUTES / config.RUN_INTERVAL_MINUTES)
  num_sats = len(sat_data)

  # dicts to map indexes back to ids
  sat_id_lookup: Dict[int, str] = {}
  time_jd_lookup: Dict[int, Tuple[float, float]] = {}

  sat_locations = np.empty((num_sats, num_times, 3))
  for i, row in enumerate(sat_data):
    sat_id, tle_line1, tle_line2 = row['OBJECT_ID'], row['TLE_LINE1'], row['TLE_LINE2']
    sat_id_lookup[i] = sat_id
    sat_satrec = Satrec.twoline2rv(tle_line1, tle_line2)
     
    for x in range(0, num_times):
      seconds = x * config.RUN_INTERVAL_MINUTES * 60
      jd, fr = add_time(config.START_TIME, seconds)
      time_jd_lookup[x] = (jd, fr)
     
      e, r, v  = sat_satrec.sgp4(jd, fr)

      if e != 0:
          sat_locations[i, x] = [np.nan, np.nan, np.nan]
      else:
          sat_locations[i, x] = r

  return sat_locations, sat_id_lookup, time_jd_lookup

def process_time_index(args: Tuple[int, str, int, Config]) -> Set[Tuple[int, int]]:
    time_index, shm_name, num_sats, config = args

    # Create numpy array view of shared memory
    shm = shared_memory.SharedMemory(name=shm_name)

    # can use time_index + 1 because we dont need the whole ndarray only up to that index
    sat_array: NDArray[np.float64] = np.ndarray((num_sats, time_index+1, 3), dtype=np.float64, buffer=shm.buf)

    cluster_analyzer = ClusterPairAnalyzer(time_index, num_sats, sat_array, config)
    collision_pairs = cluster_analyzer.get_collision_pairs()

    shm.close()
    return collision_pairs


def build_clusters(sat_locations: NDArray[np.float64], num_sats: int, num_times: int, config: Config) -> List[Set[Tuple[int, int]]]:
    
  try:
    shm = shared_memory.SharedMemory(create=True, size=sat_locations.nbytes)
    shared_array: NDArray[np.float64] = np.ndarray(sat_locations.shape, dtype=sat_locations.dtype, buffer=shm.buf)
    np.copyto(shared_array, sat_locations)
    
    with Pool() as pool:
      pairs = pool.map(process_time_index, [(idx, shm.name, num_sats, config) for idx in range(num_times)])
      return pairs

  except Exception as e:
    print(f"An error occurred: {e}")
    raise e
  
  finally:
    # Clean up, will execute even with the return in the try block
    shm.close()
    shm.unlink()


def build_collision_out(rough_collisions: List[Set[Tuple[int, int]]], sat_id_lookup: Dict[int, str], time_jd_lookup_fr: Dict[int, Tuple[float, float]]) -> Dict[str, List[List[str]]]:
                 
  result: Dict[str, List[List[str]]] = {}

  for index, pairs in enumerate(rough_collisions):
    if len(pairs) == 0:
      continue
    time_key = str(time_jd_lookup_fr[index][0]) + "_" + str(time_jd_lookup_fr[index][1])
    result[time_key] = []
    for sat_id_1, sat_id_2 in pairs:
      result[time_key].append([sat_id_lookup[sat_id_1], sat_id_lookup[sat_id_2]])
  return result
  

def run_script() -> None:
  start_time = time.time()

  config = Config()
  sat_data = load_json(config.SAT_JSON_PATH)

  # Cleanup by removing UNKNOWN id
  sat_data = [row for row in sat_data if row['OBJECT_ID'] != 'UNKNOWN']
  
  sat_locations, sat_id_lookup, time_jd_lookup = precompute_sat_locations(sat_data, config)
  num_sats = len(sat_data)
  num_times = len(time_jd_lookup)

  print (f"Total sat position calculations: {num_sats * num_times}")
  print (f"Time taken to pre-compute sat positions: {time.time() - start_time} seconds")
  
  # Build clusters
  build_cluster_time = time.time()
  rough_collisions = build_clusters(sat_locations, num_sats, num_times, config)
  collisions_out = build_collision_out(rough_collisions, sat_id_lookup, time_jd_lookup )

  # save_json(config.COLLISIONS_PATH_NEW, collisions_out)
  save_pickle(config.COLLISIONS_PATH_PICKLE, collisions_out)

  print (f"Average collision count per time period: {sum(len(collisions) for collisions in rough_collisions) / len(rough_collisions)}")
  print (f"Time taken to find broad collisions: {time.time() - build_cluster_time} seconds")


if __name__ == '__main__':
  run_script()
