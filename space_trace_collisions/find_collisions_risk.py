from sgp4.api import Satrec, days2mdhms # type: ignore
from .utils import calc_distance, load_json, save_json, load_pickle
from .config import Config
from typing import Tuple, List, Dict, TypedDict
import time
from .julian_dates import JulianDate, difference_in_time_in_seconds, get_midpoint_time, add_time, julian_date_to_datetime

TIME_FRAME = 15 * 60 # 10 minutes

def distance_between_satellites (sat1, sat2, time: JulianDate) -> float:
  e1, r1, v1  = sat1.sgp4(time[0], time[1])
  e2, r2, v2 = sat2.sgp4(time[0], time[1])

  return calc_distance(r1[0], r1[1], r1[2], r2[0], r2[1], r2[2])

def binary_search (sat1, sat2, at_time_1: JulianDate, at_time_2: JulianDate) -> Tuple[JulianDate, float]:

  # print ('binary', at_time_1, at_time_2, difference_in_time_in_seconds(at_time_1, at_time_2))

  if abs(difference_in_time_in_seconds(at_time_1, at_time_2)) < 1:
    return (at_time_1, distance_between_satellites(sat1, sat2, at_time_1))

  mid_time = get_midpoint_time(at_time_1, at_time_2)
  mid_dist = distance_between_satellites(sat1, sat2, mid_time)
  
  left_time = add_time(mid_time, -1)
  left_distance = distance_between_satellites(sat1, sat2, left_time)

  if left_distance < mid_dist:
    return binary_search(sat1, sat2, at_time_1, mid_time)
  else:
    return binary_search(sat1, sat2, mid_time, at_time_2)


def do_simple_search(sat1, sat2, start_time: JulianDate, end_time: JulianDate) -> Tuple[JulianDate, float]:
  current_time = start_time
  min_distance = 10e10
  counter = 0
  while current_time < end_time:
    distance = distance_between_satellites(sat1, sat2, current_time)
    # if counter % 100 == 0:
      # print ('at_time', current_time, 'distance', distance)
    if distance < min_distance:
      min_distance = distance
      min_distance_time = current_time
    current_time = add_time(current_time, .5)
    counter += 1
  return (min_distance_time, min_distance)


def find_min_distance (sat1, sat2, at_time: JulianDate) -> Tuple[JulianDate, float]:

  # subtract 10 minutes from the start time in julian date format
  start_time = add_time(at_time, -10 * 60)
  end_time = add_time(at_time, 10 * 60)
  
  return binary_search(sat1, sat2, start_time, end_time)


class CollisionInit(TypedDict):
    date: str
    sat_1_id: str
    sat_2_id: str
    min_distance: float
    julian_date: float  # Assuming min_distance_time is a tuple of floats
    sat_1_xyz: str
    sat_2_xyz: str

class CollisionOutEvent(TypedDict):
    date: str
    julian_date: float  # Assuming min_distance_time is a tuple of floats
    min_distance: float

class CollisionOut(TypedDict):
    sat_1_id: str
    sat_2_id: str
    sat_1_xyz: str
    sat_2_xyz: str
    collisions: List[CollisionOutEvent]

def find_closest_collisions(collision_data: Dict[str, List[List[str]]], sat_data: List[Dict[str, str]], config: Config) -> List[CollisionOut]:
  
  sat_data_lookup = {}
  for sat in sat_data:
    sat_data_lookup[sat['OBJECT_ID']] = sat


  print ('total keys', len(collision_data))

  collisions: List[CollisionInit] = []
  counter = 0
  for key in collision_data:
    counter += 1
    # if counter == 10:
    #   break
    for (sat_1_id, sat_2_id) in collision_data[key]:
      
      sat_1_data = sat_data_lookup[sat_1_id]
      sat_2_data = sat_data_lookup[sat_2_id]

      sat_1 = Satrec.twoline2rv(sat_1_data['TLE_LINE1'], sat_1_data['TLE_LINE2'])    
      sat_2 = Satrec.twoline2rv(sat_2_data['TLE_LINE1'], sat_2_data['TLE_LINE2'])

      split_key = key.split('_')
      julian_date = (float(split_key[0]), float(split_key[1]))
      (min_distance_time, min_distance) = find_min_distance(sat_1, sat_2, julian_date)
      
      e, r1, v  = sat_1.sgp4(min_distance_time[0], min_distance_time[1])
      e, r2, v  = sat_2.sgp4(min_distance_time[0], min_distance_time[1])

      sat_1_xyz = "X=" + str(r1[0]) + " Y=" + str(r1[1]) + " Z=" + str(r1[2])
      sat_2_xyz = "X=" + str(r2[0]) + " Y=" + str(r2[1]) + " Z=" + str(r2[2])

      collisions.append({
        'date': julian_date_to_datetime(min_distance_time).isoformat(),
        'sat_1_id': sat_1_id,
        'sat_2_id': sat_2_id,
        'min_distance': min_distance,
        'julian_date': min_distance_time[0] + min_distance_time[1],
        'sat_1_xyz': sat_1_xyz,
        'sat_2_xyz': sat_2_xyz
      })

  sorted_collisions = sorted(collisions, key=lambda x: x['min_distance'])
  
  # [:200]

  collision_lookup: Dict[Tuple[str, str], CollisionOut] = {}
  
  for collision in sorted_collisions:
    lookup = tuple(sorted([collision['sat_1_id'], collision['sat_2_id']]))
    if len(lookup) != 2:
      continue
    if lookup not in collision_lookup:
      collision_lookup[lookup] = {
        'sat_1_id': collision['sat_1_id'],
        'sat_2_id': collision['sat_2_id'],
        'sat_1_xyz': collision['sat_1_xyz'],
        'sat_2_xyz': collision['sat_2_xyz'],
        'collisions': [],
      }
      
    collision_lookup[lookup]['collisions'].append({
      'date': collision['date'],
      'julian_date': collision['julian_date'],
      'min_distance': collision['min_distance'],
    })

    collision_lookup[lookup]['collisions'].sort(key=lambda x: x['min_distance'])

  def get_min_distance(collision: CollisionOut):
    min_val = 10e10

    for collision_event in collision['collisions']:
      min_val = min(min_val, collision_event['min_distance'])
    return min_val

  return sorted(list(collision_lookup.values()), key=get_min_distance)[:100]






      # print (collision, min_distance)
      # collisions.append([
      #   julian_date_to_datetime(min_distance_time).isoformat(),
      #   sat_1_id,
      #   sat_2_id,
      #   min_distance,
      #   min_distance_time[0] + min_distance_time[1],
      #   sat_1_xyz,
      #   sat_2_xyz
      # ])

  # return sorted(collisions, key=lambda x: x[3])



if __name__ == '__main__':
  
  # "2,460,689.5_0.0"
  # [
  #   "2023-047A",
  #   "2023-047D",
  #   4.598756301532952
  # ],

        #   [
        #     "1973-081B",
        #     "1978-026FG",
        #     17.291773979182945
        # ],

  start_time = time.time()

  julian_date = (2460689.5, 0.0)
  sat_1_id = "2023-047A"
  sat_2_id = "2023-047D"

  # julian_date = (2460689.5, 0.0)
  # sat_1_id = "1973-081B"
  # sat_2_id = "1978-026FG"


  config = Config()
  # sat_data = load_json(config.SAT_JSON_PATH)
  sat_data = load_json(config.SAT_JSON_PATH)
  collision_data = load_pickle(config.COLLISIONS_PATH_PICKLE)

  collisions = find_closest_collisions(collision_data, sat_data, config)
  
  save_json(config.RISK_COLLISIONS_PATH, collisions)
  print (f"Time taken: {time.time() - start_time} seconds")
  
  
  # sat_1 = None
  # sat_2 = None



  # for sat in sat_data:
  #   if sat['OBJECT_ID'] == sat_1_id:
  #     sat_1 = Satrec.twoline2rv(sat['TLE_LINE1'], sat['TLE_LINE2'])
  #   elif sat['OBJECT_ID'] == sat_2_id:
  #     sat_2 = Satrec.twoline2rv(sat['TLE_LINE1'], sat['TLE_LINE2'])

  # after =  find_min_distance(sat_1, sat_2, julian_date)
  # print ('Initial', julian_date,add_time(julian_date, -TIME_FRAME), add_time(julian_date, TIME_FRAME))

  # print ('Before', julian_date, distance_between_satellites(sat_1, sat_2, julian_date))
  # print('After',after)
  # print ('Ideal time', do_simple_search(sat_1, sat_2, add_time(julian_date, -TIME_FRAME), add_time(julian_date, TIME_FRAME)))

