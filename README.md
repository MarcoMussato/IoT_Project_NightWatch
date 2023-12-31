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
   
   - **Check if Docker is Installed**:
     Open a terminal or command prompt and run the following command:
     ```bash
     docker --version
     ```

     If Docker is installed, this will return its version. If not, you'll typically see a message like "command not found" or similar.

   - If Docker isn't installed or isn't accessible from the command line, download and install it from the [Docker official site](https://www.docker.com/).

   - **(Optional) Check Docker Compose**:
     While you're at it, it might be useful to also ensure `docker-compose` is installed. You can verify this with:
     ```bash
     docker-compose --version
     ```

2. **Download the Repository**: 
   - Clone or download the NightWatch repository and save it in a directory on your computer.

3. **Configure Dashboard Adaptor**:
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

5. **Setup and Start Docker Containers**:

   - Launch the Docker application.

   - Open a terminal or command prompt in the main directory of NightWatch (where the `docker-compose.yml` file resides).

   - First, build all the Docker images using the following command:

     ```bash
     docker-compose build
     ```

   - After building, start all the containers (excluding the ones for sensor simulation and node-red) using:

     ```bash
     docker-compose up --detach --scale sensor-simulation=0 --scale node-red=0
     ```

     If you want to see the logs in the terminal, remove the `--detach` flag:

     ```bash
     docker-compose up --scale sensor-simulation=0 --scale node-red=0
     ```

     The `--detach` flag runs the containers in the background. If you prefer to view the logs directly in the terminal, simply omit this flag. This will initialize and run all the necessary services.


6. **Access Telegram Bots**:
   - Open Telegram and search for the two bots:
     - [NightWatch Doctors](https://t.me/SleepApnea_bot)
     - [NightWatch Patients](https://t.me/SleepApnea_pat_bot)
## License

This project is licensed under the GNU General Public License (GPL). See the [LICENSE](LICENSE.txt) file for details.

