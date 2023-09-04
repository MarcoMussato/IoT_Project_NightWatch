import datetime
from datetime import datetime
import paho.mqtt.client as MQTT
from shared.http_requests import *
import json
import time
import pytz

class Alert:
    def __init__(self, config):
        
        """
        :param config: url of the catalog
        :param date: date of the day to analyze
        """
        self.config = config
        self.catalog_url = config["catalog_url"] 
        self.service_data = {
            'endpoint_type': 'alert'
        }
        self.http_requests = http_requests(self.catalog_url)

        self.__message = "WARNING! A critical number of apnea episodes was found for patient: "

    def get_config(self):
        """
        Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        :param None
        :return: None
        """ 
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
        self.base_topic = config["base_topic"]
        self.broker = config["broker"]
        self.port = config["port"]
        self.clientID = config["clientID"]
        self.alert_topic = config['alert_topic']

        # Create the MQTT client   
        self.client = MQTT.Client(self.clientID, True)	
        self.client.on_connect = self.myOnConnect
        
    def register(self):
        """
        Register the data storage service by making a POST request to the catalog to register the service.

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
        

    def start(self): 
        """
        Connect to a MQTT broker.

        :param broker: The IP address or hostname of the MQTT broker to connect to.
        :param port: The port number to connect to the MQTT broker.
        """
        self.client.connect(self.broker, self.port)
        self.client.loop_start()       

    def stop(self): 
        """
        Stop the MQTT client.

        :return: None
        """
        # self.client.unsubscribe(self.topic)
        self.client.loop_stop()
        self.client.disconnect()

    def myOnConnect(self, paho_mqtt, userdata, flag, rc): 
        """
        Define callback function for successful connection.
        :param paho_mqtt: The client instance for this callback.
        :param userdata: The private user data as set in Client() or userdata_set().
        :param flag: Response flags sent by the broker.
        :param rc: The connection result.
        :return: None
        """
        print(f"Connected to {self.broker}, with result code {rc}")


    def publish(self):
        """
        Publish sensor data to MQTT broker.
        :param None
        :return: None
        """
        #GET adaptor_url
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")

        action = "find_doctor_patients"
         # Set the timezone to Houston
        local_timezone = pytz.timezone('UTC')
        # Get the current date and time
        now = datetime.now(local_timezone)
        # Replace the hour, minute and second values with 0, 0 and 0 respectively
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Convert the datetime object to Unix timestamp
        midnight_unix_timestamp = int(midnight.timestamp())
        
        doctors_info = self.http_requests.GET(adaptor_data_url, action = action, params = {"timestamp" : midnight_unix_timestamp})
        
        #if doctors_info.status_code != 200:
        if doctors_info.status_code != 200:
            raise Exception(f"Failed to retrieve the {action} from the data adaptor.")
        doctors_list = doctors_info.json()
        
        for element in doctors_list:
            chatID = element['doctor_chat_ID']
            # Construct the message for each patient associated with the doctor
            msg = self.__message + element['patient_name'] + " " + element['patient_surname']
            topic = "/".join([self.base_topic, self.alert_topic, chatID])
            self.client.publish(topic, json.dumps(msg), 2)
            print(f"message published on topic {topic}")

if __name__ == "__main__":
     
    with open("shared/config.json", "r") as f:
        config = json.load(f)
    # Register the service
    time.sleep(40)
    alert = Alert(config)
    alert.get_config()
    alert.start()
    
    while True:
        alert.get_config
        alert.publish()
        time.sleep(600) # 10 minutes
        