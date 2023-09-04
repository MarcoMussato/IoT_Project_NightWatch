
import random
import math


class sensor_generator():
    def __init__(self):
        pass

    def generate_hr_data(self):
        """
        Generate a random heart rate value using Gaussian distribution.
        
        :param heart_rate_mean: The mean heart rate value to generate.
        :param heart_rate_std: The standard deviation of the heart rate value to generate.
        :return: A heart rate value generated using Gaussian distribution.
        """
        heart_rate_mean = 70  # Mean heart rate
        heart_rate_std = 10  # Standard deviation of heart rate
        return round(random.gauss(heart_rate_mean, heart_rate_std),0)
    def generate_snoring_data(self):
        """
        Generate a random snoring value using Gaussian distribution.
        
        :param heart_rate_mean: The mean snoring value to generate.
        :param heart_rate_std: The standard deviation of the snoring value to generate.
        :return: A snoring value generated using Gaussian distribution.
        """
        snoring_mean = 45  # Mean snoring level
        snoring_std = 10  # Standard deviation of snoring level
        return round(random.gauss(snoring_mean, snoring_std),1)

    def generate_spo2_data(self):
        """
        Generate a random SpO2 value using Gaussian distribution.
        
        :param heart_rate_mean: The mean SpO2 value to generate.
        :param heart_rate_std: The standard deviation of the SpO2 value to generate.
        :return: A SpO2 value generated using Gaussian distribution.
        """
        spo2_amplitude = 2  # Amplitude of the sinusoidal signal
        spo2_frequency = 0.1  # Frequency of the sinusoidal signal
        spo2_mean = 98  # Mean SpO2 value
        spo2_std = 0.5  # Standard deviation of added noise
        spo2_data = spo2_mean + spo2_amplitude * math.sin(2 * math.pi * spo2_frequency) + random.gauss(0, spo2_std)
        return round(spo2_data,1)