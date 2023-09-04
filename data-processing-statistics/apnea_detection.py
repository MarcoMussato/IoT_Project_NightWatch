from pymongo import MongoClient
import numpy as np

#apnea detection
class ApneaDetection():
    def __init__(self):
        pass
    def detection(self,hr,spo2,snor,ts):
        """
        Detect episodes of low oxygen saturation or high snoring in a dataset of heart rate, oxygen saturation, and snoring data.

        :param hr: A list of floats representing heart rate data.
        :param spo2: A list of floats representing oxygen saturation data.
        :param snor: A list of floats representing snoring data.
        :param ts: A list of datetime objects representing timestamps for the data.
        :return: A tuple of two lists: a list of floats indicating whether an episode occurred at each timestamp, and a list of datetime objects representing the timestamps of the episodes.
        """
        episodes=np.zeros(len(hr))
        ts_episodes=[]

                
        for i in range(min(len(hr), len(spo2), len(snor))):
                    
                    if hr[i] <= (73.1):
                        if spo2[i]< (93.1) or snor[i] > 45:
                            
                            episodes[i] = 1
                            ts_episodes = ts[i]
        return episodes,ts_episodes
