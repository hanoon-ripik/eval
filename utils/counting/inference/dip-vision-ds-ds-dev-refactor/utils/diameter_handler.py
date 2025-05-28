from typing import List, Dict, Optional, Literal
import time
from collections import Counter, defaultdict
import numpy as np

class DiameterHandler:

    def __init__(self, handler_type: Literal['LIST', 'DICT'], ratios: Dict, possible_dias: List) -> None:
        
        self.diameters_curr : List | Dict = [] if handler_type == 'LIST' else defaultdict(list)
        self.handler_type : Literal['LIST', 'DICT'] = handler_type

        self.diameters_queue : List = []
        self.DIA_QUEUE_THRESHOLD : int = 5
        self.last_dia_time = None
        self.DIA_TIME_THRESHOLD : int = 7200

        self.ratios = ratios
        self.possible_dias = possible_dias

    def add(self, px_dia: int, dict_index: Optional[str] = None) -> None:

        if self.handler_type == 'LIST':
            self.diameters_curr.append(px_dia)
        elif self.handler_type == 'DICT':
            self.diameters_curr[dict_index].append(px_dia)

    def clear(self) -> None:

        self.diameters_curr = [] if self.handler_type == 'LIST' else defaultdict(list)

    def non_zero_median(self, pipe_id: Optional[str] = None) -> Optional[int]:

        if self.handler_type == 'LIST':

            if len(self.diameters_curr) == 0:
                return None

            arr = [x for x in self.diameters_curr if x!=0]

            return np.median(arr)
        
        elif self.handler_type == 'DICT':

            if len(self.diameters_curr[pipe_id]) == 0:
                return 0

            arr = [x for x in self.diameters_curr[pipe_id] if x!=0]

            return np.median(arr)            

    def px_to_mm(self, px_dia: int, pipe_id: str) -> int | float:
        
        act_dia = None

        for key, value in self.ratios['abs_limits'].items():
            if px_dia >= value[0] and px_dia < value[1]:
                act_dia = key
                break

        if act_dia is None:
    
            act_dia = px_dia*self.ratios['px_ratio']
            act_dia = min(self.possible_dias, key=lambda x: abs(x - act_dia))

        act_dia = self.verify_dia(act_dia, pipe_id)

        return act_dia

    def verify_dia(self, mm_dia: int | float, pipe_id: str) -> int | float:

        if self.last_dia_time is None:
            pass

        elif time.time() - self.last_dia_time > self.DIA_TIME_THRESHOLD:
            self.diameters_queue = []

        self.last_dia_time = time.time()
        
        dias = []
        present = None

        for i in range(len(self.diameters_queue)):
            pipe, dia = self.diameters_queue[i]

            dias.append(dia)
            if pipe == pipe_id:
                present = i

        most_common = self.highest_occurence(dias)

        if most_common:
            mm_dia = most_common

        if present is not None:
            self.diameters_queue[present] = (pipe_id, mm_dia)

        else:
            self.diameters_queue.append((pipe_id, mm_dia))

        if len(self.diameters_queue) > self.DIA_QUEUE_THRESHOLD:
            self.diameters_queue.pop(0)

        return mm_dia
    
    def highest_occurence(self, dias_list: List):

        if len(dias_list) < self.DIA_QUEUE_THRESHOLD:
            return None
        
        counter = Counter(dias_list)
        most_common = counter.most_common()

        if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
            return None
        
        return most_common[0][0]