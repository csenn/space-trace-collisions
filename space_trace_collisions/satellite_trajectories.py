from sgp4.api import Satrec, jday, SGP4_ERRORS  # type: ignore
from typing import List, Tuple, Dict, Union
from .config import Config
from .julian_dates import add_time, JulianDate

"""
times: [1, 2, 3, 4]
satellites: {
  "sat1": [(1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6)],
  "sat2": [(1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6)],
  "sat3": [(1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6)]
}
"""

class SatelliteTrajectories:
  def __init__(self, config: Config):
    self.config = config
    self.times: List[Tuple[float, float]] = []
    self._times_map: Dict[Tuple[float, float], int] = {}
    self.satellites: Dict[str, List[Union[Tuple[float, float, float, float, float, float] , None]]] = {}

  # def get_satellite_data_at_time_index(self, sat_id: str, time_index: int) -> Union[Tuple[float, float, float, float, float, float] , None]:
  #   return self.satellites[sat_id][time_index]
  
  def get_satellite_data_at_time(self, sat_id: str, time_stamp: JulianDate) -> Union[Tuple[float, float, float, float, float, float] , None]:
    time_index = self._times_map[time_stamp]
    return self.satellites[sat_id][time_index]

  def build_satellite_trajectories(self, satellite_data: List[Dict[str, str]]) -> None:
    
    iterations = int(self.config.RUN_TIME_MINUTES / self.config.RUN_INTERVAL_MINUTES)

    for x in range(0, iterations):
      seconds = x * self.config.RUN_INTERVAL_MINUTES * 60
      jd, fr = add_time(self.config.START_TIME, seconds)
      self.times.append((jd, fr))
      self._times_map[(jd, fr)] = x
      for satellite_row in satellite_data:
        sat_id = satellite_row['OBJECT_ID']
          
        if sat_id == 'UNKNOWN':
          continue

        if sat_id not in self.satellites:
          self.satellites[sat_id] = []

        satellite = Satrec.twoline2rv(satellite_row['TLE_LINE1'], satellite_row['TLE_LINE2'])
        
        e, r, v  = satellite.sgp4(jd, fr)

        if e != 0:
          # print ("There was an error with ", e, sat_id)
          self.satellites[sat_id].append(None)

        else:
          sat_data = (r[0], r[1], r[2], v[0], v[1], v[2])
          self.satellites[sat_id].append(sat_data)

