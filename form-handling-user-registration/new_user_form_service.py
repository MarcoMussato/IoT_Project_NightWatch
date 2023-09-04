import cherrypy
import json
import time
from jinja2 import Environment, FileSystemLoader
from shared.http_requests import *

class NewUserFormService(object):
    def __init__(self,config):
        """
        Initialize the service.
        :param config: The configuration dictionary for the service.
        """
        self.config = config
        self.chatID = ""
        self.catalog_url = config["catalog_url"] 
        self.service_data = {
            'endpoint_type': 'user_registration_form'
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

    def register(self):
        """
        Register a new user form service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the new user form service data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the new user form service.")
        # If the post response is successfull the new user form service has been registered
        print(response.text)

    @cherrypy.expose
    def index(self, **params):
        """
        Render the HTML form.
 
        :param params: The parameters of the request - the type of form to render (patient or doctor).
        :return: The HTML form.
        """

        if params.get("type") == "doc":
            # Render the HTML form
            with open("form_new_doctor.html") as f:
               return f.read()
        elif params.get("type")=="pat":
            # Retrieve the list of doctors from the MongoDB database
            adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
            # Send a GET request to the data adaptor to retrieve the list of doctors
            action = "get_doctors_list"
            response = self.http_requests.GET(adaptor_data_url, action)
            doctors_list = response.json()
            # Render the HTML form with the doctors list added to the template context
            env = Environment(loader=FileSystemLoader('./templates'))
            template = env.get_template('formNewPatient_CSS.html')
            return template.render(doctors=doctors_list)   
        else:
            raise cherrypy.HTTPError(404)
        
    @cherrypy.expose
    def registration(self,**form_data):
        """
        Save the form data in the MongoDB database, once the form has been submitted.
        :param form_data: The form data.
        :return: Success message or error message.
        :raises Exception: If the form data could not be saved.
        """

        # Send a POST request to the catalog microservice
        if "physician" in form_data.keys():
            action = "add_patient"
            # Make a GET request to the catalog to retrieve the endpoint of the sensor adaptor endpoint
            sensor_adaptor_url = self.http_requests.retrieve_url(endpoint_type="sensor_adaptor")
            # Register sensor when patient is registered
            response = self.http_requests.GET(sensor_adaptor_url, "start_sensor", {"chat_id": form_data["chat_id"]})
            if response.status_code != 200:
                raise Exception("Failed to start sensor.")
            print("Sensor created successfully!")
        else:
            action = "add_doctor"
             # GET request to NODE-RED to create a personalized dashboard
            dashboard_adaptor_url = self.http_requests.retrieve_url("dashboard_adaptor")
            # Create the dashboard
            dashboard_response = self.http_requests.GET(dashboard_adaptor_url, "start_nodered", {"chat_id": form_data["chat_id"]})
            # Check if the dashboard was created successfully
            if dashboard_response.status_code != 200:
                raise Exception("Failed to create the dashboard")
            print("Dashbaord created successfully!")

        # Make a GET request to the catalog to retrieve the endpoint of the mongodb data adaptor
        data_adaptor_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        # Send a POST request to the data adaptor to save the form data
        response=self.http_requests.POST(data_adaptor_url, action, form_data)
        
        if response.status_code != 200:
            raise Exception("Failed to save form data.")
        # If the post response is successfull the form data has been saved
        return "\nNew User form data saved successfully!\n"

if __name__ == "__main__":
    with open("shared/config.json", "r") as f:
        config = json.load(f)
    
    time.sleep(30)
    user_registration_form = NewUserFormService(config)
    user_registration_form.get_config()
    user_registration_form.register()
    
    # If the post response is successfull the BOT has been registered
    print(f"\nNew user form service registered and running on {user_registration_form.host}:{user_registration_form.port}\n")

    cherrypy.config.update({'server.socket_host': user_registration_form.host })
    cherrypy.config.update({'server.socket_port': user_registration_form.port })
    
    cherrypy.tree.mount(user_registration_form, '/')
    cherrypy.engine.start()
    
    prev_host = user_registration_form.host
    prev_port = user_registration_form.port

    while True:
        time.sleep(30)
        user_registration_form.get_config()
        user_registration_form.register()
        if user_registration_form.host != prev_host or user_registration_form.port != prev_port:
            cherrypy.server.socket_host = user_registration_form.host
            cherrypy.server.socket_port = user_registration_form.port
            cherrypy.tree.mount(user_registration_form, '/')
            cherrypy.engine.start()

            prev_host = user_registration_form.host
            prev_port = user_registration_form.port
            print("User registration form updated: restarted CherryPy server with new host and port!")
        else:
            print("User registration form updated: host and port did not change")
        
    
    