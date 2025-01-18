import numpy as np
from .config import Config
from typing import Dict, List, Tuple, Set, Union, Callable
from .utils import calc_distance
from numpy.typing import NDArray

class ClusterPairAnalyzer:
  def __init__(self, time_index: int, num_sats: int, sat_array: NDArray[np.float64], config: Config):
    self.time_index = time_index
    self.num_sats = num_sats
    self.sat_array = sat_array
    self.config = config
    # self.clusters: Dict[Tuple[int, int, int], List[str]] = {}

  def get_sat_coords(self, sat_id: int) -> Tuple[float, float, float]:
    return self.sat_array[sat_id, self.time_index]

  def get_collision_pairs(self) -> Set[Tuple[int, int]]:
    clusters = self.build_clusters()

    all_at_risk_pairs: Set[Tuple[int, int]] = set()

    for cluster_key in clusters:
      x_index, y_index, z_index = cluster_key

      # include current cluster
      neighbors = [
        (x_index, y_index, z_index),
        (x_index + 1, y_index, z_index),
        (x_index - 1, y_index, z_index),
        (x_index, y_index + 1, z_index),
        (x_index, y_index - 1, z_index),
        (x_index, y_index, z_index + 1),
        (x_index, y_index, z_index - 1),
      ];

      all_cluster_ids = set()
      for neighbor in neighbors:
        if neighbor in clusters:
          all_cluster_ids.update(clusters[neighbor])

      close_pairs = self.get_at_risk_sat_pairs(list(all_cluster_ids))

      for (sat_1_id, sat_2_id) in close_pairs:
        data_1 = self.get_sat_coords(sat_1_id)
        data_2 = self.get_sat_coords(sat_2_id)

        if data_1 is None or data_2 is None:
          continue

        distance = calc_distance(data_1[0], data_1[1], data_1[2], data_2[0], data_2[1], data_2[2])

        if distance != 0:
          all_at_risk_pairs.add((sat_1_id, sat_2_id))          

    return all_at_risk_pairs

  def build_clusters(self) -> Dict[Tuple[int, int, int], Set[int]]:
    clusters: Dict[Tuple[int, int, int], Set[int]] = {}

    for sat_id in range(self.num_sats):
      # sat_data = self.sat_trajectories.get_satellite_data_at_time(sat_id, self.at_time)
      sat_data = self.get_sat_coords(sat_id)
      
      # Will be None if there was an error with the satrec calculation
      if sat_data is None:
        continue

      cluster_key = self.build_cluster_key(sat_data[0], sat_data[1], sat_data[2])
      
      if cluster_key not in clusters:
        clusters[cluster_key] = set()

      clusters[cluster_key].add(sat_id)

    return clusters
    
  def build_cluster_key(self, x: float, y: float, z: float) -> Tuple[int, int, int]:
    if np.isnan(x):
      return (0, 0, 0)
  
    x_index = int(x // self.config.BOX_SIZE)
    y_index = int(y // self.config.BOX_SIZE)
    z_index = int(z // self.config.BOX_SIZE)
    return (x_index, y_index, z_index)
  

  # This takes in a list of satellites ids located within a cluster region, say 2000km
  # and returns a set of pairs of satellites that are within the collision distance
  # it uses the prune-and-sweep algorithm to find the pairs by checking each dimension
  # independently and then intersecting the results
  def get_at_risk_sat_pairs(self, sat_ids: List[int]):
    

    x_coords = []
    y_coords = []
    z_coords = []
    for sat_id in sat_ids:
      coords = self.get_sat_coords(sat_id)
      if coords is None:
        continue
      x_coords.append((sat_id, coords[0]))
      y_coords.append((sat_id, coords[1]))
      z_coords.append((sat_id, coords[2]))

    pairs_x = self.get_dimension_pairs(x_coords)
    pairs_y = self.get_dimension_pairs(y_coords)
    pairs_z = self.get_dimension_pairs(z_coords)

    return pairs_x.intersection(pairs_y).intersection(pairs_z)

  # Finds whether two satellites are within the collision distance on each dimension
  # This is done by sorting the satellites by their dimension value and then checking
  # if the distance between the two satellites is less than the collision distance
  def get_dimension_pairs(self, sat_dims: List[Tuple[int, float]]) -> Set[Tuple[int, int]]:

    sorted_sat_dims = sorted(sat_dims, key=lambda x: x[1])

    pairs: Set[Tuple[int, int]] = set()

    for i in range(len(sorted_sat_dims) - 1):
      val_id, val_dist = sorted_sat_dims[i]
      for j in range(i + 1, len(sorted_sat_dims)):
        next_val_id, next_val_dist = sorted_sat_dims[j]
        if next_val_dist - val_dist <= self.config.COLLISION_DISTANCE:
          pair = tuple(sorted([val_id, next_val_id]))
          if len(pair) == 2:
            pairs.add(pair)        
        else:
          break

    return pairs