import cherrypy
import json
from pymongo import MongoClient
import pymongo
import datetime
import time
from bson import ObjectId
from shared.http_requests import *

class MongoAPI_endpoints(object):
    def __init__(self,config):
        self.config = config
        self.catalog_url = config["catalog_url"]
        self.http_requests = http_requests((self.catalog_url))
        self.service_data = {
            "endpoint_type": "adaptor_endpoints"
        }
        
    def get_config(self):
        """
        Make a GET request to the catalog to retrieve the service configuration.
        
        :param None
        :return: None
        """ 
        
        # Make a GET request to the catalog to retrieve the service configuration
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

        self.client = MongoClient(config["mongo_url"])
        self.db = self.client[config["database_endpoints"]]
        self.collection = self.db[config["collection_endpoints"]]
        self.host = config["host"]
        self.port = config["port"]
        self.catalog_url = config["catalog_url"] 
        self.service_data["endpoint_url"] = f'http://{config["host"]}:{config["port"]}'

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def register_service(self):
        """
        Register a new service in the endpoints DB and update the service if it already exists.
        
        :body Service data
        :return: Response message with the name of the registered service
        """
        data = cherrypy.request.json
        endpoint_type = data["endpoint_type"] #save the name of the service
        query = {"endpoint_type": endpoint_type}
        existing_service = self.collection.find_one(query)

        now = datetime.datetime.now()
        now_unix_timestamp = int(now.timestamp())
        data["updated_at"] = now_unix_timestamp

        if existing_service:
            self.collection.update_one(query, {"$set": data})
            # Return response message with the name of the updated service
            print(f"{endpoint_type} service updated successfully")
            return f"{endpoint_type} service updated successfully"
        else:
            data["created_at"] = now_unix_timestamp
            self.collection.insert_one(data)
            # Return response message with the name of the registered service
            print(f"\n{endpoint_type} service registered successfully")
            return f"{endpoint_type} service registered successfully"
        
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def retrieve_endpoint_url(self,**params):
        """
        Retrieve the endpoint url of a service from the endpoints DB.

        :param endpoint_type: name of the service
        :return: Endpoint url of the service
        """

        endpoint_type = params["endpoint_type"] #save the name of the service
        query = {"endpoint_type": endpoint_type}
        existing_service = self.collection.find_one(query)

        if existing_service:
            # Convert ObjectId instance to string
            existing_service["_id"] = str(existing_service["_id"])
            print(f"{endpoint_type} service retrieved successfully")
            return existing_service
        else:
            return f"{endpoint_type} service not found"
        
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def delete_service(self):
        """
        Delete a service from the endpoints DB if it has not been updated in the last 10 minutes.

        :params endpoint_type: name of the service
        :return: Response message with the name of the deleted service
        """

        response = {"Deleted services": []}

        for service in self.collection.find():

            # Retrieve the last update time for the service from MongoDB
            last_update_time = service["updated_at"]

            # Calculate the time difference between now and the last update time
            time_diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(last_update_time)

            # If the time difference is greater than 10 minutes, delete the service from the endpoints DB
            if time_diff.total_seconds() > 600:
                delete_response = self.collection.delete_one({"endpoint_type": service['endpoint_type']})
                if delete_response.deleted_count == 1:
                    print(f"Deleted service {service['endpoint_type']} from the endpoints DB.")
                    response["Deleted services"].append(service['endpoint_type'])
                else:
                    print(f"Failed to delete service {service['endpoint_type']} from the endpoints DB.")
                    raise Exception(f"Failed to delete service {service['endpoint_type']} from the endpoints DB.")

        # Return a list of deleted services
        # If the list is empty, no services were deleted
        if response["Deleted services"]==[]:
            print("\nNo services were deleted from the endpoints DB.")
        return response    

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_process (self,**params):
        """
        Retrieve a process from the DB.

        :param process_id: id of the process
        :param collection: name of the collection
        :param option: normal or other
        :return: Process
        """
        # Retrieve the process from the DB
        process_id = params["process_id"] # save the id of the process
        collection = params["collection"] # save the name of the collection
        option = params["option"] # save the option
        # If the option is normal, retrieve the process by the process_id
        if option == "normal":
            process = self.db[collection].find_one({"process_id": process_id})
        # If the option is other, retrieve the process by the process_status
        else:
            process = self.db[collection].find_one({"process_status": False}, sort=[("created_at", pymongo.ASCENDING)])
        # Convert ObjectId instance to string
        process["_id"] = str(process["_id"])
        # Return the process
        return process
    
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def create_process (self,**params):
        """"
        Create a new process in the DB.
        
        :param collection: name of the collection
        :body Process data
        :return: Response message with the name of the collection
        """ 
        # Create a new process in the DB
        process = cherrypy.request.json
        collection = params["collection"]
        # Insert the process in the DB
        self.db[collection].insert_one(process).inserted_id
        return f"{collection} created successfully"
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def update_process (self,**params): 
        """
        Update a process in the DB.

        :param collection: name of the collection
        :param option: normal or other
        :body Process data
        :return: Response message with the name of the collection
        """
        # Update a process in the DB
        process = cherrypy.request.json
        collection = params["collection"]
        option = params["option"]
        # If the option is normal, update the process by the process_id
        if option == "normal":
            self.db[collection].update_one({"process_id": process["id"]}, {"$set": {"container_name": process["container_name"]}})
        # If the option is other, update the process by the process_status
        else: 
            self.db[collection].update_one({"process_id": process["id"]}, {"$set": {"process_status": process["process_status"]}})
        # Return response message with the name of the collection
        return {"message": f"{collection} updated successfully"}
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def delete_process (self,**params):
        """
        Delete a process from the DB.

        :param process_id: id of the process
        :param collection: name of the collection
        :return: Response message with the name of the collection
        """
        # Delete a process from the DB
        process_id = params["process_id"]
        collection = params["collection"]
        self.db[collection].find_one_and_delete({"process_id": process_id})
        return {"message": f"{collection} deleted successfully"}
     
if __name__ == "__main__":
    with open("shared/config.json", "r") as f:
        config = json.load(f)

    db_endpoints_adaptor = MongoAPI_endpoints(config)
    db_endpoints_adaptor.get_config()
    
    cherrypy.config.update({'server.socket_host': db_endpoints_adaptor.host})
    cherrypy.config.update({'server.socket_port': db_endpoints_adaptor.port})

    cherrypy.tree.mount(db_endpoints_adaptor, '/')
    cherrypy.engine.start()

    print(f"\nDb Endpoints Adaptor runnin on {db_endpoints_adaptor.host}:{db_endpoints_adaptor.port}\n")

    prev_host = db_endpoints_adaptor.host
    prev_port = db_endpoints_adaptor.port
    
    
    while True:
        time.sleep(30)
        db_endpoints_adaptor.get_config()
        if db_endpoints_adaptor.host != prev_host or db_endpoints_adaptor.port != prev_port:
            cherrypy.server.socket_host = db_endpoints_adaptor.host
            cherrypy.server.socket_port = db_endpoints_adaptor.port
            cherrypy.tree.mount(db_endpoints_adaptor, '/')
            cherrypy.engine.start()

            prev_host = db_endpoints_adaptor.host
            prev_port = db_endpoints_adaptor.port
            print("Db Endpoints Adaptor updated: restarted CherryPy server with new host and port!")
        else:
            print("Db Endpoints Adaptor updated: host and port did not change")
        
        

   