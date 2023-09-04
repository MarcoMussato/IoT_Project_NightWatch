import telepot 
from telepot.loop import MessageLoop 
import json
from datetime import time
import time
import paho.mqtt.client as MQTT
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from shared.http_requests import *

class SleepApneaBotDoc:

    def __init__(self, config):
        """
        Initialize the bot.
        :param config: The configuration dictionary for the bot.
        """
        self.config = config
        self.catalog_url = config["catalog_url"] 
        self.service_data = {
            'endpoint_type': 'telegram_bot_doc',
        } 
        # Welcome messages to each of the sections
        self.options = {
            '/start': 'Welcome to the Sleep Apnea Bot! \n\nThis bot will help you to manage your patients and to see their data in a dashboard. \n\nTo see the list of commands, type /help',
            '/help': "Here's a list of all the commands:\n/start - start the bot\n/help - show this message\n/getreport - get a weekly report of one of your patients\n/viewdashboard - see the interactive dashboard in NODE-RED\n/deleteaccount - delete your account",
            '/viewdashboard': 'In the this dashboard, you will see all of your patients data!',
            '/getreport' : 'In a few moment you will be able to download a weekly report of one of your patients',
            '/deleteaccount': 'Are you sure you want to delete your account? \n\nIf you do, you will not be able to recover your data.'
        }
        
        self.chat_id="" 
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
        self.token_bot = config["telegram_token_doc"] 
        self.catalog_url = config["catalog_url"] 
        self.service_data["telegramToken"] = self.token_bot
        self.broker= config["broker"]
        self.clientID=config["clientID"]
        self.port = config["port"]
        self.topic= config["base_topic"]+'/#'
        self.client = MQTT.Client(self.clientID, True)	
        
        # Create the MQTT client
        self.client.on_connect = self.myOnConnect
        self.client.on_message = self.myOnMessageRec
        
        # Run the bot
        self.bot = telepot.Bot(self.token_bot)
        MessageLoop(self.bot, {'chat': self.on_chat_message, 'callback_query': self.on_callback_query}).run_as_thread()
        
        
    def register(self):
        """
        Register a doctors bot service by making a POST request to the catalog to register the service.

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
        """
        
        # Extract the topic from the message
        full_topic = msg.topic
        topic_fields = full_topic.split("/")
        doctor_chat_id = topic_fields[2]
        # Extract the message from the message
        message= json.loads(msg.payload)
        
        # Send the message to the doctor
        self.bot.sendMessage(str(doctor_chat_id), text=message)
        
    def on_chat_message(self, msg):
        """
        This function is called when a message is received from the user.
        :param msg: The message received from the user.
        :return: None
        """

        content_type, chat_type, self.chat_id = telepot.glance(msg)
        message = msg['text']
        
        if message in self.options:
            # Here we have the welcome message for each of the actions that the TG BOT can do and the help section
            self.bot.sendMessage(self.chat_id, text=self.options[message]) 

            # If the message is '/start'
            if message == '/start':
                # Send the welcome messages and the registration link if needed
                self.send_start_message() 
            
            elif message == '/viewdashboard':
                # Show the dashboard link 
                self.see_dashboard()

            elif message == '/getreport':
                # Generate the report of one his patients
                self.get_report()
            
            elif message == '/deleteaccount':
                # Delete the account
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Yes', callback_data='delete-account')],
                [InlineKeyboardButton(text='No', callback_data='cancel')]])
                self.bot.sendMessage(self.chat_id, text='Are you sure you want to delete your account?', reply_markup=keyboard)
        else:
                self.bot.sendMessage(self.chat_id, text="Command not found")

    def on_callback_query(self, msg):
        """
        This function is called when a callback query is received from the user.
        :param msg: The message received from the user.
        :return: None
        """
        # Extract the query data from the message
        query_id, self.chat_id, query_data = telepot.glance(msg, flavor='callback_query')

        # If query_data starts with "patient", call get_report method
        if query_data.startswith('patient'):
            
            # Extract the patient chat id from the query data
            patient_chat_id = query_data.split('_')[1]

            # Retrieve the report generator URL 
            report_generator__url = self.http_requests.retrieve_url(endpoint_type="report_generator")
            
            # Get the report for the selected patient
            response = self.http_requests.GET(report_generator__url, "get_report", {"chat_id": patient_chat_id})
            report_path = response.json()["report_file_path"]
        
            if report_path is not None:
                with open(report_path, 'rb') as report_file:
                    self.bot.sendDocument(self.chat_id, report_file)
            else:
                self.bot.sendMessage(self.chat_id, text='Error generating report')
        elif query_data == 'registration':
            self.bot.sendMessage(self.chat_id, text='Thank you for registering!')
        elif query_data == 'delete-account':
            self.delete_account()
        elif query_data == 'cancel':
            self.bot.sendMessage(self.chat_id, text='Operation cancelled')
            
    def send_start_message(self):
        """
        This function sends the welcome message to the doctorm, check if he/she is registered on the database 
        and send the registration link if needed.
        """

        # Make a GET request to the catalog with the adaptor data as a query parameter
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        
        # Check if the doctor chat id is present in the DB
        response = self.http_requests.GET(adaptor_data_url, "check_chat_id", {"type": "doc", "chat_id": self.chat_id})
        
        # Check the response status code
        if response.status_code == 200:
        # Chat id is invalid (doctor registering for the first time)
            if response.text=='invalid':
                start_message = 'Welcome to the Sleep Apnea Bot!👋👋\n'
                start_message += f'This is your chatID, make sure to include in your form:\n👉 **{self.chat_id}** 👈'
                start_message += '\nClick here to register to the platform👇👇'
                 
                # Retrieve the registration form endpoint from the catalog
                registration_url = self.http_requests.retrieve_url(endpoint_type="user_registration_form")
                # Create inline keyboard button with the registration link 
                registration_url = registration_url+"?type=doc"
                button= [[InlineKeyboardButton(text='New Doctor Registration Form', url=registration_url, callback_data='registration')]]
                keyboard = InlineKeyboardMarkup(inline_keyboard=button)
                self.bot.sendMessage(self.chat_id, text=start_message, reply_markup=keyboard)  
               
            else: #Dr. present in the DB, api_response.text returns the name
                last_name = response.text 
                self.bot.sendMessage(self.chat_id, text=f'Welcome to the Sleep Apnea Bot, Dr. {last_name}!👋👋\n')
                
        else:
        # Can't connect to the catalog
            self.bot.sendMessage(self.chat_id, text='Unable to connect with the database')    
    
    def see_dashboard(self):
        """
        This function sends the personalized NODE-RED dashboard link to the doctor.
        """

        # GET request to the endpoints_adaptor to retrieve the dashboard link
        response = self.http_requests.GET(self.catalog_url, "get_process", {"process_id": self.chat_id, "collection": "Dashboard Processes", "option": "normal"})
        # Extract the dashboard link from the response
        dashboard_url = response.json()["process_url"]

        # Create inline keyboard button with the NODE-RED dashboard link 
        button= [[InlineKeyboardButton(text='Visit the interactive dashboard', url=dashboard_url+"/ui",callback_data='see-dashboard')]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=button)
        self.bot.sendMessage(self.chat_id, text="Click the following link to see the dashboard with all your patients data 👇👇", reply_markup=keyboard)

    def get_report(self):
        """
        This function retrieves the list of patients from the DB, create inline keyboard buttons for each patient and ask the doctor which patient to retrieve the report for.
        """

        # Retrieve the list of patients
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        patients = self.http_requests.GET(adaptor_data_url,"get_patient_list", {"doctor_chat_id": self.chat_id})
        patient_list = patients.json()

        if patient_list:
            # Create inline keyboard buttons for each patient
            patient_buttons = []
            for patient in patient_list:
                button = InlineKeyboardButton(text=f"{patient['name']} {patient['last_name']}", callback_data='patient_' + patient['chat_id'])
                patient_buttons.append([button])
            patient_keyboard = InlineKeyboardMarkup(inline_keyboard=patient_buttons)

            # Ask the doctor which patient to retrieve the report for
            self.bot.sendMessage(self.chat_id, text='Which patient do you want to see the report for?', reply_markup=patient_keyboard)
        else: 
            # Ask the doctor which patient to retrieve the report for
            self.bot.sendMessage(self.chat_id, text='There are no patients registered, add a patient first!')

    def delete_account(self):
        """
        This function deletes the doctor from the DB and stops the NODE-RED dashboard.
        """
        
        # Make a GET request to the catalog to retrieve the endpoint of the NODE-RED adaptor endpoint
        dashboard_url = self.http_requests.retrieve_url(endpoint_type="dashboard_adaptor")
        # Make a GET request to the NODE-RED adaptor to stop the dashboard for the doctor
        api_response = self.http_requests.GET(dashboard_url, "stop_nodered", {"chat_id": self.chat_id})
        
        if api_response.status_code != 200:
            print("Dashboard process deletion failed")
            raise Exception("Failed to delete the document on the database.")
            
        # Make a GET request to the catalog with the adaptor data as a query parameter
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        # Delete the doctor from the DB
    
        api_response = self.http_requests.GET(adaptor_data_url,"delete_account", {"type":"doc", "chat_id": self.chat_id})

        if api_response.status_code == 200:
            self.bot.sendMessage(self.chat_id, text='Account deleted successfully!')
        else:
            self.bot.sendMessage(self.chat_id, text='Error deleting account, please try again later.')
            
        
if __name__=="__main__":

    with open("shared/config.json", "r") as f:
        conf = json.load(f)
    time.sleep(30)
    SA_Bot = SleepApneaBotDoc(conf)
    print("Bot started...")
    SA_Bot.get_config()
    SA_Bot.register()
    SA_Bot.start()
    print("Doctor Bot registered!")
    
    while True:
        time.sleep(100)
        SA_Bot.get_config()
        SA_Bot.register() 
        print("Doctor Bot updated!")
