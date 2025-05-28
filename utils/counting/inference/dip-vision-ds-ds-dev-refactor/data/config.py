from typing import Dict
import os
import yaml
from exceptions import ConfigFileNotFound
import json

def check_cfg_exists(cfg_path: str) -> None:
    
    if cfg_path is None:
        raise ConfigFileNotFound('Config file cannot be None.')

    if not os.path.exists(cfg_path):
        raise ConfigFileNotFound('Config file {cfg_path} does not exist.')

def read_yaml_config(cfg_path: str) -> Dict:

    check_cfg_exists(cfg_path)

    with open(cfg_path, 'r') as f:
        data = yaml.safe_load(f)

    return data

def read_json_config(cfg_path: str) -> Dict:

    check_cfg_exists(cfg_path)

    with open(cfg_path, 'r') as f:
        data = json.load(f)

    return data

def read_cam_config(cfg_path: str) -> Dict:

    # ------- CHECK ALL PERMUTATIONS FOR CONFIG FILE -------
    if not cfg_path.endswith('.yaml'):
        cfg_path = cfg_path+'.yaml'

    if not os.path.exists(cfg_path):
        cfg_path = os.path.join('cfg/camera-cfg', cfg_path)
    # ------------------------------------------------------

    data = read_yaml_config(cfg_path)

    return data