import cherrypy
import json
import subprocess
import datetime
import time
import docker
from shared.http_requests import *

class sensor_adaptor(): 
    def __init__(self,config):
        self.config = config
        self.catalog_url = config["catalog_url"]
        self.service_data= {
            "endpoint_type": "sensor_adaptor"
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
        # Update the configuration parameters
        self.image_name = config["image_name"]

        self.host = config["host"] 
        self.port = config["port"] 
        self.service_data["endpoint_url"] = f'http://{config["host"]}:{config["port"]}'
        self.catalog_url = config["catalog_url"] 
        
    def register(self):
        """
        Register a sensor adaptor service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the data adaptor service data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the sensor adaptor.")
        # If the post response is successfull the sensor has been registered
        print(response.text)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def start_sensor(self,**params):
        """
        Creates a new sensor process for a specific chat_id and returns the metadata for the newly created process.
        :params (dict): A dictionary containing parameters for the sensor creation process.
        :returns: A dictionary containing the metadata for the newly created sensor process.
        :raises exception: If any of the GET, POST, or PUT requests to the mongodb adaptor fail.
        """
        
        id = params["chat_id"] 
        container_name = f"sensor_{int(id)}"
    
        now = datetime.datetime.now()
        now_unix_timestamp = int(now.timestamp())
        #Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        payload = {
                "process_id": id,
                "process_status" : False,
                "created_at": now_unix_timestamp,
                "container_name": container_name, 
            }
        post_response = self.http_requests.POST(self.catalog_url,action="create_process",params = {"collection":"Sensors Processes"},payload = payload)
        if post_response.status_code != 200: 
            print("Sensor process creation failed")
            raise Exception("Failed to create the service on the database.")
        #print(f"\n{post_response.json()['message']}\n") 
        
        try:
           
            docker_command = ["docker", "run", "--name", container_name, "--network", "iot_17_08_my_network", "iot_17_08-sensor-simulation"]
            print(docker_command)
            subprocess.run(docker_command, check=True)
        
        except subprocess.CalledProcessError as e:
            error_msg = f"Docker container creation failed: {str(e)}."
            return json.dumps({"error": error_msg})
        # Make a PUT request to the mongodb adaptor to send a collection and a json
        put_response = self.http_requests.PUT(self.catalog_url,action="update_process",params = {"collection":"Sensors Processes", "option":"normal"},payload = {"id": id, "container_name": container_name})
        if put_response.status_code != 200: 
            print("Sensor Process registration failed")
            raise Exception("Failed to update the service on the database.")
        print(f"\nConteiner {id} created succesfully \n")
        return {"message": "Docker container and sensor created succesfully"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def stop_sensor(self,**params):
        """
        Close the process associated with the given chat_id
        :param params: A dictionary containing the chat_id associated with the process to close.
        :raises Exception: If the process associated with the given chat_id is not found or failed to be updated in the database.
        """

        id = params["chat_id"]

        process_info = self.http_requests.GET(self.catalog_url,action="get_process",params = {"process_id":{id}, "collection":"Sensors Processes", "option":"normal"})

        if process_info.status_code != 200: 
            print("Sensor process retrieve failed")
            raise Exception("Failed to retrieve the service from the database.")
        process_info = process_info.json()

        # Stop and remove the container
        try:
            subprocess.run(["docker", "rm", "-f", process_info["container_name"]], check=True)
            # Delete the process record from the database
            delete_response = self.http_requests.DELETE(self.catalog_url,action="delete_process",params = {"process_id":{id}, "collection":"Sensors Processes"})
            if delete_response.status_code != 200: 
                print("Sensor process deletion failed")
                raise Exception("Failed to delete the document on the database.")
            print(f"Sensor process deleted succesfully")
            return {"message": "Sensor document deleted succesfully"}
        
        except subprocess.CalledProcessError as e:
            print(f"Error running docker command: {e}")

if __name__ == "__main__":
    
    with open("shared/config.json","r") as f:
        config = json.load(f)
    
    sensor_adaptor = sensor_adaptor(config)
    time.sleep(30)
    sensor_adaptor.get_config()
    sensor_adaptor.register()
    print(f"Sensor Adaptor registered and running on {sensor_adaptor.host}:{sensor_adaptor.port}" )

    cherrypy.config.update({'server.socket_host': sensor_adaptor.host})
    cherrypy.config.update({'server.socket_port': sensor_adaptor.port})
    cherrypy.tree.mount(sensor_adaptor, '/')
    cherrypy.engine.start()
    
    prev_host = sensor_adaptor.host
    prev_port = sensor_adaptor.port

    while True:
        time.sleep(30)
        sensor_adaptor.get_config()
        sensor_adaptor.register()
        if sensor_adaptor.host != prev_host or sensor_adaptor.port != prev_port:
            cherrypy.server.socket_host = sensor_adaptor.host
            cherrypy.server.socket_port = sensor_adaptor.port
            cherrypy.tree.mount(sensor_adaptor, '/')
            cherrypy.engine.start()

            prev_host = sensor_adaptor.host
            prev_port = sensor_adaptor.port
            print("Sensor adaptor updated: restarted CherryPy server with new host and port!")
        else:
            print("Sensor adaptor updated: host and port did not change")
        
    
