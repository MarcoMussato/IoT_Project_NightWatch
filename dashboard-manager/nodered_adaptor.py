import cherrypy
import json
import random
import subprocess
import datetime
import time
from shared.http_requests import *

class noderedAdaptor(): 
    
    def __init__(self,config):
        self.config = config
        self.catalog_url = config["catalog_url"]
        self.service_data= {
            "endpoint_type": "dashboard_adaptor",
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
        self.host = config["host"] 
        self.port = config["port"] 
        self.service_data["endpoint_url"] = f'http://{config["host"]}:{config["port"]}' 
        self.catalog_url = config["catalog_url"] 
        self.nodered_host = config["nodered_host"]

    def register(self):
        """
        Register a node-red adaptor service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the data adaptor service data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the node-red adaptor.")
        # If the post response is successfull the BOT has been registered
        print(response.text)
        
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def start_nodered(self, **params):
        """
        Register a new dashboard process by starting a Node-RED instance and sending its details to the database.
        :param params: A dictionary containing parameters needed to register the process, including 'chat_id'.
        :return: A list of dictionaries representing the registered dashboard processes.
        """
        # Initialize params for container creation
        id = params["chat_id"]
        container_name = f"dashboard_{id}"
        
        # Start a new container
        try:
            cmd = ["docker", "run", "--name", f"{container_name}", "-p", "1880", "--network", "<main_folder_name>_my_network", "<main_folder_name>-sensor-simulation"]
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
        
        # Once the container is started, retrieve the port mapping
        port_cmd = ["docker", "port", container_name, "1880"]
        result = subprocess.run(port_cmd, capture_output=True, text=True)
        host_port = result.stdout.split(":")[-1].strip()
        
        # Create the payload
        now = datetime.datetime.now()
        now_unix_timestamp = int(now.timestamp())
        payload = {
                "process_id": id,
                "process_url" : f"http://{self.nodered_host}:{host_port}",
                "process_status" : True,
                "created_at": now_unix_timestamp,
                "container_name": container_name,
            }
        # Make a POST request to the catalog to create a new document in the database
        post_response = self.http_requests.POST(self.catalog_url, "create_process", payload, {"collection":"Dashboard Processes"})
    
        if post_response and post_response.status_code != 200:      
            print("Dashboard process creation failed")
            raise Exception("Failed to create the process on the database.")
        # If the post response is successfull the process has been created
        print("Dashboard process created successfully")
        return {"message": "Dashboard process created successfully using " + str(host_port) + "."}
        
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def stop_nodered(self,**params):
        """
        Close a dashboard process by stopping its Node-RED instance and updating the database.
        :param params: A dictionary containing parameters needed to close the process, including 'chat_id'.
        :return: message
        """    
        id = params["chat_id"]
        process_info = self.http_requests.GET(self.catalog_url,action="get_process",params = {"process_id":{id}, "collection":"Dashboard Processes", "option":"normal"})

        if process_info.status_code != 200: 
            print("Dashboard process retrieve failed")
            raise Exception("Failed to retrieve the service from the database.")
        process_info = process_info.json()
        
        # Stop and remove the container
        try:
            subprocess.run(["docker", "rm", "-f", process_info["container_name"]], check=True)
            delete_response = self.http_requests.DELETE(self.catalog_url,action="delete_process", params = {"process_id":{id}, "collection":"Dashboard Processes"})
            if delete_response.status_code != 200: 
                print("Dashboard process deletion failed")
                raise Exception("Failed to delete the document on the database.")
            print(f"Dashboard process deleted succesfully")
            return {"message": "Dashboard document deleted succesfully"}
        
        except subprocess.CalledProcessError as e:
            print(f"Error running docker command: {e}")    
                

if __name__ == "__main__":
    
    # Load the configuration file
    with open("shared/config.json","r") as f:
        config = json.load(f)
    time.sleep(30)
    adaptor = noderedAdaptor(config)
    adaptor.get_config()
    adaptor.register()
    
    print(f"Node-RED adaptor registered running on {adaptor.host}:{adaptor.port}")
    
    # Start the CherryPy server
    cherrypy.config.update({'server.socket_host': adaptor.host})
    cherrypy.config.update({'server.socket_port': adaptor.port})
    cherrypy.tree.mount(adaptor, '/')
    cherrypy.engine.start()

    prev_host = adaptor.host
    prev_port = adaptor.port

    # Periodically check if the configuration has changed
    while True:
        time.sleep(30)
        adaptor.get_config()
        adaptor.register()
        if adaptor.host != prev_host or adaptor.port != prev_port:
            cherrypy.server.socket_host = adaptor.host
            cherrypy.server.socket_port = adaptor.port
            cherrypy.tree.mount(adaptor, '/')
            cherrypy.engine.start()

            prev_host = adaptor.host
            prev_port = adaptor.port
            print("Node-RED adaptor updated: restarted CherryPy server with new host and port!")
        else:
            print("Node-RED adaptors updated: host and port did not change")
        
