import cherrypy
import json
import time
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import numpy as np
from datetime import datetime, timedelta
from weasyprint import HTML
from shared.http_requests import *
import matplotlib
matplotlib.use('Agg')

class report_generator:
  
    def __init__(self,config):
        """
        Initialize the service.
        :param config: The configuration dictionary for the service.
        """
        self.chatID = ""
        self.config = ""
        self.catalog_url = config["catalog_url"] 
        self.config = ""
        self.service_data = {
            'endpoint_type': 'report_generator',
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

        self.host = config["host"] 
        self.port = config["port"] 
        self.service_data["endpoint_url"] = f'http://{config["host"]}:{config["port"]}'
        self.catalog_url = config["catalog_url"] 

    def register(self):
        """
        Register a pdf generator service by making a POST request to the catalog to register the service.

        :param None
        :return: None
        :raises Exception: If the registration process fails.
        """

        # Make a POST request to the catalog to send the pdf generator service data
        response = self.http_requests.POST(self.catalog_url, "register_service", self.service_data)
        
        if response.status_code != 200:
            raise Exception("Failed to register the pdf generator.")
        # If the post response is successfull the pdf generator has been registered
        print(response.text)
        
    def get_last_week_data(self,patient, sleep_diary_col, sleep_analytics_col):
        """
        Get the data for the last 7 days.
        :param patient: The patient for which the data is to be retrieved.
        :param sleep_diary_col: The sleep diary collection.
        :param sleep_analytics_col: The sleep analytics collection.
        :return: The sleep diary data and the sleep analytics data.
        """

        # Get the data for the last 7 days
        today = datetime.now()
        last_week = today - timedelta(days=7)

        sleep_diary_data = list(sleep_diary_col.find({"patient_id": patient["_id"], "date": {"$gte": last_week, "$lt": today}}))
        sleep_analytics_data = list(sleep_analytics_col.find({"patient_id": patient["_id"], "date": {"$gte": last_week, "$lt": today}}))

        return sleep_diary_data, sleep_analytics_data

    def extract_data(self, sleep_diary_data, sleep_analytics_data):
        """
        Extract the relevant information.
        :param sleep_diary_data: The sleep diary data.
        :param sleep_analytics_data: The sleep analytics data.
        :return: The processed data.
        """

        # Initialize the arrays for storing the data
        hours_of_sleep = []
        quality = []
        rested = []
        meal = []
        alcohol = []
        hr_values = []
        hr_std = []
        spo2_std = []
        snor_std = []
        snor_values = []
        spo2_values = []

        # Loop through the sleep diary data and extract the relevant information
        for document in sleep_diary_data:
            #hours_of_sleep.append(document["hours_of_sleep"])
            quality.append(document["quality"])
            rested.append(document["rested"])
            meal.append(document["meal"])
            alcohol.append(document["alcohol"])

        # Loop through the sleep analytics data and extract the relevant information
        for document in sleep_analytics_data:
            hr_values.append(document["hr_mean"])
            hr_std.append(document["hr_std"])
            snor_values.append(document["snoring_mean"])
            snor_std.append(document["snoring_std"])
            spo2_values.append(document["spo2_mean"])
            spo2_std.append(document["spo2_std"])

        return hours_of_sleep, quality, rested, meal, alcohol, hr_values,hr_std, snor_values, snor_std,  spo2_values,spo2_std, sleep_diary_data, sleep_analytics_data

    def create_hr_subplot(self, ax, hr_values, std_values, dates_sleep_analytics, font, font_dates):
        """
        Create the heart rate subplot.
        
        :param ax: The axis to plot on.
        :param hr_values: The heart rate values.
        :param dates_sleep_analytics: The dates for the sleep analytics data.
        :param font: The font to use.
        :param font_dates: The font to use for the dates.
        :return: None
        """

        # Plot the heart rate data
        ax.errorbar(dates_sleep_analytics, hr_values, yerr=std_values, linestyle='-', marker='o', color='red', capsize=5)
        ax.set_ylabel("Heart Rate, [bpm]", fontproperties=font)
        ax.set_ylim([min(hr_values) - 15, max(hr_values) + 15])
        ax.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
        ax.set_title("Heart Rate", fontsize=14, weight='bold')
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.tick_params(axis='x', rotation=45)
        self._annotate_values(ax, hr_values, dates_sleep_analytics)


    def create_spo2_subplot(self, ax, spo2_values,std_values, dates_sleep_analytics, font, font_dates):
        """
        Create the SpO2 subplot.

        param ax: The axis to plot on.
        :param spo2_values: The SpO2 values.
        :param dates_sleep_analytics: The dates for the sleep analytics data.
        :param font: The font to use.
        :param font_dates: The font to use for the dates.
        :return: None
        """

        ax.errorbar(dates_sleep_analytics, spo2_values, yerr=std_values, linestyle='-', marker='o', color='blue', capsize=5)
        ax.set_ylabel('SpO2, [%]', fontproperties=font)
        ax.set_ylim([min(spo2_values) - 3 , 100 ])
        ax.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
        ax.set_title("Sp02", fontsize=14, weight='bold')
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.tick_params(axis='x', rotation=45)
        self._annotate_values(ax, spo2_values, dates_sleep_analytics)

    def create_snoring_subplot(self, ax, snor_values,std_values, dates_sleep_analytics, font, font_dates):
        """
        Create the snoring subplot.

        :param ax: The axis to plot on.
        :param snor_values: The snoring values.
        :param dates_sleep_analytics: The dates for the sleep analytics data.
        :param font: The font to use.
        :param font_dates: The font to use for the dates.
        :return: None
        """
        ax.errorbar(dates_sleep_analytics, snor_values, yerr=std_values, linestyle='-', marker='o', color='purple', capsize=5)
        ax.set_ylabel('Snoring Intensity, [dB]', fontproperties=font)
        ax.set_ylim([min(snor_values) - 15, max(snor_values) + 15 ])
        ax.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
        ax.set_title("Snoring", fontsize=14, weight='bold')
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.tick_params(axis='x', rotation=45)
        self._annotate_values(ax, snor_values, dates_sleep_analytics)

    def _annotate_values(self, ax, values, dates):
        """
        Annotate the values on the given axis.

        :param ax: The axis to annotate.
        :param values: The values to annotate.
        :param dates: The dates for the sleep analytics data.
        :return: None
        """
        for i, value in enumerate(values):
            x_offset = 5
            y_offset = 5
            ax.annotate(f"{value}", (dates[i], value), textcoords="offset points", xytext=(x_offset, y_offset), ha='left', fontsize=8, color='black')

    def generate_pdf(self,chat_id, patient_id, sleep_analytics_data, sleep_diary_data):
        """
        Generate a PDF report for the patient.

        :param patient_id: The patient ID.
        :param sleep_analytics_data: The sleep analytics data.
        :param sleep_diary_data: The sleep diary data.
        :return: None
        """
        # Define the PDF file name and path as his name_date_report.pdf
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")
        action = "patient_info"
        patient = self.http_requests.GET(adaptor_data_url, action = action, params = {"id" :chat_id})
        patient_name = patient.json()["name"]
        patient_lastname = patient.json()["last_name"]
        current_date = datetime.now().strftime('%d-%m-%Y')
        self.pdf_file_name = f'{patient_name}_{patient_lastname}_{current_date}report.pdf'
        self.pdf_file_path = os.path.join(os.getcwd(), 'data', self.pdf_file_name)  # Construct the full path to the PDF file
        
        # Define the HTML content of the report
        html_content = """
        <html>
          <head>
            <style>
              table, th, td {{
                border: 1px solid black;
                border-collapse: collapse;
              }}
              th, td {{
                padding: 5px;
                text-align: left;
              }}
              .page-break {{
                page-break-after: always;
              }}
              img {{
                width: 700px;
                height:700px;
              }}
              /* Page numbering */
              @page {{
                counter-increment: page;
                @bottom-center {{
                  content: "Page " counter(page);
                }}
              }}
            </style>
          </head>
          <body>
            <div>
                <h1>Sleep Data Report</h1>
                <p>Patient ID: {}</p>
                <div class="center-image">
                  <img src="file:{}" />
                </div>
            <div class="page-break"></div>
            <div>
              <h3>Sleep Analytics Data</h3>
              <table>
                <tr>
                  <th>Date</th>
                  <th>Heart Rate Mean</th>
                  <th>Snoring Mean</th>
                  <th>SPO2 Mean</th>
                </tr>
                {}
              </table>
            </div>

            <div>
              <h3>Sleep Diary Data</h3>
              <table>
                <tr>
                  <th>Date</th>
                  <th>Quality</th>
                  <th>Rested</th>
                  <th>Meal</th>
                  <th>Alcohol</th>
                </tr>
                {}
              </table>
            </div>
          </body>
        </html>
        """.format(patient_id, self.figure_file_path,
            "".join([
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                    datetime.fromtimestamp(data["date"]).strftime("%m-%d"), data["hr_mean"], data["snoring_mean"], data["spo2_mean"] 
                ) for data in sleep_analytics_data
            ]),
            "".join([
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                    datetime.fromtimestamp(entry["date"]).strftime("%m-%d"), entry["quality"], entry["rested"], entry["meal"], entry["alcohol"]
                ) for entry in sleep_diary_data
            ])
        )


        # Generate the PDF file
        HTML(string=html_content).write_pdf(self.pdf_file_path)


    def get_report(self, chat_id):

        """
        Get the report for the patient.

        :param chat_id: The chat ID.
        :return: The report path
        """
        
        # Make a GET request to the catalog to retrieve the endpoint of the mongodb endpoints adaptor
        adaptor_data_url = self.http_requests.retrieve_url(endpoint_type="adaptor_data")

        # Retrieve the sleep diary and sleep analytics data for the last 7 days 
        response = self.http_requests.GET(adaptor_data_url, "get_last_week_data", {"chat_id": chat_id})

        if response.status_code == 200:
            data = response.json()
            sleep_diary_data = data["sleep_diary_data"]
            sleep_analytics_data = data["sleep_analytics_data"]
            patient_id = data["patient_id"]
        else:
            error_message = response.json()["error"]
            print(f"Error retrieving data: {error_message}")

        # Process the data and fill the arrays with the values 
        hours_of_sleep, quality, rested, meal, alcohol, hr_values,hr_std, snor_values,snor_std, spo2_values,spo2_std, sleep_diary_data, sleep_analytics_data = self.extract_data(sleep_diary_data, sleep_analytics_data)
        
        # Get the dates for the x-axis
        dates_sleep_analytics = []
        for document in sleep_analytics_data:
            date = datetime.fromtimestamp(document["date"]).strftime("%m-%d")
            dates_sleep_analytics.append(date)
        # Reverse the dates 
        dates_sleep_analytics.reverse()

        
        # Create the subplots 
        fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(12, 8))
        axs = axs.flatten()
        
        # Specify the font to use
        font = font_manager.FontProperties(fname='KaTeX_Main-Bold.ed829b5f.ttf', size=12)
        font_dates = font_manager.FontProperties(fname='KaTeX_Main-Bold.ed829b5f.ttf', size=8)

        # Create the subplots
        self.create_hr_subplot(axs[0], hr_values, hr_std, dates_sleep_analytics, font, font_dates)
        self.create_spo2_subplot(axs[1], spo2_values, spo2_std, dates_sleep_analytics,font, font_dates)
        self.create_snoring_subplot(axs[2], snor_values, snor_std, dates_sleep_analytics,font, font_dates)
        
        # Show the plot
        fig.tight_layout()
        self.figure_file_path = os.path.join(os.getcwd(), 'data', "figure.png")  # Construct the full path to the PDF file
        plt.savefig(self.figure_file_path)
        
        
        # Save the data into a PDF report
        self.generate_pdf(chat_id,patient_id, sleep_analytics_data, sleep_diary_data)
      
        return self.pdf_file_path

class report_generator_service:
    def __init__(self,config):
        """
        Initialize the service.
        
        :param config: The configuration file.
        """
        self.generator = report_generator(config)
        
    
    def get_config(self):
        """
        Get the configuration file.
        """
        self.generator.get_config()
        self.host = self.generator.host
        self.port = self.generator.port
    def register(self):
        """
        Register the service to the catalog.
        """

        self.generator.register()
    
    @cherrypy.expose
    def get_report(self, **params):
        """
        Get the report for the patient.

        :param chat_id: The chat ID.
        :return: The report path
        """

        chat_id = params["chat_id"]
        file_path = self.generator.get_report(chat_id)
        response = {"report_file_path": file_path}
        return json.dumps(response)

if __name__ == '__main__':

    with open("shared/config.json", "r") as f:
        config = json.load(f)
    time.sleep(30)
    report_generator_service = report_generator_service(config)
    report_generator_service.get_config()
    report_generator_service.register()
    
    cherrypy.config.update({'server.socket_host': report_generator_service.host})
    cherrypy.config.update({'server.socket_port': report_generator_service.port})
    
    cherrypy.quickstart(report_generator_service)
    
    prev_host = report_generator_service.host
    prev_port = report_generator_service.port

    while True:
        time.sleep(30)
        report_generator_service.get_config()
        report_generator_service.register()
        if report_generator_service.host != prev_host or report_generator_service.port != prev_port:
            cherrypy.server.socket_host = report_generator_service.host
            cherrypy.server.socket_port = report_generator_service.port
            cherrypy.tree.mount(report_generator_service, '/')
            cherrypy.engine.start()

            prev_host = report_generator_service.host
            prev_port = report_generator_service.port
            print("Report generator service updated: restarted CherryPy server with new host and port!")
        else:
            print("Report generator service updated: host and port did not change")
        
    


"""
To generate a report for a specific chat ID, 
send an HTTP GET request to http://localhost:8080/get_report with the chat_id parameter:
http://localhost:8080/get_report?chat_id=1234
The service will return the file path to the generated PDF report, 
which you can then download or view. 
"""