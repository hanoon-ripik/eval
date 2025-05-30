from datetime import datetime

cam_to_ccm_mapping = {
    203: 'ccm4',
    204: 'ccm5',
    205: 'ccm3',
    206: 'ccm2',
    207: 'ccm6',
    208: 'ccm1',
    209: 'annealing1'
}

def get_ist_timestamp(milli=False, system_tz='utc'):
    """
    :param milli: If resp is needed in ms epoch
    :param system_tz: The timezone of the machine on which script is running
    :return:
    """
    if system_tz == 'ist':
        utc_timestamp = int(datetime.now().timestamp())
        if milli:
            utc_timestamp = int(datetime.now().timestamp() * 1000)
    else:
        utc_timestamp = int(datetime.utcnow().timestamp())
        if milli:
            utc_timestamp = int(datetime.utcnow().timestamp() * 1000)

    ist_seconds = ((5 * 60) + 30) * 60
    ist_timestamp = utc_timestamp + ist_seconds
    return ist_timestamp

def get_shift() ->  str:
    current_ist_time = get_ist_timestamp()
    # current_ist_time = int(datetime.utcnow().timestamp())
    # if time is between 10 pm of previous day and 6 am of current day shift is c
    # if time is between 6 am and 2 pm shift is a
    # if time is between 2 pm and 10 pm shift is b
    if datetime.fromtimestamp(current_ist_time).hour >= 22 or datetime.fromtimestamp(current_ist_time).hour < 6:
        shift = 'C'
    elif datetime.fromtimestamp(current_ist_time).hour >= 6 and datetime.fromtimestamp(current_ist_time).hour < 14:
        shift = 'A'
    elif datetime.fromtimestamp(current_ist_time).hour >= 14 and datetime.fromtimestamp(current_ist_time).hour < 22:
        shift = 'B'

    return shift

def log_camera_down() -> None:
    with open(f'camera_down_logs.log', 'a') as f:
        f.write(f"Dropped: {get_ist_timestamp()}\n")

def log_camera_reconnected() -> None:
    with open(f'camera_down_logs.log', 'a') as f:
        f.write(f"Reconnected: {get_ist_timestamp()}\n")