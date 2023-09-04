import numpy as np
from datetime import datetime

class statistics_generator():
    """
    This class is used to generate statistics from the data received from the data storage service.
    :param None
    """
    def __init__(self):
        pass
    def mean_value(self,data):
        mean_value=np.average(data)
        return mean_value
    def dev_value(self,data):
        dev_value=np.std(data)
        return dev_value
    def tot_episodes(self,data):
        tot_apnea=int(np.sum(data))
        return tot_apnea
    def mean_apnea_duration(self,data):
        ones_succession = []
        counter = 0
        for i in range(len(data)):
            if data[i] == 1:
                counter += 1
            else:
                if counter != 0:
                    ones_succession.append(counter)
                    counter = 0
        if counter != 0:
            ones_succession.append(counter)

        mean_apnea_dur=round(np.mean(ones_succession),1)
        return mean_apnea_dur