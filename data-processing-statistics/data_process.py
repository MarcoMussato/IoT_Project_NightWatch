from apnea_detection import *
import datetime
from shared.http_requests import *
import json
import time
from stats import *
import pytz


# Define a class called Processing
class Processing():
    exposed=True
    def __init__(self,config):
        # Define a dictionary called service_data with three keys and initialize them to empty strings
        self.service_data= {
            "endpoint_type": "data_process"
        }
        # Get the value of the "catalog_url" key from the configuration file and assign it to a variable called "catalog_url"
        self.catalog_url = config["catalog_url"]
        self.http_requests = http_requests(self.catalog_url)
        self.config = config
    
    def get_config(self):
        """
        Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        
        :param None
        :return: None
        """ 
        
        # Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        catalog_response = self.http_requests.GET(self.catalog_url, action= "get_config", params = {"endpoint_type": self.service_data['endpoint_type']})
        
        if catalog_response.status_code != 200:
            raise Exception(f"Failed to retrieve the {self.service_data['endpoint_type']} configuration from catalog.")
        config = catalog_response.json()

        if config != self.config:  
            self.config = config
            self.update_config(config)
    
    def update_config(self,config):
        """
        Update the configuration of the data adaptor.

        :param config: A dictionary containing the configuration parameters.
        :return: None
        """
        # Update the configuration parameters
        self.catalog_url = config["catalog_url"] 
        
    def register(self):
        """
        Register a data processing service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the data adaptor service data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the doctors bot.")
        # If the post response is successfull the bot has been registered
        print(response.text)


    def check_end_night(self,time): 
        """
        Retrieves documents from a MongoDB endpoint adaptor using the endpoint URL retrieved from a catalog service,
        based on a specified "time" key.
        
        :param time: The time argument used to query the MongoDB adaptor.
        :return: None
        :raises Exception: If the response code is not 200.
        """
         # Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        # Make a GET request to the mongodb adaptor to retrieve the documents that have the "time" key equal to the "time" argument
        documents = self.http_requests.GET(adaptor_data_url,action="check_end_night",params = {"time":{time}})
        # Define the action to be performed as "check_end_night" and send a GET request to the endpoint
        if documents.status_code != 200:
            # If the response code is not 200, raise an exception
            raise Exception(f"Failed to perform check_end_night from the catalog.")
        # If the response code is 200, call the "processing" method and pass the response data as an argument
        self.processing(documents.json())
        
    def processing(self,documents):
        """
        Process the patient data to perform analytics and store them in the MongoDB database.

        :args: documents: A list of documents, where each document contains the patient's data.

        :Returns: None
        """
         # Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        # Loop through the documents returned by the previous method
        for document in documents:
            # Create empty lists for hr_values, spo2_values, and snor_values, as well as a list for timestamps
            hr_values = []
            spo2_values = []
            snor_values = []
            timestamp = []
            # Get the patient ID from the document
            patient_id = document["patient_id"]
            # Populate the hr_values, spo2_values, snor_values, and timestamp lists with data from the document
            hr_values = [doc["value"] for doc in document["ecg_data"]]
            spo2_values = [doc["value"] for doc in document["spo2_data"]]
            snor_values=[doc["value"] for doc in document["snoring_data"]]
            timestamp = [doc["timestamp"] for doc in document["ecg_data"]]
            
            #Apnea Detection
            det = ApneaDetection()
            apnea_episodes,ts_episodes=det.detection(hr_values,spo2_values,snor_values,timestamp)
            #Statistics
            a= statistics_generator()
        
            avr_hr=round(a.mean_value(hr_values),0)
            std_hr=round(a.dev_value(hr_values),0)

            avr_spo2=round(a.mean_value(spo2_values),1)
            std_spo2=round(a.dev_value(spo2_values),1)
            
            avr_snor=round(a.mean_value(snor_values),1)
            std_snor=round(a.dev_value(snor_values),1)
            
            tot_apnea=a.tot_episodes(apnea_episodes)
            mean_apnea_duration=a.mean_apnea_duration(apnea_episodes)

            # Set the timezone to Houston
            local_timezone = pytz.timezone('UTC')
            # Get the current date and time
            now = datetime.now(local_timezone)
            # create a new datetime object with the same date but at 00:00:00 time
            midnight_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # convert midnight datetime to Unix timestamp and add one day
            date_unix = int(midnight_datetime.timestamp())
            
            #Dictionary
            data_to_insert={
                "patient_id" : patient_id,
                "date" : date_unix,
                "hr_mean": avr_hr,
                "hr_std": std_hr,
                "spo2_mean": avr_spo2,
                "spo2_std": std_spo2,
                "snoring_mean": avr_snor,
                "snoring_std": std_snor,
                "total apnea episodes":tot_apnea,
                "mean total apnea duration":mean_apnea_duration,
                "ts apnea episodes": ts_episodes
            }
            post_response = self.http_requests.POST(adaptor_data_url,action="create_data_document",params = {"type":"analytics"},payload = data_to_insert)
            
            # #if the request is ok the patient_id is saved in the variable
            if post_response.status_code != 200:
                raise Exception(f"Failed to perform create_data_document from the catalog.")
            doc_id = post_response.json()
            print(f"Analytics of patient {patient_id} created in document {doc_id}")

if __name__ == "__main__":
    with open("shared/config.json","r") as f:
        config = json.load(f)
    time.sleep(30)  
    current_datetime = datetime.now()
    # Create an instance of the Processing class
    processing = Processing(config)
    processing.get_config()
    processing.register()
    print(f"Data process service registered")
    
    while True: 
        processing.get_config()
        processing.register()
        print(f"Data process service updated")
        
        time_unix = int(current_datetime.timestamp())
        processing.check_end_night(time_unix)
        
        time.sleep(180)
    
