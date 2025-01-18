import json
import pickle
from typing import List, Dict

def calc_distance(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
  return ((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) ** 0.5

def load_json(json_path):
  with open(json_path, 'r') as file:
    return json.load(file)    

def save_json(json_path, data) -> None:
  with open(json_path, 'w') as file:
    json.dump(data, file)

def save_pickle(json_path, data) -> None:
  with open(json_path, 'wb') as file:
    pickle.dump(data, file)

def load_pickle(json_path):
  with open(json_path, 'rb') as file:
    return pickle.load(file)    