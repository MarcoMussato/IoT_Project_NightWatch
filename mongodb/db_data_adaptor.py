import cherrypy
import json
from pymongo import MongoClient
import datetime
import time
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from data_extractor import *
from shared.http_requests import *
import pytz

class MongoAPI_data(object):
    
    def __init__(self, config):
        """
        Initialize the MongoDB adaptor with the configuration parameters
        """
        self.config = config
        self.catalog_url = config["catalog_url"] 
        self.service_data = {
            'endpoint_type': 'adaptor_data',
        }
        self.http_requests = http_requests(self.catalog_url)
        self.last_processed_timestamp = 0
        self.processed_documents = []
    
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
        self.db = self.client[config["database_data"]]
        self.host = config["host"]
        self.port = config["port"]
        self.catalog_url = config["catalog_url"] 
        self.service_data["endpoint_url"] = f'http://{config["host"]}:{config["port"]}'
        
    def register(self):
        """
        Register a data adaptor service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the data adaptor service data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the mongodb adaptor.")
        # If the post response is successfull the data adaptor has been registered
        print(response.text)
        
    @cherrypy.expose
    def check_chat_id(self, **params):
        """
        Check if a given chat ID exists in the database for either a patient or a doctor.

        :param params: A dictionary of query parameters, including the chat ID and the type of new user (pat or doc).
        :type params: dict
        :return: The name of the patient or the last name of the doctor if the chat ID is found, 
                 otherwise 'invalid'.
        :rtype: str
        """


        # Extract the chat ID and chat type from the parameters
        chat_id = params['chat_id']
        chat_type = params.get('type')
        
        # Check if the chat type is for a patient
        if chat_type == 'pat':
            # Retrieve the Patients collection from the database
            patients = self.db['Patients']
            # Check if the chatID parameter matches a patient chatID
            patient = patients.find_one({'chat_id': chat_id})
            if patient:
                 # Return the patient's name if the chatID is found
                return patient["name"]
            # If chatID is not found, return 'invalid'
            print("Patient chat ID not found in the database")
            return 'invalid'

        # Check if the chat type is for a doctor
        if chat_type == 'doc':
            # Retrieve the Doctors collection from the database
            doctors = self.db['Doctors']
            # Check if the chatID parameter matches a doctor chatID
            doctor = doctors.find_one({'chat_id': chat_id})
            if doctor:
                # Return the doctor's last name if the chatID is found
                return doctor["last_name"]
            # If chatID is not found, return 'invalid'
            print("Doctor chat ID not found in the database")
            return 'invalid'
    
    @cherrypy.expose
    def get_doctors_list(self):
        """
        Retrieve a list of all doctors from the MongoDB "Doctors" collection and convert it to a JSON string.

        :param None
        :return: A JSON string representing a list of dictionaries, where each dictionary contains 
                 the doctor's ID and their name.
        :rtype: str
        """

        # Retrieve list of doctors from the MongoDB "Doctors" collection and convert it to a list of dictionaries
        doctors = self.db["Doctors"].find()
        doctors_list = []
        for doctor in doctors:
            # Append each doctor's ID and name to the list
            doctors_list.append({
                "id": str(doctor["_id"]),
                "last_name": "Dr. "+doctor["last_name"]
            })
        # Convert the list to a JSON string and return it as the response body
        return json.dumps(doctors_list)

    @cherrypy.expose
    def get_patient_list(self, **params):
        """
        Retrieve a list of patients associated with a doctor's chat ID from the MongoDB "Patients" collection
        and convert it to a JSON string.

        :param params: A dictionary containing the doctor's chat ID.
        :return: A JSON string representing a list of dictionaries, where each dictionary contains the patient's ID,
                 name, last name, and chat ID.
        :rtype: str
        """

        # Get the doctor's chat ID from the parameters
        doctor_chat_id = params["doctor_chat_id"]
        # Retrieve the doctor's information from the database
        doctor = self.db["Doctors"].find_one({"chat_id": doctor_chat_id})
        # Retrieve the list of patients associated with the doctor's ID
        patients = self.db["Patients"].find({"doctor_id": doctor["_id"]})
        # Convert the list of patients to a list of dictionaries
        patients_list = []
        for patient in patients:
            # Append each patient's ID, name, last name, and chat ID to the list
            patients_list.append({
                "id": str(patient["_id"]),
                "name": patient["name"],
                "last_name": patient["last_name"],
                "chat_id": patient["chat_id"]
            })
        # Print the list of patients (for debugging purposes)
        print(patients_list)
        # Convert the list to a JSON string and return it as the response body
        return json.dumps(patients_list)
    
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def add_patient(self, **form_data):
        """
        Add a new patient to the Patients collection in the MongoDB database.

        :param form_data: A dictionary containing the patient's name, last name, date of birth, doctor's name, chat ID, sensor ID, wake-up time, and fall asleep time.
        :return: A success message indicating that the patient has been added to the database.
        """
        # Get the patients and doctors collection
        patients_collection = self.db["Patients"]
        doctors_collection = self.db["Doctors"]
        
        # Parse the JSON data sent in the request
        form_data = cherrypy.request.json

        # Find the doctor document by name
        physician= form_data['physician']
        physician_last_name = physician[4:]
        physician_doc = None
        for doc in doctors_collection.find({'last_name': physician_last_name}):
            physician_doc = doc
            break

        # Create a new patient document
        new_patient = {
            "name": form_data["name"],
            "last_name": form_data["last_name"],
            "dob": int(datetime.strptime(form_data["dob"], "%Y-%m-%d").timestamp()),
            "doctor_id": physician_doc['_id'],
            "chat_id": form_data["chat_id"],
            "wake_up_time": form_data["wake_up_time"],
            "fall_asleep_time": form_data["fall_asleep_time"],
            "sleep_diary_entries": [],
            "sleep_sensor_data": [],
            "sleep_analytics": []
        }

        # Insert the new patient document into the patients collection
        patients_collection.insert_one(new_patient)

        # Add the new patient to the right doctor's patient list
        doctors_collection.update_one(
            {'_id': physician_doc['_id']},
            {'$push': {'patients': new_patient['_id']}}
        )

        # Return a success message to the client
        return "Patient added successfully"
     
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def add_doctor(self, **form_data):
        """
        Add a new doctor to the MongoDB database and create a personalized dashboard for the doctor using a GET request to a catalog service.
        :param form_data: JSON data containing the form data submitted in the request.
        :return: A success message indicating that the doctor was added successfully.
        """

        # Get the doctors collection
        doctors_collection = self.db["Doctors"]
        
        # Retrieve the form data from the request and store it in the variable `form_data`
        form_data = cherrypy.request.json
        
        # Create a new doctor object from the form data
        new_doc = {
            "name": form_data["name"],
            "last_name": form_data["last_name"],
            "dob": int(datetime.strptime(form_data["dob"], "%Y-%m-%d").timestamp()),
            "chat_id": form_data["chat_id"],
            "username": form_data["username"],
            "password": form_data["password"]
        }
        
        # Insert the new doctor object into the MongoDB database
        doctors_collection.insert_one(new_doc)
        return "Doctor added successfully!"
    
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def store_sleep_diary(self):
        """
        Store a new sleep diary entry in the database (received from a post request) and link it to the correct patient.

        :return: A success message and the stored sleep diary.
        :raises cherrypy.HTTPError: If the patient cannot be found in the database.
        """

        patients_collection = self.db["Patients"]
        sleep_diary_collection = self.db["Sleep Diary"]

        # Retrieve the form data from the request and store it in the variable `form_data`
        form_data = cherrypy.request.json
        form_data["date"] = datetime.now().timestamp()
        # Insert the sleep diary in the sleep diary collection and get the inserted object id
        inserted_id = sleep_diary_collection.insert_one(form_data).inserted_id
        
        # Insert the id in the correct patient
        
        # Find the patient in the database using their chat ID
        patient = patients_collection.find_one({"chat_id": form_data["chat_id"]})
        if patient is None:
            # Return an error response if the patient is not found
            cherrypy.response.status = 404
            return "Patient not found"

        # Append the sleep diary's object id to the patient's existing data
        patient["sleep_diary_entries"].append(inserted_id)
        patients_collection.replace_one({"_id": patient["_id"]}, patient)

        # Return a success response with the stored sleep diary
        return f"Sleep diary stored successfully: \n {form_data}"

    @cherrypy.expose
    def get_last_week_data(self, **params):
        """
        Retrieve sleep data for a patient for the last seven days.

        :param params: A dictionary containing the chat_id of the patient.
        :return: A JSON string containing the sleep data for the last week.
        """
        # Get the chat_id from the parameters
        chat_id = params['chat_id']
        
        # Get the collections for patients, sleep diary, and sleep analytics
        patients_col = self.db["Patients"]
        sleep_diary_col = self.db["Sleep Diary"]
        sleep_analytics_col = self.db["Sleep Analytics"]
        
        # Retrieve the patient based on the chat_id
        patient = patients_col.find_one({"chat_id": chat_id})
        if not patient:
            return "Patient not found"
        patient_id = str(patient["_id"])
        
        # Retrieve the documents from the last seven days
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Create a query for the documents that have the right patientID and the dates of the last 7 days
        patient_query = { "chat_id" : str(chat_id), "date": {"$gte": seven_days_ago.timestamp()} }
        # Retrieve all the patients data
        sleep_diary_data = list(sleep_diary_col.find(patient_query))
        for doc in sleep_diary_data:
            doc["_id"] = str(doc["_id"])
        
        # Create a query for the documents that have the right patientID and the dates of the last 7 days
        patient_query = { "patient_id" : patient_id, "date": {"$gte": seven_days_ago.timestamp()} }
        # Retrieve all the patients data
        sleep_analytics_data = list(sleep_analytics_col.find(patient_query))
        for doc in sleep_analytics_data:
            doc["_id"] = str(doc["_id"])
        
        last_week_data = {"sleep_diary_data": sleep_diary_data, "sleep_analytics_data": sleep_analytics_data, "patient_id":patient_id}

        return json.dumps(last_week_data)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def login(self, username=None, password=None):
        """
        Retrieve the list of patients associated with a doctor from the database.

        :param username: A string representing the doctor's username.
        :param password: A string representing the doctor's password.
        :return: A dictionary containing the list of patients associated with the doctor
        and the doctor's name, returned as a JSON response. 
        If the username and password are incorrect, returns an error message as a string.
        """
        doctors = self.db['Doctors']
        patients = self.db['Patients']
        # Find the doctor with the given username and password
        doctor = doctors.find_one({"username": username, "password": password})

        if doctor is not None:
            # Get the list of patients associated with the doctor
            try: 
                patient_ids = doctor["patients"]

                # Get the patient information for each patient id
                info = {"patient_list":[], "doc_name" : doctor["last_name"]}
                for patient_id in patient_ids:
                    # Convert patient_id from string to ObjectId
                    patient_id = ObjectId(patient_id) 
                    # Get patient document
                    patient = patients.find_one({"_id": patient_id})
                    # Get patient name
                    key_name = patient["name"]+" "+patient["last_name"]
                    # Convert patient_id to string
                    val = str(patient_id)
                    # Add patient name and id to patient_names list
                    info["patient_list"].append({f"{key_name}": val})  
                # Return the patient information as a JSON response
                return info
            except KeyError:
                return {"message":"No patients found", "doc_name": doctor["last_name"]}
        else:
            # Return an error message if the username and password are incorrect
            return {"message": "Username or password incorrect"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_sleep_data(self, patient_id, timeframe):
        """
        Retrieve sleep data for a patient from the database.

        :param patient_id: A string representing the patient's id.
        :param timeframe: A string representing the timeframe for which to retrieve the data. 
        Can be '1' for a single day, '2' for the past week, or '3' for the past month.
        :return: A dictionary containing the sleep data for the patient, returned as a JSON response.
        """
        patient_id = patient_id
        data_function= dataExtractor(self.db["Sleep Sensor Data"],self.db["Sleep Analytics"])
        # Initialize a dictionary to store the sleep data
        sleep_data = {
            "ecg":[],
            "snoring":[],
            "spo2":[],
            "n_episods": 0,
            "max_episods" :0,
            "day_max_ep":0,
            "avg_time_ep":0 }
        #
        # Set the timezone to Houston
        local_timezone = pytz.timezone('UTC')
        # Get the current date and time
        now = datetime.now(local_timezone)
        # Replace the hour, minute and second values with 0, 0 and 0 respectively
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Convert the datetime object to Unix timestamp
        start_date = int(today.timestamp())

        #start_date = 1677283200
        if timeframe == '2':
            end_date = start_date - 604800 #one week in seconds
            sleep_data = data_function.multiple_day(start_date, end_date, sleep_data, patient_id)
            return sleep_data
        elif timeframe == '3': 
            end_date = start_date - 2592000 #one month (30 day) in seconds
            sleep_data = data_function.multiple_day(start_date, end_date, sleep_data, patient_id)
            return sleep_data
        else: 
            sleep_data = data_function.single_day(start_date, sleep_data, patient_id)
            return sleep_data

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def check_end_night(self,**params):
        """
        Retrieve documents from the Sleep Sensor Data collection based on a given time range.

        :param params: A dictionary containing parameters for the request, including "time" (Unix timestamp).
        :return: A list of documents from the Sleep Sensor Data collection that meet the time criteria and
        do not have a matching document in the Sleep Analytics collection.
        """
        check_time = int(params["time"])
        # Get the required collections
        collection_data = self.db["Sleep Sensor Data"]
        collection_analytics = self.db["Sleep Analytics"]
        # Initialize an empty list to store the documents that fulfill the request
        docs_to_return = []
        # Loop through the documents in Sleep Sensor Data that meet the time criteria
        for doc in collection_data.find({'updated_at': {'$gte': check_time - 32400, '$lte': check_time - 300}}):
            # Get the patient ID and the date from the document
            patient_id = str(doc['patient_id'])
            date = doc["date"]
            # Check if a document already exists in the Sleep Analytics collection with the same patient ID and date
            existing_doc = collection_analytics.find_one({'patient_id': patient_id, 'date': date})
            # If there's no matching document in the Sleep Analytics collection, add the current document to the docs_to_return list
            if not existing_doc:
                doc['_id'] = str(doc['_id'])
                docs_to_return.append(doc)
        # Return the list of documents that fulfill the request
        return docs_to_return

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def find_data_document(self,**params):
        """
        Search for a sleep data document with the given patient's 
        sensor_id and a time range, and return the sleep data _id if found.

        :param params: A dictionary containing the following parameters:
                - sensor_id: The sensor_id of the patient whose sleep data is to be retrieved.
                - time: The time (in Unix timestamp format) when the sleep data was recorded.
        :return: The _id of the sleep data document if found, otherwise return a
        dictionary with the message "Patient not found." or "Sleep data not found." 
        """ 
        sensor_id = params["sensor_id"] #sensor_id of the patient whose sleep data is to be retrieved
        time = int(params["time"]) #timestamp of the time in which the data was requested
        # Search for the patient with the given sensor_id
        patient_collection = self.db['Patients']
        patient = patient_collection.find_one({'chat_id': sensor_id})
        if patient is None:
            return {'message': 'Patient not found.'}
        # Extract the patient_id from the patient document
        patient_id = str(patient['_id'])
        # Search for a sleep data document with the given date and patient_id
        sleep_data_collection = self.db['Sleep Sensor Data']
        try: 
            sleep_data = sleep_data_collection.find_one({'updated_at': {'$gte': time - 10800, '$lte': time}},{'patient_id': patient_id})
            if sleep_data is None:
                return {'message': 'Sleep data not found.'}
            # Extract the _id from the sleep data document
            sleep_data_id = str(sleep_data['_id'])
             # Return the sleep data _id
            return sleep_data_id 
        except: 
            return {'message': 'Sleep data not found.'}
        
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def create_data_document(self, **params):
        """
        Insert sleep data for a patient into the database.
        :param params: A dictionary containing the parameters for inserting the data. 
        Must include the following keys: 'type', 'sensor_id', and 'data_type'.
        :param data: A dictionary containing the sleep data to insert into the database.
        :return: A string representing the ID of the newly created document in the database.
        """
        type = params["type"]
        data = cherrypy.request.json
        
        if type == "data": 
            collection = self.db["Sleep Sensor Data"]
            sensor_id = params["sensor_id"]
            data_type = params["data_type"]
            
            # Find the patient with the given sensor_id
            patient = self.db["Patients"].find_one({'chat_id': sensor_id})
            if patient is None:
                raise cherrypy.HTTPError(404, "Patient not found")

            # Get the patient ID as a string
            patient_id = str(patient['_id'])
            # get current date and time
            current_datetime = datetime.now()
            # create a new datetime object with the same date but at 00:00:00 time
            midnight_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            # convert midnight datetime to Unix timestamp and add one day
            date = int(midnight_datetime.timestamp())+86400
            creation_time = int(current_datetime.timestamp())
            # Create a new document in SleepData collection with empty vectors
            sleep_data = {'patient_id': patient_id, 'date' : date, 'updated_at':creation_time, 'ecg_data': [], 'snoring_data': [], 'spo2_data': []}

            if data_type == 'HR':
                sleep_data["ecg_data"].append(data)
            elif data_type == 'snor':
                sleep_data["snoring_data"].append(data)
            elif data_type == 'spo2':
                sleep_data["spo2_data"].append(data)
            else:
                return {'message': 'Invalid data type.'}
        elif type == "analytics":
            collection = self.db["Sleep Analytics"] 
            sleep_data = data
        result = collection.insert_one(sleep_data)
        # Get the ID of the newly created document
        document_id = str(result.inserted_id)

        return document_id

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def update_data_document(self, **params):
        """
        Update sleep data for a patient in the database. 
        :param document_id: A string representing the id of the document containing the sleep data.
        :param data_type: A string representing the type of data to be updated. Can be 'HR' for ECG data, 'snor' for snoring data, or 'spo2' for SPO2 data.
        :return: A dictionary containing a message indicating the success or failure of the update operation.
        """
        document_id = params["document_id"]
        data_type = params["data_type"]
        # Convert document_id to ObjectId and search for the sleep data document
        sleep_data_collection = self.db['Sleep Sensor Data']
        sleep_data = sleep_data_collection.find_one({'_id': ObjectId(document_id)})
        if sleep_data is None:
            return {'message': 'Sleep data not found.'}
        # Get the data vector and update it with the values from the request body
        data_field = None
        if data_type == 'HR':
            data_field = 'ecg_data'
        elif data_type == 'snor':
            data_field = 'snoring_data'
        elif data_type == 'spo2':
            data_field = 'spo2_data'
        else:
            return {'message': 'Invalid data type.'}
        request_body = cherrypy.request.json
        data_vector = sleep_data.get(data_field, [])
        if not isinstance(data_vector, list):
            return {'message': f'{data_field} field is not a list.'}
        data_vector.append(request_body)
        # Update the sleep data document with the new data vector
        result = sleep_data_collection.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {data_field: data_vector, 'updated_at': int(datetime.now().timestamp())}}
        )
        if result.matched_count != 1:
            return {'message': 'Failed to update sleep data.'}
        return {'message': 'Sleep data updated successfully.'}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def patient_info(self, **params):
        """
        Get patient information from the database.
        :param patient_id: A string representing the id of the patient.
        :return: A dictionary containing the patient information.
        """
        chat_id = str(params["id"])  # Cast to string if the chat_id is stored as a string in the database

        # Convert patient_id to ObjectId and search for the patient document
        patient_collection = self.db['Patients']
        patient = patient_collection.find_one({'chat_id': chat_id})
        if patient is None:
            return {'message': 'Patient not found.'}
        patient["_id"] = str(patient['_id'])
        patient["doctor_id"] = str(patient['doctor_id'])
        return patient
    
    @cherrypy.expose
    def delete_account(self, **params):
        """
        Delete a patient or doctor account from the database.

        :param params: A dictionary containing the chat_id of the patient or doctor and the type of account.
        :return: A success message.
        """
        #delete the patient or the doctor account from the database
        if params["type"] == "pat":
            patients_collection = self.db["Patients"]
            patients_collection.find_one_and_delete({"chat_id": params["chat_id"]})
        elif params["type"] == "doc":
            doctors_collection = self.db["Doctors"]
            doctors_collection.find_one_and_delete({"chat_id": params["chat_id"]})
        return "Account deleted successfully."
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def find_doctor_patients(self, **params):
        """
        Find doctors and associated patients based on the provided timestamp.

        :param params: A dictionary containing the timestamp of the request.
        :return: A list of dictionaries containing doctors' chat_IDs and their associated patient info.
        """
        timestamp = int(params["timestamp"])
        # Reset the processed_documents if it's been more than 24 hours
        if self.last_processed_timestamp:
            time_difference = timestamp - self.last_processed_timestamp
            if time_difference >= 24*60*60:  # 24 hours in seconds
                self.processed_documents = []
                self.last_processed_timestamp = timestamp
        else:
            self.last_processed_timestamp = timestamp
            self.processed_documents = []  
            
            
        # Search Sleep Analytics collection
        sleep_analytics = self.db['Sleep Analytics']
        documents = list(sleep_analytics.find({'date': timestamp}))

        # Initialize lists for current request
        patient_data_list = []  # Updated from patientIDs
        doctors_info = [] # Updated from doctorIDs
    
        # Iterate through the cursor
        for doc in documents:
            # Check if the document meets the criteria
            if int(doc['total apnea episodes']) > 40 and str(doc['_id']) not in self.processed_documents:
                
                patient_doc = self.db["Patients"].find_one({'_id': ObjectId(doc['patient_id'])})
                # Extract and structure the patient info
                if patient_doc:
                    patient_data = {
                        'id': str(doc['_id']),
                        'patient_id': str(patient_doc['_id']),
                        'name': patient_doc['name'],
                        'surname': patient_doc['last_name']
                    }
                    patient_data_list.append(patient_data)
                self.processed_documents.append(str(doc['_id']))
        
        # Search the Doctors collection
        doctors = self.db['Doctors']
        # Iterate through the patient_data_list
        for patient_data in patient_data_list:
            # Find the doctor associated with the patient
            doctor_doc = doctors.find_one({'patients': ObjectId(patient_data['patient_id'])})
            # Extract and structure the info
            if doctor_doc:
                # Extract and structure the info
                info = {
                    'doctor_chat_ID': doctor_doc['chat_id'],
                    'patient_name': patient_data['name'], 
                    'patient_surname': patient_data['surname'],
                }
                doctors_info.append(info)
        # Return the list of doctors and associated patients
        return doctors_info


if __name__ == "__main__":
     
    with open("shared/config.json", "r") as f:
        config = json.load(f)

    db_data_adaptor = MongoAPI_data(config)
    time.sleep(10)
    db_data_adaptor.get_config()
    db_data_adaptor.register()

    print(f"Db Data Adaptor registered and runnin on {db_data_adaptor.host}:{db_data_adaptor.port}")

    cherrypy.config.update({'server.socket_host': db_data_adaptor.host})
    cherrypy.config.update({'server.socket_port': db_data_adaptor.port})

    cherrypy.tree.mount(db_data_adaptor, '/')
    cherrypy.engine.start()

    prev_host = db_data_adaptor.host
    prev_port = db_data_adaptor.port

    while True:
        time.sleep(30)
        db_data_adaptor.get_config()
        db_data_adaptor.register()
        if db_data_adaptor.host != prev_host or db_data_adaptor.port != prev_port:
            cherrypy.server.socket_host = db_data_adaptor.host
            cherrypy.server.socket_port = db_data_adaptor.port
            cherrypy.tree.mount(db_data_adaptor, '/')
            cherrypy.engine.start()

            prev_host = db_data_adaptor.host
            prev_port = db_data_adaptor.port
            print("Db Data Adaptor updated: restarted CherryPy server with new host and port!")
        else:
            print("Db Data Adaptor updated: host and port did not change")

    
