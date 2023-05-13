# Written by Evan Kiely
# For more information, please see here: https://github.com/evankiely/PyOT/tree/master/PassiveThermostat
# Licensed under the GNU General Public License v3.0

# Importing dependencies
import os
import re
import time
import math
import email
import shutil
import random
import smtplib
import imaplib
import Adafruit_DHT
import pandas as pd
from email.message import EmailMessage

# Defining Sensor class that will be used to hold values specific to a given sensor and location
class Sensor:

    # Defining initialization requirements and their corresponding methods
    def __init__(self, sensorLocation, sensor, pin):
        self.location = sensorLocation
        self.sensor = sensor
        self.increment = 0
        self.pin = pin

    # Main function of the sensor class - does what it sounds like, returns relevant values, and notifies if a given sensor appears to have failed
    def getTemp(self, useHI=True, wantRH=False, wantAll=False, useF=True):

        # Pulls temperature and (relative) humidity values from the sensor
        humidity, temperature = Adafruit_DHT.read(self.sensor, self.pin)

        # Filtering for absence of sensor data
        if humidity is not None and temperature is not None:

            if useF:
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
            time.sleep(1)
            return self.getTemp(useHI=useHI, wantRH=wantRH, wantAll=wantAll)

        # But there should be a limit to the number of times we try in case the sensor is just broken
        else:
                
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

    # calculations per: https://web.archive.org/web/20200212215746im_/https://www.vaisala.com/en/system/files?file=documents/Humidity_Conversion_Formulas_B210973EN.pdf
    # which was referenced here: https://earthscience.stackexchange.com/questions/16570/how-to-calculate-relative-humidity-from-temperature-dew-point-and-pressure
    def getDewPoint(self, useF=True):
        temp, RH = 999, 999

        while temp == 999 or RH == 999:
            temp, RH = self.getTemp(useHI=False, wantRH=True, useF=False)

        # first calculate water vapour saturation pressure over water/ice in hPa
        if temp in range(-70, 0):
            A, m, Tn = 6.114742, 9.778707, 273.1466

        elif temp in range(0, 51):
            A, m, Tn = 6.116441, 7.591386, 240.7263

        Pws = A * 10**((m * temp)/ (temp + Tn))

        # next derive the water vapour pressure
        Pw = (Pws * RH)/100
        # finally, calculate the dew point
        Td = Tn/((m/math.log10(Pw/A))-1)

        if useF:
            # converting c to f
            Td = (Td * 1.8) + 32

        return round(Td)

class Thermostat:

    def __init__(self, targetTemp, internal: Sensor, external: Sensor):
        self.targetTemp = targetTemp
        self.internal = internal
        self.external = external

        # Set this to the interval for sensor checking -- how often to ping
        self.interval = 30
        self.isOpen = False
        # Setting up to send emails later
        # Using environmental variables to store username and password of associated Gmail account
        self.gmailEmail = os.environ.get("gmailUser")
        self.gmailPass = os.environ.get("gmailToken")
        self.outputDir = "downloads"
        self.logDir = "logs"
        self.logFile = "dataLog.csv"
        self.contactsFile = "contacts.csv"
        self.recognizedCommands = [
            
            "set target", "set interval",
            "get target", "get current",
            "get commands", "get interval",
            "get feels like", "get dew point",
            "add recipient", "drop recipient"

        ]

        self.logTimes = ["00", "15", "30", "45"]
        self.logged = False
        self.wantHeartbeat = True
        self.kill = False
        self.killConfirm = False

        self.buildEnv()
        self.currentTime = time.strftime("%I:%M %p %b %d", time.localtime())
        self.helloWorld()
        self.main()

    def buildEnv(self):

        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)

        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)

        if not os.path.exists(self.logFile):
            columns = [

                "Year", "Month", "Day",
                "Hour", "Minute",
                "InternalTemp", "InternalHI", "InternalRH",
                "ExternalTemp", "ExternalHI", "ExternalRH"
                
                ]
            self.dataLog = pd.DataFrame(columns=columns)
            self.dataLog.to_csv(self.logFile, index=False)

        else:
            self.dataLog = pd.read_csv(self.logFile, dtype=str)

        if not os.path.exists(self.contactsFile):
            columns =["Contact", "Recipient"]
            self.contactsDF = pd.DataFrame(columns=columns)
            self.contactsDF.to_csv(self.contactsFile, index=False)

        else:
            self.contactsDF = pd.read_csv(self.contactsFile)
            self.recipientEmail = self.contactsDF.loc[self.contactsDF["Recipient"] == 1.0, "Contact"].astype(list)
            self.authedInputs = [email.split("@")[0] for email in self.recipientEmail]

    def helloWorld(self):
        status = "System Start"
        helloWorld = f"Initial boot at {self.currentTime}"
        self.sendEmail(status, helloWorld)

    def main(self):
        
        while True:

            self.currentTime = time.strftime("%I:%M %p %b %d", time.localtime())
            minute = self.currentTime.split(" ")[0].split(":")[1]

            # logging first, since it is often skipped, but having it after the others means it sometimes logs a minute later than it should, depending on number and type of commands
            doLog = minute in self.logTimes
            
            if doLog and not self.logged:
                # logged set true in below if successful
                self.logData()
            
            #below does not permit use of adjacent numbers
            elif not doLog and self.logged:
                self.logged = False

            if not doLog:
                
                # checking for updates from user
                self.getInput()
                # checking temperatures
                self.checkTemp()

            # finally, heartbeat is important, but is not high priority
            if self.wantHeartbeat and minute == "00":
                self.wantHeartbeat = False
                self.sendEmail("Heartbeat", f"Still alive as of {self.currentTime}")

            elif not self.wantHeartbeat and minute != "00":
                self.wantHeartbeat = True

            time.sleep(self.interval)

            if self.killConfirm:
                break

    # Defining the function that composes and sends emails
    def sendEmail(self, subject, message):

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.gmailEmail
        msg.set_content(message)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

            smtp.login(self.gmailEmail, self.gmailPass)
            msg["To"] = self.recipientEmail
            smtp.send_message(msg)

    def getInput(self):

        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(self.gmailEmail, self.gmailPass)
        status, messages = mail.select("INBOX")
        (retcode, emailnums) = mail.search(None,'(UNSEEN)')
        emailnums = emailnums[0].split()

        if retcode == 'OK' and len(emailnums) > 0:

            for emailnum in emailnums:

                typ, data = mail.fetch(emailnum,'(RFC822)')
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                fromAddress = email_message["From"].split("@")[0]

                if fromAddress not in self.authedInputs:
                    continue

                if email_message.get_content_maintype() != 'multipart':
                    continue

                for part in email_message.walk():

                    if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                        
                        open(f"{self.outputDir}/{random.randint(0, 10000)}_{part.get_filename()}", 'wb').write(part.get_payload(decode=True))

            self.removeMail(mail)
            
        if len(os.listdir(self.outputDir)) > 0:
            self.followCommands()

    def followCommands(self):

        commands = self.aggregateCommands()
        subject = "Confirmation"
        error = "Error"

        for command, val in zip(commands.keys(), commands.values()):

            if command in self.recognizedCommands:

                valIsNone = val is None
                setInCommand = "set" in command
                addInCommand = "add" in command
                dropInCommand = "drop" in command

                if valIsNone and setInCommand:
                    message = f"Set commands require an integer assignment value, such as '{command}: 68'"
                    self.sendEmail(error, message)
                    continue

                elif (addInCommand or dropInCommand) and valIsNone:
                    message = f"Add/Drop commands require contact information, such as '{command}: contact'"
                    self.sendEmail(error, message)
                    continue

                elif not valIsNone and not addInCommand and not dropInCommand:

                    try:
                        val = int(val)

                    except:
                        message = f"Input ({command}: {val}) could not be coerced to integer"
                        self.sendEmail(error, message)
                        continue

                if setInCommand:

                    # 45 - 90 is an arbitrary choice, but figured it would cover most normal home temperatures
                    if command == "set target" and val in range(45, 90):
                        self.targetTemp = val
                        message = f"Target temperature set to {self.targetTemp}f as of {self.currentTime}"
                        self.sendEmail(subject, message)

                    # 1 - 3600 is an arbitrary choice; between once/second and once/hour
                    elif command == "set interval" and val in range(1, 3600):
                        self.interval = val
                        message = f"Interval set to {self.interval}s as of {self.currentTime}"
                        self.sendEmail(subject, message)

                elif "get" in command:

                    if command == "get target":
                        message = f"Target temperature is {self.targetTemp}f as of {self.currentTime}"
                        self.sendEmail(subject, message)

                    elif command == "get current":

                        tempInternal, tempExternal = 999, 999
                        # clear risk of infinite loop here, but this is the best solution to recieving false positive malfuntions so far
                        while tempInternal == 999 or tempExternal == 999:
                            tempInternal, rhInternal = self.internal.getTemp(useHI=False, wantRH=True) 
                            tempExternal, rhExternal = self.external.getTemp(useHI=False, wantRH=True)

                        message = f"As of {self.currentTime}, temperature and RH outside: {tempExternal}f, {rhExternal}%, and inside: {tempInternal}f, {rhInternal}% with target temperature of {self.targetTemp}f"
                        self.sendEmail(subject, message)

                    elif command == "get feels like":

                        tempInternal, tempExternal = 999, 999
                        # clear risk of infinite loop here, but this is the best solution to recieving false positive malfuntions so far
                        while tempInternal == 999 or tempExternal == 999:
                            tempInternal, rhInternal = self.internal.getTemp(wantRH=True) 
                            tempExternal, rhExternal = self.external.getTemp(wantRH=True)

                        message = f"As of {self.currentTime}, apparent temperature and RH outside: {tempExternal}f, {rhExternal}%, and inside: {tempInternal}f, {rhInternal}% with target temperature of {self.targetTemp}f"
                        self.sendEmail(subject, message)

                    elif command == "get commands":
                        commands = [recognized for recognized in self.recognizedCommands if "add" not in recognized and "drop" not in recognized]
                        message = f"{', '.join(commands)}"
                        self.sendEmail("Commands", message)

                    elif command == "get interval":
                        message = f"Interval is {self.interval}s as of {self.currentTime}"
                        self.sendEmail(subject, message)

                    elif command == "get dew point":
                        TdInternal = self.internal.getDewPoint()
                        TdExternal = self.internal.getDewPoint()
                        message = f"Dew point internal is {TdInternal}f and dew point external is {TdExternal}f as of {self.currentTime}"
                        self.sendEmail(subject, message)
                        
                elif addInCommand or dropInCommand:

                    # use this to match more general email addresses (^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$) 
                    # below will match only email addresses which conform to the 10 digit phone number + service provider extension (technically any extension)
                    match = re.fullmatch(r"(^[0-9]{10}@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", val)

                    if match is None:
                        message = f"Input value ({val}) must be a valid email address"
                        self.sendEmail(error, message)
                        continue

                    if addInCommand:
                        toggle = 1.0

                    elif dropInCommand:
                        toggle = None

                    contactFilt = self.contactsDF["Contact"] == val
                    rFilt = (self.contactsDF["Recipient"] != toggle) & contactFilt

                    recipientInCommand = "recipient" in command

                    if recipientInCommand and not self.contactsDF.loc[rFilt].empty:
                        self.contactsDF.loc[contactFilt, "Recipient"] = toggle
                        self.contactsDF.dropna(subset=["Recipient"], inplace=True)
                        self.contactsDF.to_csv(self.contactsFile, index=False)
                        self.recipientEmail = self.contactsDF.loc[self.contactsDF["Recipient"] == 1.0, "Contact"].astype(list)
                        self.authedInputs = [email.split("@")[0] for email in self.recipientEmail]

                    elif toggle and not self.contactsDF["Contact"].isin([val]).any():

                        if recipientInCommand:
                            self.contactsDF = self.contactsDF.append({"Contact": val, "Recipient": 1}, ignore_index=True, sort=False)
                            self.contactsDF.to_csv(self.contactsFile, index=False)
                            self.recipientEmail = self.contactsDF.loc[self.contactsDF["Recipient"] == 1.0, "Contact"].astype(list)
                            self.authedInputs = [email.split("@")[0] for email in self.recipientEmail]

                    else:
                        message = f"Cannot execute command ({command}), as it appears {val} is already listed as a contact of that type"
                        self.sendEmail(subject, message)

                    message = f"Command ({command}) completed successfully as of {self.currentTime}"
                    self.sendEmail(subject, message)
                    self.recipientEmail = self.contactsDF.loc[self.contactsDF["Recipient"] == 1.0, "Contact"].astype(list)
                    self.authedInputs = [email.split("@")[0] for email in self.recipientEmail]

                else:
                    message = f"Hm, something seems to have gone wrong. Please check your command ({command}) and value ({val}) for errors"
                    self.sendEmail(error, message)

            elif command == "kill":
                self.kill = True
                message = f"Are you sure you wish to kill this process?"
                self.sendEmail(subject, message)

            elif self.kill and command == "kill confirm":
                self.killConfirm = True
                message = f"Killing process..."
                self.sendEmail(subject, message)

    def aggregateCommands(self):

        commands = []
        messages = [item for item in os.listdir(self.outputDir) if item.endswith(".txt")]

        for item in messages:
            path = f"{self.outputDir}/{item}"

            with open(path, "r") as f:
                f = f.read()

                if "\n" in f:
                    vals = f.split("\n")

                elif ", " in f:
                    vals = f.split(", ")

                else:
                    vals = [f]

            commands += set(vals)
            os.remove(path)

        commands = set(commands)
        commands = {
                    (item.split(": ")[0].lower() if ": " in item else item.lower()): (item.split(": ")[1] if ": " in item and len(item.split(": ")) == 2 else None)
                    for item in commands
                }

        return commands

    def removeMail(self, mail):

        mail.store("1:*", '+X-GM-LABELS', '\\Trash')

        folders = ['"[Gmail]/Sent Mail"', '"[Gmail]/All Mail"']
        for folder in folders:
            status, messages = mail.select(folder)
            mail.store("1:*", '+X-GM-LABELS', '\\Trash')

        status, messages = mail.select('"[Gmail]/Trash"')
        mail.store("1:*", "+FLAGS", "\\Deleted")
        mail.expunge()

    def checkTemp(self):

        tempInternal = self.internal.getTemp() 
        tempExternal = self.external.getTemp()

        if tempInternal != 999 and tempExternal != 999:

            if not self.isOpen:

                openStatus = "Time to Open Windows!"
                openNotification = f"As of {self.currentTime}, temperature outside is {tempExternal}f and temperature inside is {tempInternal}f, with target temperature of {self.targetTemp}f"

                if tempExternal > self.targetTemp and tempInternal < self.targetTemp:

                    self.sendEmail(openStatus, openNotification)
                    self.isOpen = True

                elif tempExternal < self.targetTemp and tempInternal > self.targetTemp:

                    self.sendEmail(openStatus, openNotification)
                    self.isOpen = True

                # maybe the below two conditions send: "consider using ac/heat"?
                # if outside more than target, and inside more than outside, outside is cooler, so opening works to approach target
                elif tempExternal > self.targetTemp and tempInternal > tempExternal:

                    self.sendEmail(openStatus, openNotification)
                    self.isOpen = True

                # if outside less than target, and inside less than outside, outside is warmer, so opening works to approach target
                elif tempExternal < self.targetTemp and tempInternal < tempExternal:

                    self.sendEmail(openStatus, openNotification)
                    self.isOpen = True

            else:

                closeStatus = "Time to Close Windows!"
                closeNotification = f"As of {self.currentTime}, temperature outside is {tempExternal}f and temperature inside is {tempInternal}f, with target temperature of {self.targetTemp}f"

                if tempInternal >= self.targetTemp and tempInternal < tempExternal:

                    self.sendEmail(closeStatus, closeNotification)
                    self.isOpen = False

                elif tempInternal <= self.targetTemp and tempInternal > tempExternal:

                    self.sendEmail(closeStatus, closeNotification)
                    self.isOpen = False

    def logData(self):

        internalTemp, internalHI, internalRH = self.internal.getTemp(wantAll=True)
        externalTemp, externalHI, externalRH = self.external.getTemp(wantAll=True)

        # hope here is that it continues to loop and gets at least a single pair of good readings before the doLog reads False
        # certainly not the most elegant, but definitely the best way of avoiding false positive malfunction readings
        if internalTemp == 999 or externalTemp == 999:
            return

        else:
            self.logged = True
            logTime = time.strftime("%H:%M %m %d %Y", time.localtime())
            splitLog = logTime.split(" ")
            endLog = splitLog[0] == "23:45"
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
            self.dataLog.to_csv(self.logFile, index=False)

            # starting a new log at 11:45 pm by renaming current log, moving it to logs folder, then making a replacement log DF
            if endLog:
                newName = f"{splitLog[3]}_{splitLog[1]}_{splitLog[2]}_{self.logFile}"
                os.rename(self.logFile, newName)
                shutil.move(newName, f"{self.logDir}/{newName}")
                columns = [

                    "Year", "Month", "Day",
                    "Hour", "Minute",
                    "InternalTemp", "InternalHI", "InternalRH",
                    "ExternalTemp", "ExternalHI", "ExternalRH"
                    
                    ]
                self.dataLog = pd.DataFrame(columns=columns)
                self.dataLog.to_csv(self.logFile, index=False)

dht11 = Adafruit_DHT.DHT11
thermo = Thermostat(68, Sensor("Internal Temperature", dht11, 4), Sensor("External Temperature", dht11, 4))
subject = "Confirmation"
message = f"Process killed, exiting gracefully as of {thermo.currentTime}"
thermo.sendEmail(subject, message)
