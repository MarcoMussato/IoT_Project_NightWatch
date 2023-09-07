import telepot
from telepot.loop import MessageLoop 
import json
from datetime import datetime
import time
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import schedule
from shared.http_requests import *

class SleepApneaBot:
    def __init__(self, config):
        """
        Initialize the bot.
        :param config: The configuration dictionary for the bot.
        """
        self.config = config
        self.catalog_url = config["catalog_url"] 
        self.service_data = {
            'endpoint_type': 'telegram_bot_pat',
        } 
        # Welcome messages to each of the sections
        self.options = {
            '/help': "Here's a list of all the commands:\n/start - Start the bot\n/help - Show this message\n/sleepdiary - manage your sleep diary\n/getreport - manage your sleep apnea reports\n/deleteaccount - delete your account",
            '/start': 'Welcome to the Sleep Apnea Bot! \n\nThis bot will help you to manage your sleep apnea data and fill out your sleep diary. \n\nTo see the list of commands, type /help',
            '/sleepdiary': 'Here you can fill out your sleep diary! 📗',
            '/getreport': 'Here you can see and save your sleep apnea reports! 📁',
            '/deleteaccount': 'Are you sure you want to delete your account? \n\nIf you do, you will not be able to recover your data.'
        }
        self.callbacks = {
            
            'reminder': self.set_reminder,
            'viewdiary': self.view_sleep_diary,
            'filldiary': self.fill_sleep_diary,
            'delete-account': self.delete_account,
            'cancel': self.cancel,
        }
        # Define a dictionary to map button labels to numerical values
        self.form_buttons = {  'sleep_quality_poor':1,
                            'sleep_quality_average':2,
                            'sleep_quality_good':3,
                            'sleep_rested_poor':1,
                            'sleep_rested_average':2,
                            'sleep_rested_good':3,
                            'heavy_meal_yes':1,
                            'heavy_meal_no':0,
                            'yesterday_alcohol_yes':1,
                            'yesterday_alcohol_no' :0}
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
        self.token_bot = config["telegram_token_pat"] 
        self.catalog_url = config["catalog_url"] 
        self.service_data["telegramToken"] = self.token_bot
        # Run the bot
        self.bot = telepot.Bot(self.token_bot)
        MessageLoop(self.bot, {'chat': self.on_chat_message, 'callback_query': self.on_callback_query}).run_as_thread()


    def register(self):
        """
        Register a patients bot service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the bot data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the patients bot.")
        # If the post response is successfull the bot has been registered
        print(response.text)
    
    def on_chat_message(self, msg):
        """
        This method is called when a message is received from the user.
        :param msg: The message received from the user.
        :return: None
        """
        # Extract the content type, chat type and chat id from the message
        content_type, chat_type, self.chat_id = telepot.glance(msg)
        message = msg['text']
    
        # If the message is '/start'
        if message == '/start':
            # Send the start message
            self.send_start_message()
        elif message in self.options:
            # Here we have the welcome message for each of the actions that the TG BOT can do and the help section
            self.bot.sendMessage(self.chat_id, text=self.options[message])
            if message == '/sleepdiary':
                # Here we have the section for managing the sleep diary
                keyboard = InlineKeyboardMarkup(inline_keyboard=[               
                [InlineKeyboardButton(text='Fill out the sleep diary', callback_data='filldiary')]])
                self.bot.sendMessage(self.chat_id, text='👇👇👇👇👇👇👇👇👇👇', reply_markup=keyboard)  
            elif message == '/getreport':
                # Generate the report
                self.get_report()
            elif message == '/deleteaccount':
                # Delete the account
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Yes', callback_data='delete-account')],
                [InlineKeyboardButton(text='No', callback_data='cancel')]])
                self.bot.sendMessage(self.chat_id, text='Are you sure you want to delete your account?', reply_markup=keyboard)
        else:
                self.bot.sendMessage(self.chat_id, text='Please select a valid command')
    
    def on_callback_query(self, msg):
        """
        This method is called when a callback query is received from the user.
        :param msg: The message received from the user.
        :return: None
        """
        # Extract the query id, chat id and query data from the message
        query_id, self.chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        print(query_data)

        # If the query data is in the callbacks dictionary, call the corresponding function
        if query_data in self.callbacks:
            self.callbacks[query_data]()
        
        elif query_data.startswith('time_'):
            # Extract the selected hour and minute from the callback data
            hour, minute = query_data.split('_')[1:]
            # Formating hour and minute to the right format
            reminder_time = f'{hour}:{minute}'
            # Save the selected time to the user's profile
            self.reminder_time = reminder_time
            self.bot.answerCallbackQuery(query_id, text=f'Reminder set for {reminder_time}')
            self.set_reminder_schedule()
                
        elif query_data in self.form_buttons: 
            # Update the user_responses dictionary with the selected value using the rating_scale dictionary.
            self.user_responses[query_data.split('_')[1]] = self.form_buttons[query_data]
            self.bot.answerCallbackQuery(query_id, text=f'{query_data.split("_")[-1]} selected')

        elif query_data == 'submit':
            # Get DB data adaptor url
            adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
            
            # Store the sleep diary in the DB
            api_response = self.http_requests.POST(adaptor_data_url, "store_sleep_diary", self.user_responses)

            if api_response.status_code == 200:
                self.bot.sendMessage(self.chat_id, text='Sleep diary stored successfully!')
            else:
                self.bot.sendMessage(self.chat_id, text='Error storing sleep diary, please try again later.')
            # And clear the user_responses dictionary or list.
            self.user_responses = {}
            self.bot.sendMessage(self.chat_id, text='Thank you for completing the sleep diary')
            
    def send_start_message(self):
        """
        This function sends the welcome message to the patient, check if he/she is registered on the database 
        and send the registration link if needed.
        """

        # Make a GET request to the catalog with the adaptor data as a query parameter
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        
        # Define the action we want to perform on the dabase (in this case check if the patient chat id is present in the DB)
        api_response = self.http_requests.GET(adaptor_data_url, "check_chat_id", {"type": "pat", "chat_id": self.chat_id})
        
        # Check the response status code
        if api_response.status_code == 200:
        # Chat id is invalid (doctor registering for the first time)
            if api_response.text=='invalid':
                start_message = 'Welcome to the Sleep Apnea Bot!👋👋\n'
                start_message += f'This is your chatID, make sure to include in your form:\n👉 **{self.chat_id}** 👈'
                start_message += '\nClick here to register to the platform👇👇'
                
                # Make a GET request to the catalog to retrieve the registration form URL
                registration_url = self.http_requests.retrieve_url(endpoint_type="user_registration_form")
                
                # Create inline keyboard button with the registration link
                button= [[InlineKeyboardButton(text = 'New Patient Registration Form', url = registration_url+"?type=pat", callback_data = 'registration')]]
                keyboard = InlineKeyboardMarkup(inline_keyboard=button)
                self.bot.sendMessage(self.chat_id, text=start_message, reply_markup=keyboard)


            else: #Dr. present in the DB, api_response.text returns the name
                last_name = api_response.text 
                self.bot.sendMessage(self.chat_id, text=f'Welcome to the Sleep Apnea Bot, {last_name}!👋👋\n')
                
        else:
        # Can't connect to the catalog
            self.bot.sendMessage(self.chat_id, text='Unable to connect with the database')

    def get_report(self):
        """
        This function generates the PDF weekly report and sends it to the patient.
        """

        # Retrieve the report generator URL 
        report_generator__url = self.http_requests.retrieve_url(endpoint_type="report_generator")
        
        # Get the report from the report generator service
        response = self.http_requests.GET(report_generator__url, "get_report", {"chat_id": self.chat_id})
        report_path = response.json()["report_file_path"]

        # Send the report to the patient chat
        if report_path is not None:
            with open(report_path, 'rb') as report_file:
                self.bot.sendDocument(self.chat_id, report_file)
        else:
            self.bot.sendMessage(self.chat_id, text='Error generating report')
    
    def delete_account(self):
        """
        This function deletes the patient account from the database and its sensors.
        """

        # Delete the registered sensors from the DB
        sensor_adaptor_url = self.http_requests.retrieve_url(endpoint_type="sensor_adaptor")
        response = self.http_requests.GET(sensor_adaptor_url, "stop_sensor", {"chat_id": self.chat_id})

        # Delete the patient from the DB
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        params = {"type":"pat", "chat_id": self.chat_id}
        api_response = self.http_requests.GET(adaptor_data_url, "delete_account", params=params)
        
        if api_response.status_code == 200:
            self.bot.sendMessage(self.chat_id, text='Account deleted successfully!')
        else:
            self.bot.sendMessage(self.chat_id, text='Error deleting account, please try again later.')
    
    def cancel(self):
        self.bot.sendMessage(self.chat_id, text='Operation cancelled')
    
    def fill_sleep_diary(self):
        """
        This function allows the user to fill out a new sleep diary.
        """
        # Add a dictionary or list to store the user's responses, initializing it as empty
        self.user_responses = {}
        self.user_responses['chat_id'] = str(self.chat_id)
        
        self.bot.sendMessage(self.chat_id, text="Please fill out the sleep diary")
        
        # Create inline keyboard buttons for the rating scale
        sleep_quality_buttons = [
            [InlineKeyboardButton(text='Poorly', callback_data='sleep_quality_poor')],
            [InlineKeyboardButton(text='Average', callback_data='sleep_quality_average')],
            [InlineKeyboardButton(text='Good', callback_data='sleep_quality_good')],
        ]
        sleep_rested_buttons = [
            [InlineKeyboardButton(text='Poorly', callback_data='sleep_rested_poor')],
            [InlineKeyboardButton(text='Average', callback_data='sleep_rested_average')],
            [InlineKeyboardButton(text='Good', callback_data='sleep_rested_good')],
        ]
        heavy_meal_buttons = [
            [InlineKeyboardButton(text='Yes', callback_data='heavy_meal_yes')],
            [InlineKeyboardButton(text='No', callback_data='heavy_meal_no')]
        ]
        alcohol_buttons = [
            [InlineKeyboardButton(text='Yes', callback_data='yesterday_alcohol_yes')],
            [InlineKeyboardButton(text='No', callback_data='yesterday_alcohol_no')]
        ]
        submit_button = InlineKeyboardButton(text='Submit', callback_data='submit')
        
        # Create inline keyboard markup
        sleep_quality_keyboard = InlineKeyboardMarkup(inline_keyboard=sleep_quality_buttons)
        sleep_rested_keyboard = InlineKeyboardMarkup(inline_keyboard=sleep_rested_buttons)
        heavy_meal_keyboard = InlineKeyboardMarkup(inline_keyboard=heavy_meal_buttons)
        alcohol_keyboard = InlineKeyboardMarkup(inline_keyboard=alcohol_buttons)
        submit_keyboard = InlineKeyboardMarkup(inline_keyboard=[[submit_button]])      
        
        # Then use the sendMessage method to send the questions with the corresponding keyboard markup.
        self.bot.sendMessage(self.chat_id, text='How did you sleep?', reply_markup=sleep_quality_keyboard)
        self.bot.sendMessage(self.chat_id, text='Do you feel rested?', reply_markup=sleep_rested_keyboard)
        self.bot.sendMessage(self.chat_id, text='Did you have a heavy meal last night?', reply_markup=heavy_meal_keyboard)
        self.bot.sendMessage(self.chat_id, text='Did you drink alcohol last night?', reply_markup=alcohol_keyboard)
        self.bot.sendMessage(self.chat_id, text='Do you want to submit the diary?', reply_markup=submit_keyboard)

  
if __name__=="__main__":
    
    with open("shared/config.json", "r") as f:
        conf = json.load(f)
    time.sleep(30)
    SA_Bot = SleepApneaBot(conf)
    print("Bot started...")
    SA_Bot.get_config()
    SA_Bot.register()
    print("Patienet Bot registered!")
    
    while True:
        time.sleep(100)
        SA_Bot.get_config()
        SA_Bot.register()
        print("Patient Bot Updated!") 
