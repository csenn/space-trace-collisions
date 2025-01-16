from sgp4.api import jday  # type: ignore

class Config:
  RUN_TIME_MINUTES = 60 * 24 # 24 hours
  RUN_INTERVAL_MINUTES = 4 # 3 minutes
  COLLISION_DISTANCE = 100 # 100 km
  BOX_SIZE = 1200 # 2000 km box
  START_TIME = jday(2025, 1, 12, 0, 0, 0)

  SAT_JSON_PATH = './space_trace_collisions/data_in/satellites-api.json'
  COLLISIONS_PATH = './space_trace_collisions/data_cache/collisions.json'
  COLLISIONS_PATH_PICKLE = './space_trace_collisions/data_cache/collisions.pickle'

  RISK_COLLISIONS_PATH = './space_trace_collisions/data_out/risk-collisions.json'
  # SAT_TRAJECTORIES_PICKLE_PATH = './space_trace_collisions/data_out/sat_trajectories.pickle'

  