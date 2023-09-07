class dataExtractor(): 
    """
    this class is used to extract data from the database and to format it in a way that is compatible with NODE-RED
    """ 
    def __init__(self,catalog_data,catalog_stat): 
        self.collection_data = catalog_data
        self.collection_stat = catalog_stat

    def single_day(self, start_date, sleep_data, patient_id_str): 
        """
        Retrieve sleep data for a specific patient and date.
    
        :param patient_id_str: A string representing the ID of the patient whose data is to be retrieved.
        :param start_date: A string representing the start date for the data to be retrieved.
        :return: A dictionary containing the sleep data for the specified patient and date, or an error message if no data is found.
        """
        # define a query with the specific patient and the selected date
        query = {"patient_id": patient_id_str, "date": start_date}
        # perform a find_one operation on the specified query
        data_graph = self.collection_data.find_one(query)
        data_stat = self.collection_stat.find_one(query)
        # if no data is found, return error
        if data_graph and data_stat is None: 
            return "No data found"
        # else save the returned data into the specific sleep data structure 
        # (it has to be saved in this way to be compatible with NODE-RED)
        else: 
            sleep_data["ecg"]= data_graph["ecg_data"]
            sleep_data["snoring"]=data_graph["snoring_data"]
            sleep_data["spo2"]=data_graph["spo2_data"]
            sleep_data["n_episods"] = data_stat["total apnea episodes"]
            sleep_data["max_episods"]= data_stat["total apnea episodes"]
            sleep_data["day_max_ep"] = "Today"
            sleep_data["avg_time_ep"] = data_stat["mean total apnea duration"]
            return sleep_data     
    
    def multiple_day(self, start_date, end_date, sleep_data, patient): 
        """    
        Retrieve sleep data for a patient between the specified dates from the database.
    
        :param patient: The patient ID for which to retrieve data.
        :param start_date: The end date for the data to retrieve.
        :param end_date: The start date for the data to retrieve.
        :return: A dictionary containing the sleep data for the patient between the specified dates.
        """

        query = {"patient_id":patient, "date": {"$gte": end_date, "$lte": start_date }}
        data = list(self.collection_stat.find(query))
        if data is None: 
           return "No data found"
        else: 
            max_epi = 0
            for element in data:
                sleep_data["ecg"].append(self.sensor_ecg_template(self.range_values(element["hr_mean"],element["hr_std"]),element["date"]))
                sleep_data["snoring"].append(self.sensor_snoring_template(self.range_values(element["snoring_mean"],element["snoring_std"]),element["date"]))
                sleep_data["spo2"].append(self.sensor_spo2_template(self.range_values(element["spo2_mean"],element["spo2_std"]),element["date"])) 
                sleep_data["n_episods"] = sleep_data["n_episods"] + element["total apnea episodes"]
                if element["total apnea episodes"]>max_epi: 
                    sleep_data["max_episods"]= element["total apnea episodes"]
                    sleep_data["day_max_ep"] = element["date"]
                    max_epi = element["total apnea episodes"]
                sleep_data["avg_time_ep"] = sleep_data["avg_time_ep"] + element["mean total apnea duration"]
            sleep_data["avg_time_ep"] = sleep_data["avg_time_ep"]/len(data)
            return sleep_data
    
    def range_values(self,data,std):
        """    
        Calculate the range of values around a given data point based on the standard deviation.
    
        :param data: The data point around which to calculate the range.
        :param std: The standard deviation used to calculate the range.
        :return: A list containing the range of values around the data point.
        """ 
        range = [data-std, data, data+std]
        return range
    
    def sensor_ecg_template(self, range, date):
        """
        Generate a dictionary with ECG data for a given range of heart rate values.

        :param data: The heart rate value.
        :param std: The standard deviation of the heart rate value.
        :param date: The timestamp of the heart rate value.
        :return: A dictionary containing ECG data with the heart rate range, timestamp and bpm unit.
        """
        ecg = {
        "n": "heart rate",
        "min value" : range[0], 
        "avg value": range[1],
        "max value" : range[2], 
        "timestamp": date,
        "unit": "bpm"
        }
        return ecg 

    def sensor_snoring_template(self, range, date): 
        """
        Generate a dictionary with Snoring data for a given range of Snoring values.

        :param data: The Snoring value.
        :param std: The standard deviation of the Snoring value.
        :param date: The timestamp of the Snoring value.
        :return: A dictionary containing ECG data with the Snoring range, timestamp and dB unit.
        """
        snoring = {
        "n": "snooring",
        "min value" : range[0], 
        "avg value": range[1],
        "max value" : range[2], 
        "timestamp": date,
        "unit": "dB"
        }
        return snoring

    def sensor_spo2_template(self, range, date): 
        """
        Generate a dictionary with SpO2 data for a given range of SpO2 values.

        :param data: The SpO2 value.
        :param std: The standard deviation of the SpO2 value.
        :param date: The timestamp of the SpO2 value.
        :return: A dictionary containing ECG data with the SpO2 range, timestamp and % unit.
        """
        spo2 = { 
        "n": "Sp02",
        "min value" : range[0], 
        "avg value": range[1],
        "max value" : range[2], 
        "timestamp": date,
        "unit": "%"
        }
        return spo2
