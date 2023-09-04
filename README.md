# NightWatch

NightWatch is a platform that offers an integrated solution for monitoring sleep apnea patients, keeping both doctors and patients at the forefront. The platform aims to enhance sleep care by leveraging modern technology, offering timely interventions, and ensuring a seamless user experience.

## Features

- **Telegram Bots**: User-friendly bots for doctors and patients, streamlining registration, data access, and communication.
  
- **Node-RED Dashboard**: Provides doctors with a visual interface, granting in-depth insights into patient sleep patterns.
  
- **Docker Compose Deployment**: Guarantees consistent application behavior across various environments, from local setups to production servers.
  
- **Service Monitoring**: An automated catalog that continuously tracks the health of services, updating active ones and retiring unresponsive ones.
  
- **Automated Alerts**: A dedicated system that reviews patient data nightly, dispatching critical apnea episode alerts directly to the respective doctor's chat.
  
- **Data Management**: Comprehensive data analysis backed by MongoDB, efficiently storing patient details, sleep data, and analytics.

## Installation & Usage

Follow these steps to set up and run the NightWatch platform:

1. **Install Docker**: 
   - Ensure that Docker is installed on your computer. If not, download and install it from the [Docker official site](https://www.docker.com/).

2. **Download the Repository**: 
   - Clone or download the NightWatch repository and save it in a directory on your computer.

3. **Configure Node-RED Adaptor**:
   - Navigate to the folder `dashboard-manager`.
   - Open the file `nodered_adaptor.py`.
   - Go to line 83 and modify it as follows:

     ```python
     cmd = ["docker", "run", "--name", f"{container_name}", "-p", "1880", "--network", "<main_folder_name>_my_network", "<main_folder_name>-node-red"]
     ```

     Replace `<main_folder_name>` with the name of the main directory where you saved the repository.

4. **Configure Sensor Adaptor**:
   - Navigate to the folder `sensor-manager`.
   - Open the file `sensor_adaptor.py`.
   - Go to line 99 and modify it as follows:

     ```python
     docker_command = ["docker", "run", "--name", container_name, "--network", "<main_folder_name>_my_network", "<main_folder_name>-sensor-simulation"]
     ```

     Again, replace `<main_folder_name>` with the name of the main directory where you saved the repository.

5. **Run Docker Compose**:
   - Open the Docker application.
   - Open a terminal or command prompt in the main directory of NightWatch (where the `docker-compose.yml` file resides).
   - Run the following command to start the Docker containers:

     ```bash
     docker-compose up
     ```

     This will initialize and run all the services.

6. **Access Telegram Bots**:
   - Open Telegram and search for the two bots:
     - NightWatch Doctors
     - NightWatch Patients

## License

This project is licensed under the GNU General Public License (GPL). See the [LICENSE](LICENSE.txt) file for details.

