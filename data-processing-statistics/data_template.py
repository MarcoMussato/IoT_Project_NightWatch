class Template(): 
    
    def __init__(self):
        self.ecg = {
                'n':'',
                'value':'',
                'unit':'',
                'timestamp':''
            }
        self.snoring={
            'n':'',
            'value':'',
            'unit':'',
            'timestamp':''
            }
        self.spo2={
            'n':'',
            'value':'',
            'unit':'',
            'timestamp':''
            }
    
    def ecg_template(self,message): 
        """
        Process an ECG message and extract the relevant data.

        :param message: A dictionary representing an ECG message, containing keys for 'n', 'value', 'unit', and 'timestamp'.
        :return: A dictionary containing the extracted ECG data, with keys for 'n', 'value', 'unit', and 'timestamp'.
        """
        self.ecg['n'] = message["e"][0]["n"]
        self.ecg['value'] = message["e"][0]["value"]
        self.ecg['unit'] = message["e"][0]["unit"]
        self.ecg['timestamp'] = message["e"][0]["timestamp"]
        return self.ecg
    
    def snoring_template(self,message): 
        """
        Process a Snoring message and extract the relevant data.

        :param message: A dictionary representing a Snoring message, containing keys for 'n', 'value', 'unit', and 'timestamp'.
        :return: A dictionary containing the extracted Snoring data, with keys for 'n', 'value', 'unit', and 'timestamp'.
        """
        self.snoring["n"]=message["e"][0]["n"]
        self.snoring["value"]=message["e"][0]["value"]
        self.snoring["unit"]=message["e"][0]["unit"]
        self.snoring["timestamp"]=message["e"][0]["n"]
        return self.snoring
          
    def spo2_template(self,message): 
        """
        Process a SpO2 message and extract the relevant data.

        :param message: A dictionary representing a SpO2 message, containing keys for 'n', 'value', 'unit', and 'timestamp'.
        :return: A dictionary containing the extracted SpO2 data, with keys for 'n', 'value', 'unit', and 'timestamp'.
        """
        self.spo2['n'] = message["e"][0]["n"]
        self.spo2['value'] = message["e"][0]["value"]
        self.spo2['unit'] = message["e"][0]["unit"]
        self.spo2['timestamp'] = message["e"][0]["timestamp"]
        return self.spo2