import json
import paho.mqtt.client as MQTT
from sensor_generator import *
import datetime
from datetime import datetime, timedelta
import time
from shared.http_requests import *
import pytz

class MyPublisher:

    def __init__(self, config):
        """
        Initialize the MQTT client and set the configuration parameters.

        :param baseTopic: The base topic for the MQTT client.

        """
        self.catalog_url = config["catalog_url"]
        self.http_requests = http_requests(self.catalog_url)
        self.service_data = {"endpoint_type": "sensor_docker"}
        self.config = config
        # Define the message structure
        self.__message={"bn": "",
                "e":
                    [
                        {
                            "n":"",
                            "value":"",
                            "unit":"",
                            "timestamp":""
                        }
                    ]

        }
        
    
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
        self.broker = config["broker"]
        self.port = config["port"]
        self.clientID = config["clientID"]

        # Update the service data
        self.baseTopic = config["base_topic"]
        self.topic_hr= config["topic_hr"]
        self.topic_spo2 = config["topic_spo2"]
        self.topic_snor = config["topic_snor"]

        self.service_data["topics"] = [self.baseTopic,self.topic_hr, self.topic_spo2, self.topic_snor]
        self.catalog_url = config["catalog_url"] 
        
        # Create the MQTT client   
        self.client = MQTT.Client(self.clientID, True)	
        self.client.on_connect = self.myOnConnect

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
        self.client.loop_stop()
        self.client.disconnect()
    
    def myOnConnect(self, paho_mqtt, userdata, flag, rc): 
        """
        Define callback function for successful connection to the MQTT broker.
        :param paho_mqtt: The MQTT client.
        :param userdata: The user data.
        :param flag: The connection flag.
        :param rc: The connection result code.
        :return: None
        """
        print(f"Connected to {self.broker}, with result code {rc}")
    
    def publish(self):
        """
        Publish sensor data to MQTT broker.

        This method retrieves the endpoint URL for the data adaptor from the catalog service and retrieves the sensor information from the adaptor service. 
        It then checks if the current time is within the sleep window of the sensor 
        and generates and publishes sensor data to the MQTT broker for heart rate, spo2, and snoring. 
        If the current time is not within the sleep window, the method does not publish any data.

        Note that this method requires an active MQTT client connection 
        and assumes that the self.sensor_id variable is set to a valid sensor ID.

        :return: None
        """
        # GET adaptor_url
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")

        # GET list of sensors
        action = "patient_info"
        sensor_info = self.http_requests.GET(adaptor_data_url, action = action, params = {"id" :self.sensor_id})
        
        # If the request is ok the patient_id is saved in the variable
        if sensor_info.status_code != 200:
            raise Exception(f"Failed to retrieve sensor info from the catalog.")
        sensor_element = sensor_info.json()
        

        # Set the timezone to UTC
        local_timezone = pytz.timezone('UTC')
        # Get the current date and time
        now = datetime.now(local_timezone).replace(tzinfo=None)

        start_time = datetime.strptime(sensor_element["fall_asleep_time"], "%H:%M")
        end_time = datetime.strptime(sensor_element["wake_up_time"], "%H:%M")
        
        # Create datetime objects for start and end times on the current date
        start_datetime = datetime.combine(now.date(), start_time.time()).replace(tzinfo=None)
        end_datetime = datetime.combine(now.date(), end_time.time()).replace(tzinfo=None)
        # Adjust end time if it's before start time
        if end_datetime < start_datetime:
            end_datetime = end_datetime + timedelta(days=1)
        # Check if current time is between start and end times
        if start_datetime < now < end_datetime:        
            rg=sensor_generator() #calling the class for generating sensors values
            topic = "/".join([self.baseTopic,self.sensor_id])
            hr_data = rg.generate_hr_data()
            snoring_data = rg.generate_snoring_data()
            spo2_data = rg.generate_spo2_data()
            message = self.__message
            message["bn"]=self.topic_hr
            message["e"][0]["n"]='HR'
            message["e"][0]["value"]=hr_data
            message["e"][0]["unit"]='bpm'
            message["e"][0]["timestamp"]=int(now.timestamp()) 
            self.client.publish(topic+self.topic_hr,json.dumps(message),2)
            print(f"message published on topic {topic+self.topic_hr}")
            message["bn"]=self.topic_spo2
            message["e"][0]["n"]='spo2'
            message["e"][0]["value"]=spo2_data
            message["e"][0]["unit"]='%'
            message["e"][0]["timestamp"]=int(now.timestamp())
            self.client.publish(topic+self.topic_spo2,json.dumps(message),2)
            print(f"message published on topic {topic+self.topic_spo2}")
            message["bn"]=self.topic_snor
            message["e"][0]["n"]="snor"
            message["e"][0]["value"]=snoring_data
            message["e"][0]["unit"]='dB'
            message["e"][0]["timestamp"]=int(now.timestamp())
            self.client.publish(topic+self.topic_snor,json.dumps(message),2)
            print(f"message published on topic {topic+self.topic_snor}")

    def get_document_id(self):
        """
        Retrieves the document id for the current sensor from a catalog service using an HTTP GET request.

        :return: A dictionary containing a message confirming that the document id was retrieved.
        :raises Exception: If the request to retrieve the sensor info from the catalog fails.
        """  
        
        
        # GET sensor info
        sensor_info = self.http_requests.GET(self.catalog_url, action = "get_process", params = {"process_id": "", "collection" : "Sensors Processes", "option":"docker"})
       
        # If the request is ok the patient_id is saved in the variable
        if sensor_info.status_code != 200:
            raise Exception(f"Failed to retrieve sensor info from the catalog.")
        self.sensor_id = sensor_info.json()["process_id"]
        updare_response = self.http_requests.PUT(self.catalog_url, action = "update_process", params = { "collection" : "Sensors Processes", "option":"docker"}, payload = {"id":self.sensor_id,"process_status":True})
        if updare_response.status_code != 200:
            raise Exception(f"Failed to update sensor status.") 
        return {"message": f"document_id: {self.sensor_id} retrived and saved"}

if __name__ == "__main__":
    
    with open("shared/config.json","r") as f:
        config = json.load(f)
    
    time.sleep(30)
    sensor = MyPublisher(config)
    sensor.get_config()
    response = sensor.get_document_id()
    print(f"{response['message']}")
    sensor.start()

    while True:
        sensor.publish()
        sensor.get_config()
        time.sleep(59)

