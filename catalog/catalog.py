import cherrypy
import json
from shared.http_requests import *
import time

class SleepApneaCatalog:
    def __init__(self, config):
        """
        Initialize the catalog.
        :param config: The configuration dictionary for the catalog.
        """
        self.adaptor_endpoints_url=f'http://{config["adaptor_endpoints"]["host"]}:{config["adaptor_endpoints"]["port"]}'
        self.config = config
        self.host = config["host"]
        self.port = config["port"]
        self.catalog_url = f'http://{self.host}:{self.port}'
        self.http_requests = http_requests(self.catalog_url)

    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_config(self,**params): 
        """
        Retrieve the configuration of the requested service.

        :param params: The parameters of the request - the endpoint_type.
        :return: The configuration of the requested service.
        """

        try:
            endpoint_type = params["endpoint_type"]
            # Load the configuration file
            with open("config_catalog.json", "r") as f:
                self.config = json.load(f)

            # Return the configuration of the requested service
            if endpoint_type in self.config:
                config = self.config[endpoint_type]
                config["catalog_url"] = f'http://{self.host}:{self.port}'
                return config
            else:
                raise ValueError(f"Could not retrieve config for endpoint_type {endpoint_type}.")
        except ValueError as e:
            raise cherrypy.HTTPError(400, str(e))

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def register_service(self):
        """
        Register a new service in the endpoints DB and update the service if it already exists.

        :body Service data
        :return: Response message with the name of the registered service
        """
        try:
            service_data = cherrypy.request.json
            endpoint_type = service_data["endpoint_type"]

            # Make a POST request to the mongodb adaptor to register the service
            response = self.http_requests.POST(self.adaptor_endpoints_url, "register_service", service_data)

            if response.status_code == 200:
                print(f"\n{response.text}")
                return response.text
            else:
                raise ValueError(f"Could not register service {endpoint_type}. Response status code: {response.status_code}")
        except ValueError as e:
            raise cherrypy.HTTPError(400, str(e))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def retrieve_endpoint(self,**params):
        """
        Retrieve the endpoint of the requested service.

        :param params: The parameters of the request - the endpoint_type.
        :return: The endpoint of the requested service.
        """
        try:
            endpoint_type = params["endpoint_type"]

            if endpoint_type != "adaptor_endpoints":
                response = self.http_requests.GET(self.adaptor_endpoints_url, "retrieve_endpoint_url", params)

                if response.status_code == 200:
                    endpoint_url = response.json()["endpoint_url"]
                    print(f"\n{endpoint_type} url retrieved successfully")
                    return endpoint_url
                else:
                    raise ValueError(f"Could not retrieve endpoint_info for endpoint_type {endpoint_type}. Response status code: {response.status_code}")
            else:
                endpoint_url = self.adaptor_endpoints_url
                print(f"\nadaptor_endpoint url retrieved successfully")
                return endpoint_url
        except ValueError as e:
            raise cherrypy.HTTPError(400, str(e))
   
    def delete_service(self,):
        """
        Delete a service from the endpoints DB if it has not been updated in the last 20 minutes.

        :return: print the deleted services
        """
        
        try:
            response = self.http_requests.DELETE(self.adaptor_endpoints_url, "delete_service")

            if response.status_code == 200:
                if response.json()["Deleted services"] == []:
                    pass
                else:
                    print(f"\nList deleted services:\n{response.json()['Deleted services']}\n")
            else:
                raise ValueError("Could not delete the service.")
        except ValueError as e:
            raise cherrypy.HTTPError(400, str(e))
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_process (self,**params):
        """
        Get process from the DB
        
        :param params: The parameters of the request - the process_id.
        :return: The process of the requested process_id.
        """
        action = "get_process"
        try:
            response = self.http_requests.GET(self.adaptor_endpoints_url, action=action, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise cherrypy.HTTPError(400, f"Failed to retrieve {action} from: {self.adaptor_endpoints_url}: {e}")
        return response.json()
    
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def create_process (self,**params):
        """
        Create document in the DB
        
        :body Process data
        :return: Response message with the name of the registered process
        """

        payload = cherrypy.request.json
        action="create_process"
        try:
            response = self.http_requests.POST(self.adaptor_endpoints_url,action = action, payload = payload, params = params)
            response.raise_for_status() # raise exception for 4xx and 5xx status codes
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to retrieve {action} from: {self.adaptor_endpoints_url}: {e}"
            raise Exception(error_msg)
        return response.text
        
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def update_process (self,**params):
        """
        Update document in the DB
        
        :body Process data
        :return: Response message with the name of the registered process
        """

        payload = cherrypy.request.json
        action="update_process"

        try:
            response = self.http_requests.PUT(self.adaptor_endpoints_url, action=action, payload=payload, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise cherrypy.HTTPError(400, f"Failed to retrieve {action} from: {self.adaptor_endpoints_url}: {e}")
        return response.text
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def delete_process (self,**params):
        """
        Delete document from the DB
        
        :param params: The parameters of the request - the process_id.
        :return: The process of the requested process_id.
        """
        
        action="delete_process"
        try:
            response = self.http_requests.DELETE(self.adaptor_endpoints_url, action=action, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise cherrypy.HTTPError(400, f"Failed to retrieve {action} from: {self.adaptor_endpoints_url}: {e}")
        return response.text
        
        
        
if __name__ == '__main__':
    
    with open("config_catalog.json", "r") as f:
        config = json.load(f)
    
    sleep_apnea_catalog = SleepApneaCatalog(config)
    
    cherrypy.config.update({'server.socket_host': sleep_apnea_catalog.host})
    cherrypy.config.update({'server.socket_port': sleep_apnea_catalog.port})
    cherrypy.tree.mount(sleep_apnea_catalog, '/')
    cherrypy.engine.start()

    print(f"\nCatalog runnin on {sleep_apnea_catalog.host}:{sleep_apnea_catalog.port}\n")

    while True:
        # Delete services that have not been updated in the last 10 minutes
        time.sleep(30)
        sleep_apnea_catalog.delete_service()
        

