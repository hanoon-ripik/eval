import time

pipes_crossed = []
pipe_come_backs = []
files_stored = 0

pipe_crossed_in_frame_count = dict()

def trim_multi_pipe(pipe_id, threshold = 10):
    global pipe_crossed_in_frame_count

    if pipe_id == None:
        return True

    if not pipe_id in pipe_crossed_in_frame_count.keys():
        pipe_crossed_in_frame_count[pipe_id] = {
                                                'count': 0,
                                                'createdAt': time.time()
                                            }

    pipe_crossed_in_frame_count[pipe_id]['count']+=1
    pipe_crossed_in_frame_count[pipe_id]['createdAt']=time.time()
    if pipe_crossed_in_frame_count[pipe_id]['count'] > threshold:
        return True
    
    return False

def clear_multi_pipe_dict(seconds_threshold = 30):
    global pipe_crossed_in_frame_count

    to_be_deleted = []
    for pipe_id in pipe_crossed_in_frame_count.keys():
        if time.time() - pipe_crossed_in_frame_count[pipe_id]['createdAt'] > seconds_threshold:
            to_be_deleted.append(pipe_id)

    for pipe_id in to_be_deleted:
        del pipe_crossed_in_frame_count[pipe_id]