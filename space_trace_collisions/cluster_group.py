from .satellite_trajectories import SatelliteTrajectories
from .config import Config
from typing import Dict, List, Tuple, Set, Union, Callable
from .julian_dates import JulianDate
from .utils import calc_distance

class ClusterGroup:
  def __init__(self, at_time: JulianDate, sat_trajectories: SatelliteTrajectories, config: Config):
    self.at_time = at_time
    self.sat_trajectories = sat_trajectories
    self.config = config
    # self.clusters: Dict[Tuple[int, int, int], List[str]] = {}


  def get_collision_pairs(self) -> Set[Tuple[str, str]]:
    clusters = self.build_clusters()

    all_at_risk_pairs: Set[Tuple[str, str]] = set()

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

      all_at_risk_pairs.update(self.get_at_risk_sat_pairs(list(all_cluster_ids)))

    final_pairs: Set[Tuple[str, str]] = set()
    # remove all pairs with a distance of 0 because that means there is some issue 
    # with data duplication
    for (sat_1_id, sat_2_id) in all_at_risk_pairs:
      data_1 = self.sat_trajectories.get_satellite_data_at_time(sat_1_id, self.at_time)
      data_2 = self.sat_trajectories.get_satellite_data_at_time(sat_2_id, self.at_time)

      if data_1 is None or data_2 is None:
        all_at_risk_pairs.remove((sat_1_id, sat_2_id))
        continue

      distance = calc_distance(data_1[0], data_1[1], data_1[2], data_2[0], data_2[1], data_2[2])

      if distance != 0:
        final_pairs.add((sat_1_id, sat_2_id))          

    return final_pairs

  def build_clusters(self) -> Dict[Tuple[int, int, int], Set[str]]:
    clusters: Dict[Tuple[int, int, int], Set[str]] = {}

    for sat_id in self.sat_trajectories.satellites:
      sat_data = self.sat_trajectories.get_satellite_data_at_time(sat_id, self.at_time)
      
      # Will be None if there was an error with the satrec calculation
      if sat_data is None:
        continue

      cluster_key = self.build_cluster_key(sat_data[0], sat_data[1], sat_data[2])
      
      if cluster_key not in clusters:
        clusters[cluster_key] = set()

      clusters[cluster_key].add(sat_id)

    return clusters
    
  def build_cluster_key(self, x: float, y: float, z: float) -> Tuple[int, int, int]:
    x_index = int(x // self.config.BOX_SIZE)
    y_index = int(y // self.config.BOX_SIZE)
    z_index = int(z // self.config.BOX_SIZE)
    return (x_index, y_index, z_index)
  

  # This takes in a list of satellites ids located within a cluster region, say 2000km
  # and returns a set of pairs of satellites that are within the collision distance
  # it uses the prune-and-sweep algorithm to find the pairs by checking each dimension
  # independently and then intersecting the results
  def get_at_risk_sat_pairs(self, sat_ids: List[str]):
    
    def get_value(sat_id: str, dimension: int) -> Union[float, None]:
      data = self.sat_trajectories.get_satellite_data_at_time(sat_id, self.at_time)
      if data is None:
        return None
      return data[dimension]    

    pairs_x = self.get_dimension_pairs(sat_ids, lambda x: get_value(x, 0))
    pairs_y = self.get_dimension_pairs(sat_ids, lambda x: get_value(x, 1))
    pairs_z = self.get_dimension_pairs(sat_ids, lambda x: get_value(x, 2))

    return pairs_x.intersection(pairs_y).intersection(pairs_z)

  # Finds whether two satellites are within the collision distance on each dimension
  # This is done by sorting the satellites by their dimension value and then checking
  # if the distance between the two satellites is less than the collision distance
  def get_dimension_pairs(self, sat_ids: List[str], get_value: Callable[[str], Union[float, None]]) -> Set[Tuple[str, str]]:
    
    sat_dims: List[Tuple[str, float]] = []  
    for cluster_id in sat_ids:
      val = get_value(cluster_id)
      if val is None:
        continue
      sat_dims.append((cluster_id, val))

    sorted_sat_dims = sorted(sat_dims, key=lambda x: x[1])

    pairs: Set[Tuple[str, str]] = set()

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