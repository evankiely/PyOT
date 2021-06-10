# Written by Evan Kiely
# For more information, please see here: https://github.com/evankiely/PyOT/tree/master/PassiveThermostat
# Licensed under the GNU General Public License v3.0

# Importing dependencies
import os
import re
import time
import math
import email
import random
import smtplib
import imaplib
import Adafruit_DHT
import pandas as pd
from threading import Timer
from email.message import EmailMessage

# Defining Sensor class that will be used to hold values specific to a given sensor and location
class Sensor:

    # Defining initialization requirements and their corresponding methods
    def __init__(self, sensorLocation, sensor, pin):
        self.statusNominal = True
        self.location = sensorLocation
        self.sensor = sensor
        self.increment = 0
        self.pin = pin

    # This function is used to reset the status of the instance to queriable if it/its associated sensor had previously been identified as malfunctioning
    def reset(self):
        self.increment = 0
        self.statusNominal = True

    # Main function of the sensor class - does what it sounds like, returns relevant values, and notifies if a given sensor appears to have failed
    def getTemp(self, useHI=True, wantRH=False, wantAll=False):

        # Pulls temperature and humidity values from the sensor
        humidity, temperature = Adafruit_DHT.read(self.sensor, self.pin)

        # Filtering for absence of sensor data
        if humidity is not None and temperature is not None:

            # converting c to f
            temperature = round((temperature * 1.8) + 32)
            humidity = round(humidity)

            if wantAll:
                tempHI = self.getHI(humidity, temperature)
                return (temperature, tempHI, humidity)

            else:

                # HI = Heat Index aka Apparent Temperature
                if useHI:

                    if wantRH:
                        return (self.getHI(humidity, temperature), humidity)

                    return self.getHI(humidity, temperature)

                if wantRH:
                    return (temperature, humidity)

                return temperature
        
        return self.incrementState(useHI, wantRH, wantAll)
        # If there does seem to be an issue with the sensor data, we need to try again

    def incrementState(self, useHI, wantRH, wantAll):

        if self.increment < 30:

            self.increment += 1
            # giving the sensor time in case it's an issue of ping frequency overwhelming it
            time.sleep(2)
            return self.getTemp(useHI=useHI, wantRH=wantRH, wantAll=wantAll)

        # But there should be a limit to the number of times we try in case the sensor is just broken
        else:

            if self.statusNominal:
                # So, we turn off the ability of the list comprehension to call this sensor
                self.statusNominal = False
                # 14400 for four hours, 86400 for 24 -- Prevents multiple messages about the same issue in a short period of time
                antiSpam = Timer(900, self.reset)
                # And then start a timer to reset this, so that it doesn't require a reboot when the sensor is replaced, but also doesn't send notifications repeatedly in the mean time
                antiSpam.start()
                currentTime = time.strftime("%I:%M %p %b %d", time.localtime())
                status = "Potential Sensor Failure"
                infiniteCall = f"The sensor monitoring the {self.location} appears to be broken as of {currentTime}"
                # Note that malfunction is True here, so the malfunction contact(s) will be messaged directly
                sendEmail(status, infiniteCall, True)
                
            if wantAll:
                return (999, 999, 999)
            elif wantRH:
                return (999, 999)
            else:
                return 999

    # calculations per: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    def getHI(self, humidityVal, tempVal):
        HI = 0.5 * (tempVal + 61.0 + ((tempVal - 68.0) * 1.2) + (humidityVal * 0.094))

        if HI < 80:
            return round(HI)

        else:
            HI = -42.379 + (2.04901523 * tempVal) + (10.14333127 * humidityVal) - (0.22475541 * tempVal * humidityVal) - (0.00683783 * tempVal**2) - (0.05481717 * humidityVal**2) + (0.00122874 * tempVal**2 * humidityVal) + (0.00085282 * tempVal * humidityVal**2) - (0.00000199 * tempVal**2 * humidityVal**2)

        if humidityVal > 85 and tempVal in range(80, 85):
            HI += ((humidityVal - 85) / 10) * ((87 - tempVal) / 5) # added to HI before returning

        elif humidityVal < 13 and tempVal in range(80, 112):
            HI -= ((13 - humidityVal) / 4) * math.sqrt((17 - abs(tempVal - 95)) / 17)
        
        return round(HI)

class Thermostat:

    def __init__(self, targetTemp, internal: Sensor, external: Sensor, contactsDF: pd.DataFrame):
        self.targetTemp = targetTemp
        self.contactsDF = contactsDF
        self.internal = internal
        self.external = external

        self.interval = 30
        self.isOpen = False
        self.outputDir = "./downloads"
        self.logDir = "dataLog.csv"
        self.recognizedCommands = [
            
            "set target", "set interval",
            "get current", "get commands",
            "get interval", "get feels like",
            "add recipient", "add malfunction",
            "drop recipient", "drop malfunction"

        ]

        self.buildEnv()

    def buildEnv(self):

        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)

        if not os.path.exists(self.logDir):
            columns = [

                "Year", "Month", "Day",
                "Hour", "Minute",
                "InternalTemp", "InternalHI", "InternalRH",
                "ExternalTemp", "ExternalHI", "ExternalRH"
                
                ]
            self.dataLog = pd.DataFrame(columns=columns)
            self.dataLog.to_csv(self.logDir, index=False)

        else:
            self.dataLog = pd.read_csv(self.logDir, dtype=str)

    def getInput(self):

        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(gmailEmail, gmailPass)
        status, messages = mail.select("INBOX")
        (retcode, emailnums) = mail.search(None,'(UNSEEN)') # "(BODY.PEEK[])" to avoid marking read?
        emailnums = emailnums[0].split()

        if retcode == 'OK' and len(emailnums) > 0:

            for emailnum in emailnums:

                typ, data = mail.fetch(emailnum,'(RFC822)')
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                fromAddress = email_message["From"].split("@")[0]

                if fromAddress not in authedInputs:
                    continue

                if email_message.get_content_maintype() != 'multipart':
                    continue

                for part in email_message.walk():

                    if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                        
                        # could use %f with datetime to get milliseconds and avoid potentially reusing same "random" number by accident, and maintain file ordering -> see: https://stackoverflow.com/questions/6677332/using-f-with-strftime-in-python-to-get-microseconds
                        open(f"{self.outputDir}/{random.randint(0, 10000)}_{part.get_filename()}", 'wb').write(part.get_payload(decode=True))
                
            if len(os.listdir(self.outputDir)) > 0:
                
                commands = [item for item in os.listdir(self.outputDir) if item.endswith(".txt")]
                subject = "Confirmation"
                error = "Error"

                for item in commands:

                    path = f"{self.outputDir}/{item}"

                    with open(path, "r") as f:

                        f = f.read()

                        if "\n" in f:
                            commands = set(f.split("\n"))

                        elif ", " in f:
                            commands = set(f.split(", "))

                        else:
                            commands = [f]

                        commands = {
                            (item.split(": ")[0].lower() if ": " in item else item.lower()): (item.split(": ")[1] if ": " in item and len(item.split(": ")) == 2 else None)
                            for item in commands
                        }

                    for command, val in zip(commands.keys(), commands.values()):

                        if "set" in command and val is None:
                            message = f"Set commands require an integer assignment value, such as '{command}: 68'"
                            sendEmail(error, message)
                            continue

                        elif ("add" in command or "drop" in command) and val is None:
                            message = f"Add/Drop commands require contact information, such as '{command}: contact'"
                            sendEmail(error, message)
                            continue

                        elif val is not None and "add" not in command and "drop" not in command:

                            try:
                                val = int(val)

                            except:
                                message = f"Input ({command}: {val}) could not be coerced to integer"
                                sendEmail(error, message)
                                continue

                        # 45 - 90 is an arbitrary choice, but figured it would cover most normal home temperatures
                        if command == "set target" and val in range(45, 90):
                            self.targetTemp = val
                            message = f"Target Temperature set to {self.targetTemp}f as of {currentTime}"
                            sendEmail(subject, message)

                        # 1 - 3600 is an arbitrary choice; between once/second and once/hour
                        elif command == "set interval" and val in range(1, 3600):
                            self.interval = val
                            message = f"Interval set to {self.interval}s as of {currentTime}"
                            sendEmail(subject, message)

                        elif command == "get current":
                            tempInternal, rhInternal = self.internal.getTemp(useHI=False, wantRH=True) 
                            tempExternal, rhExternal = self.external.getTemp(useHI=False, wantRH=True)
                            message = f"As of {currentTime}, temperature and RH outside: {tempExternal}f, {rhExternal}%, and inside: {tempInternal}f, {rhInternal}% with target temperature of {self.targetTemp}f"
                            sendEmail(subject, message)
                            time.sleep(0.5)

                        elif command == "get commands":
                            message = f"{', '.join(self.recognizedCommands)}"
                            sendEmail("Commands", message)

                        elif command == "get interval":
                            message = f"Interval is {self.interval}s as of {currentTime}"
                            sendEmail(subject, message)

                        elif command == "get feels like":
                            internalVals = self.internal.getTemp(wantRH=True) 
                            externalVals = self.external.getTemp(wantRH=True)
                            tempInternal, rhInternal = internalVals
                            tempExternal, rhExternal = externalVals
                            message = f"As of {currentTime}, apparent temperature and RH outside: {tempExternal}f, {rhExternal}%, and inside: {tempInternal}f, {rhInternal}% with target temperature of {self.targetTemp}f"
                            sendEmail(subject, message)
                            time.sleep(0.5)
                            
                        elif "add" in command or "drop" in command:

                            # use this to match more general email addresses (^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$) 
                            # below will match only email addresses which conform to the 10 digit phone number + service provider extension (technically any extension)
                            match = re.fullmatch(r"(^[0-9]{10}@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", val)

                            if match is None:
                                message = f"Input value ({val}) must be a valid email address"
                                sendEmail(subject, message)
                                continue

                            if "add" in command:
                                toggle = 1.0

                            elif "drop" in command:
                                toggle = None

                            contactFilt = self.contactsDF["Contact"] == val
                            rFilt = (self.contactsDF["Recipient"] != toggle) & contactFilt
                            mFilt = (self.contactsDF["Malfunction"] != toggle) & contactFilt

                            if "recipient" in command and not self.contactsDF.loc[rFilt].empty:
                                self.contactsDF.loc[contactFilt, "Recipient"] = toggle
                                self.contactsDF.dropna(how="all", subset=["Recipient", "Malfunction"], inplace=True)
                                self.contactsDF.to_csv(contactPath, index=False)
                                message = f"Command ({command}) completed successfully as of {currentTime}"
                                sendEmail(subject, message)

                            elif "malfunction" in command and not self.contactsDF.loc[mFilt].empty:
                                self.contactsDF.loc[contactFilt, "Malfunction"] = toggle
                                self.contactsDF.dropna(how="all", subset=["Recipient", "Malfunction"], inplace=True)
                                self.contactsDF.to_csv(contactPath, index=False)
                                message = f"Command ({command}) completed successfully as of {currentTime}"
                                sendEmail(subject, message)

                            elif toggle:

                                if "recipient" in command:
                                    self.contactsDF = self.contactsDF.append({"Contact": val, "Recipient": 1}, ignore_index=True, sort=False)
                                    self.contactsDF.to_csv(contactPath, index=False)
                                    message = f"Command ({command}) completed successfully as of {currentTime}"
                                    sendEmail(subject, message)

                                elif "malfunction" in command:
                                    self.contactsDF = self.contactsDF.append({"Contact": val, "Malfunction": 1}, ignore_index=True)
                                    self.contactsDF.to_csv(contactPath, index=False)
                                    message = f"Command ({command}) completed successfully as of {currentTime}"
                                    sendEmail(subject, message)

                        else:
                            message = f"Hm, something seems to have gone wrong. Please check your command ({command}) and value ({val}) for errors"
                            sendEmail(error, message)

                    os.remove(path)
                    
            self.removeMail(mail)

    def removeMail(self, mail):

        mail.store("1:*", '+X-GM-LABELS', '\\Trash')

        folders = ['"[Gmail]/Sent Mail"', '"[Gmail]/All Mail"']
        for folder in folders:
            status, messages = mail.select(folder)
            mail.store("1:*", '+X-GM-LABELS', '\\Trash')

        status, messages = mail.select('"[Gmail]/Trash"')
        mail.store("1:*", "+FLAGS", "\\Deleted")
        mail.expunge()

    def checkTemp(self, currentTime):

        tempInternal = self.internal.getTemp() 
        tempExternal = self.external.getTemp()

        if tempInternal is not None and tempExternal is not None:

            if not self.isOpen:

                openStatus = "Time to Open Windows!"
                openNotification = f"As of {currentTime}, temperature outside is {tempExternal}f and temperature inside is {tempInternal}f, with target temperature of {self.targetTemp}f"

                if tempExternal > self.targetTemp and tempInternal < self.targetTemp:

                    sendEmail(openStatus, openNotification)
                    self.isOpen = True

                elif tempExternal < self.targetTemp and tempInternal > self.targetTemp:

                    sendEmail(openStatus, openNotification)
                    self.isOpen = True

                # maybe the below two conditions send: "consider using ac/heat"?
                # if outside more than target, and inside more than outside, outside is cooler, so opening works to approach target
                elif tempExternal > self.targetTemp and tempInternal > tempExternal:

                    sendEmail(openStatus, openNotification)
                    self.isOpen = True

                # if outside less than target, and inside less than outside, outside is warmer, so opening works to approach target
                elif tempExternal < self.targetTemp and tempInternal < tempExternal:

                    sendEmail(openStatus, openNotification)
                    self.isOpen = True

            else:

                closeStatus = "Time to Close Windows!"
                closeNotification = f"As of {currentTime}, temperature outside is {tempExternal}f and temperature inside is {tempInternal}f, with target temperature of {self.targetTemp}f"

                if tempInternal > self.targetTemp and tempInternal < tempExternal:

                    sendEmail(closeStatus, closeNotification)
                    self.isOpen = False

                elif tempInternal < self.targetTemp and tempInternal > tempExternal:

                    sendEmail(closeStatus, closeNotification)
                    self.isOpen = False

    def logData(self, logTime):

        internalTemp, internalHI, internalRH = self.internal.getTemp(wantAll=True)
        externalTemp, externalHI, externalRH = self.external.getTemp(wantAll=True)
        splitLog = logTime.split(" ")
        splitLog[0] = splitLog[0].split(":")

        data = {

            "Year": splitLog[3],
            "Month": splitLog[1],
            "Day": splitLog[2],
            "Hour": splitLog[0][0],
            "Minute": splitLog[0][1],
            "InternalTemp": internalTemp,
            "InternalHI": internalHI,
            "InternalRH": internalRH,
            "ExternalTemp": externalTemp,
            "ExternalHI": externalHI,
            "ExternalRH": externalRH

        }

        self.dataLog = self.dataLog.append(data, ignore_index=True)
        self.dataLog.to_csv(self.logDir, index=False)

# Setting up to send emails later
# Using environmental variables to store username and password of associated Gmail account
gmailEmail = os.environ.get("gmailUser")
gmailPass = os.environ.get("gmailToken")

# For (email -> text), [phone number] + ("@vtext.com", "@txt.att.net", "@msg.fi.google.com", "@messaging.sprintpcs.com", "@tmomail.net", "@sms.cricketwireless.net")
contactPath = "./contacts.csv"
contactsDF = pd.read_csv(contactPath)
recipientEmail = contactsDF.loc[contactsDF["Recipient"] == 1.0, "Contact"].astype(list)
malfunctionContact = contactsDF.loc[contactsDF["Malfunction"] == 1.0, "Contact"].astype(list)

# taking the below approach because the script looks for attachments, which generally come back from a different URL (think @mms.att.net)
authedInputs = [email.split("@")[0] for email in recipientEmail]

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
            msg["To"] = malfunctionContact
            smtp.send_message(msg)

# Creating variable to contain sensor type
dht11 = Adafruit_DHT.DHT11
thermo = Thermostat(68, Sensor("Internal Temperature", dht11, 4), Sensor("External Temperature", dht11, 17), contactsDF)

# Creating a variable to track the start/boot status of the system and notify on initial invocation
globalBoolean = True
logTimes = ["00", "15", "30", "45"]
logged = False
wantHeartbeat = True

while True:

    currentTime = time.strftime("%I:%M %p %b %d", time.localtime())
    minute = currentTime.split(" ")[0].split(":")[1]

    # Checks if this is the first time the script is running -- if so, it's important to notify that it has just started so the user knows it is working and/or in case of unexpected reboot, etc.
    if globalBoolean is True:
        # Creating variable to contain the current time
        status = "System Start"
        helloWorld = f"Initial boot at {currentTime}"
        sendEmail(status, helloWorld)
        # Turns off the welcome message after the first loop
        globalBoolean = False

    # checking for updates from user
    thermo.getInput()
    # Set this to the interval for sensor checking -- how often to ping
    time.sleep(thermo.interval) # set to 900 for 15 min
    thermo.checkTemp(currentTime)

    doLog = minute in logTimes
    
    if doLog and not logged:
        thermo.logData(time.strftime("%H:%M %m %d %Y", time.localtime()))
        logged = True
    
    #below does not permit use of adjacent numbers
    elif not doLog and logged:
        logged = False
    
    if wantHeartbeat and minute == "00":
        wantHeartbeat = False
        sendEmail("Heartbeat", f"Still alive as of {currentTime}")

    elif not wantHeartbeat and minute != "00":
        wantHeartbeat = True

    # Set this to the interval for sensor checking -- how often to ping
    # time.sleep(thermo.interval) # set to 900 for 15 min
