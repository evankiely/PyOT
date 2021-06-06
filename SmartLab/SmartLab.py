# Written by Evan Kiely for the Gilbert-Ross Lab, Emory University, January 2020
# For more information, please see here: https://github.com/evanjkiely/SmartLab
# Licensed under the GNU General Public License v3.0

# Importing dependencies
import os
import time
import smtplib
import Adafruit_DHT
from threading import Timer
from email.message import EmailMessage


# Defining Equipment class that will be used to hold values specific to a given piece of equipment
class Equipment:

    # Defining initialization requirements and their corresponding methods
    def __init__(self, equipmentType, sensor, pin, lowerBound, upperBound):
        self.statusNominal = True
        self.type = equipmentType
        self.lower = lowerBound
        self.upper = upperBound
        self.sensor = sensor
        self.increment = 0
        self.pin = pin

    # This function is used to reset the status of the instance to queriable if it/its associated sensor had previously been identified as malfunctioning
    def reset(self):
        self.increment = 0
        self.statusNominal = True

    # Main function of the equipment class - does what it sounds like, returns relevant values, and notifies if a given sensor appears to have failed
    def getTemp(self):
        # No need to check temp, etc. if a malfunction was previously identified
        if self.statusNominal is False:
            return
        # Pulls temperature and humidity values from the sensor
        humidity, temperature = Adafruit_DHT.read(self.sensor, self.pin)
        # 14400 for four hours -- Prevents multiple messages about the same issue in a short period of time
        antiSpam = Timer(30, self.reset)

        # Filtering for absence of sensor data
        if humidity is not None and temperature is not None:
            temperature = int(round(temperature))

            # No need to continue if everything is normal
            if temperature in range(self.lower, self.upper):
                return

            # However, we ought to take note of anything that is malfunctioning
            else:
                # Effectively turns off this piece of equipment from future checks
                self.statusNominal = False
                # Runs timer to prevent malfunctioning equipment/sensor from being checked, and resets it to checkable after the timer has expired
                antiSpam.start()
                return f"{self.type}: {temperature} C"

        # If there does seem to be an issue with the sensor data, we need to try again
        elif self.increment < 25:
            self.increment += 1
            return self.getTemp()

        # But there should be a limit to the number of times we try in case the sensor is just broken
        elif self.increment == 25:
            # So, we turn off the ability of the list comprehension to call this piece of equipment
            self.statusNominal = False
            # And then start a timer to reset this, so that it doesn't require a reboot when the sensor is replaced, but also doesn't send notifications repeatedly in the mean time
            antiSpam.start()
            status = "Potential Sensor Failure"
            infiniteCall = f"The sensor monitoring your {self.type} appears to be broken."
            # Note that emergency is True here, so the emergency contact(s) will be messaged directly
            sendEmail(status, infiniteCall, True)

# Creating variable to contain sensor type
dht11 = Adafruit_DHT.DHT11

# Initializing instances of Equipment class
incubator25 = Equipment("25C_Inc", dht11, 4, 22, 27)
incubator18 = Equipment("18C_Inc", dht11, 4, 16, 22)
minus20 = Equipment("-20", dht11, 4, -30, -15)
minus80 = Equipment("-80", dht11, 4, -90, -70)

# Placing our instances in a list
equipmentList = [incubator25, incubator18, minus20, minus80]
# Creating a variable to track the start/boot status of the system and notify on initial invocation
globalBoolean = True

# Setting up to send emails later
# Using environmental variables to store username and password of associated Gmail account
gmailEmail = os.environ.get("gmailUser")
gmailPass = os.environ.get("gmailToken")
# For (email -> text), [phone number] + ("@vtext.com", "@txt.att.net", "@msg.fi.google.com", "@messaging.sprintpcs.com", "@tmomail.net", "@sms.cricketwireless.net")
recipientEmail = ["8005882300@msg.fi.google.com"]
malfunctionContact = ["8005882300@msg.fi.google.com"]

# Defining the function that composes and sends emails
def sendEmail(subject, message, malfunction=False):

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmailEmail
    msg.set_content(message)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        smtp.login(gmailEmail, gmailPass)

        if malfunction is False:
            msg["To"] = recipientEmail
            smtp.send_message(msg)

        else:
            # Certain issues may require notifying the individual responsible for maintaining the equipment/sensor network itself rather than the experiments in the equipment, etc.
            msg["To"] = malfunctionContact
            smtp.send_message(msg)

while True:

    currentTime = time.strftime("%I:%M %p %b %d", time.localtime())

    # Checks if this is the first time the script is running -- if so, it's important to notify that it has just started so the user knows it is working and/or in case of unexpected reboot, etc.
    if globalBoolean is True:
        status = "System Start"
        helloWorld = f"Initial boot at {currentTime}"

        sendEmail(status, helloWorld)
        # Turns off the welcome message after the first loop
        globalBoolean = False

    # List comprehension that queries the current temperature of our equipment, but only if they/their associated sensor are not already known to be malfunctioning
    malfunctioning = [equipment.getTemp() for equipment in equipmentList]
    # Filters for None types returned when equipment is in the normal range
    malfunctioning = [equipment for equipment in malfunctioning if equipment is not None]

    # Easy way of determining if anything has been reported as out of range, otherwise, there's no need to do anything but wait until the next time we need to retrieve data
    if len(malfunctioning) > 0:
        # Creating the final message contents
        status = "Potential Equipment Failure"
        malfunctioning = f"As of {currentTime}: {', '.join(malfunctioning)}"

        # calling email function
        sendEmail(status, malfunctioning)

        # Deletes the malfunctioning list, if it is known to have contents, so as to ensure there is no potential for carry over between iterations
        del malfunctioning

    # Set this to the interval for sensor checking -- how often to ping
    time.sleep(10)
