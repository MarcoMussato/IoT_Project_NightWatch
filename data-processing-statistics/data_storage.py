import datetime
import cherrypy
import json
import paho.mqtt.client as MQTT
import time
from data_template import *
from shared.http_requests import *

class data_storage():
    
    def __init__(self,config):
        self.all_ecg=[]
        self.all_spo2=[]
        self.all_snoring=[]
        self.all_data=[]
        self.data = []
        self.config = config
        self.catalog_url = config["catalog_url"] 
        self.service_data= {
            "endpoint_type": "data_storage"
        }
        self.http_requests = http_requests(self.catalog_url)
        
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
        self.catalog_url = config["catalog_url"]
        self.clientID=config["clientID"]
        self.topic=f'{config["base_topic"]}/#'
        self.broker= config["broker"]
        self.port = config["port"]
        self.client = MQTT.Client(self.clientID, True)	
        # Bind the functions to the MQTT client
        self.client.on_connect = self.myOnConnect
        self.client.on_message = self.myOnMessageRec
    

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
        Connect to a MQTT broker and subscribe to a topic.

        :param broker: The IP address or hostname of the MQTT broker to connect to.
        :param port: The port number to connect to the MQTT broker.
        :param topic: The topic to subscribe to.
        """
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        self.client.subscribe(self.topic, 2)
        print(f"Subscribed to topics: {self.topic}")
        
    def stop(self):
        """
        Stop the MQTT client and unsubscribe from the topic.

        :param topic: The topic to unsubscribe from.
        :return: None
        """
        self.client.unsubscribe(self.topic)
        self.client.loop_stop()
        self.client.disconnect()
        
    def myOnConnect(self, paho_mqtt, userdata, flag, rc): 
        """
        Prints a message indicating the successful connection to a broker and its result code.

        :param rc: The result code of the connection to the broker.
        :return: None
        """
        print(f"Connected to {self.broker}, with result code {rc}")

    def myOnMessageRec(self, paho_mqtt, userdata, msg):
        """    
        Method that handles the message received by the MQTT client.

        :args: client (paho.mqtt.client.Client): the MQTT client instance for which the callback was triggered.
        :args: userdata (any): the private user data as set in Client() or userdata_set().
        :args: msg (paho.mqtt.client.MQTTMessage): the message received from the MQTT broker.
    
        :returns: None

        :raises: exception: if any of the HTTP requests to the catalog or the database fails.
        """
        
        now = datetime.datetime.now()
        now_unix_timestamp = int(now.timestamp())
        
        full_topic = msg.topic
        topic_fields = full_topic.split("/")
        sensor_id = topic_fields[2]
        data_type = topic_fields[3]
        
        message= json.loads(msg.payload)
        data = Template()
        
        if data_type == "HR": 
            data_to_insert = data.ecg_template(message)
        elif data_type == "snor": 
            data_to_insert = data.snoring_template(message)
        elif data_type == "spo2": 
            data_to_insert = data.spo2_template(message)
           
        # Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        #This method checks if there is already a document related to that night's patient, based on the sensor
        catalog_response = self.http_requests.GET(adaptor_data_url, action = "find_data_document" , params = {"sensor_id": sensor_id, "time": now_unix_timestamp})
    
        if catalog_response.status_code != 200:
            raise Exception(f"Failed to perform {action} on the catalog.")
        document_id = catalog_response.json()
        
        if document_id != {'message': 'Sleep data not found.'}:
            put_response = self.http_requests.PUT(adaptor_data_url,action="update_data_document",params = {"data_type": data_type, "document_id":document_id},payload = data_to_insert)
            #if the request is ok the patient_id is saved in the variable
            if put_response.status_code != 200:
                raise Exception(f"Failed to perform {action} on the database.")
            print(f"{put_response.json()['message']} on field {data_type} for sensor {sensor_id}")
        else: 
            action = "create_data_document"
            post_response = self.http_requests.POST(adaptor_data_url,action=action,params = {"data_type": data_type, "sensor_id":sensor_id,"type":"data"},payload = data_to_insert)
            #if the request is ok the patient_id is saved in the variable
            if post_response.status_code != 200:
                raise Exception(f"Failed to perform {action} on the database.")
            print(f"Document created and {data_type} data inserted correctly")     

if __name__ == '__main__':
    
    with open("shared/config.json","r") as f:
        config = json.load(f)
    time.sleep(30)

    data_storage_service = data_storage(config)
    data_storage_service.get_config()
    data_storage_service.register()

    data_storage_service.start()
    
    while True: 
        time.sleep(180)
        data_storage_service.get_config()
