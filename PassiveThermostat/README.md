# PassiveThermostat
### Work with Nature to Maintain a Pre-Set Temperature & Avoid Unnecessary Heating/Cooling

**About**:
The intent of this project is to enable you to regulate the temperature of a given space, relative to some other space, and do so without using additional energy. In the most common use case, when to open or close windows/vents. The specific logic relies on comparing the [apparent temperature](https://en.wikipedia.org/wiki/Apparent_temperature) of the spaces to a desired set point and to one another. This logic is outlined in more detail below.

When to open windows:
 - If the temperature outside is above the target, and the temperature inside is below the target
 - If the temperature outside is below the target, and the temperature inside is above the target
 - If the temperature outside is above the target, and the temperature inside is above the temperature outside
 - If the temperature outside is below the target, and the temperature inside is below the temperature outside

When to close windows:
 - If the temperature inside is equal to or above the target, and the temperature inside is below the temperature outside
 - If the temperature inside is equal to or below the target, and the temperature inside is above the temperature outside

Notice that the last two cases under **open** windows are a bit fuzzy. They serve the purpose of approaching the target temperature, but, depending on your preference, may be better suited as a test of when to activate heating/cooling systems.

~~Known Issues~~ Intended Features:
 - If you are very actively communicating with the thermostat via commands, as described below, and you notice that it stops responding to your messages, it is likely that your messages have been shunted to the spam folder of the email account used by the thermostat. To remediate this, go to the spam folder, select all the messages from the erroneously filtered sender, then select the Not Spam button. This should resolve the issue, prevent it moving forward, and act as an additional filter for any undesired contacts

**Materials and Cost** (as of 06/20/2021)
 - Raspberry Pi (or other [SBC](https://en.wikipedia.org/wiki/Single-board_computer))
   - [Raspberry Pi 3 B+ Kit](https://www.pishop.us/product/raspberry-pi-3-b-plus-starter-kit/): $65
   - [Raspberry Pi Zero W Kit](https://www.amazon.com/CanaKit-Raspberry-Wireless-Complete-Starter/dp/B07CMVDHWB/ref=pd_sbs_14/131-4316577-2525250?pd_rd_w=3SNDc&pf_rd_p=f8e24c42-8be0-4374-84aa-bb08fd897453&pf_rd_r=VJK610W0FARTBCNVHG0E&pd_rd_r=4eb32cbc-b5be-43f0-a489-93ce3fc763ef&pd_rd_wg=fesic&pd_rd_i=B07CMVDHWB&psc=1): $35
 - [DHT22 Sensor Module (Pack of 5)](https://www.amazon.com/gp/product/B01DKC2GQ0/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1): $12
 - [4 Wire Ribbon Cable (20 Meters)](https://www.amazon.com/65-6-Color-Extension-Cable-Strip/dp/B00L67YQ9W/ref=sr_1_3?keywords=3+wire+ribbon+cable&qid=1579014504&sr=8-3): $10
 - [Soldering Iron and Solder](https://www.amazon.com/Soldering-Kit-Temperature-Desoldering-Electronics/dp/B07XKZVG8Z/ref=sr_1_9?keywords=soldering+iron&qid=1580765871&sr=8-9): $11

 **Total: $68 - $98**

**Note:** This script was written to work with, and has only been tested using, the DHT11 and DHT22 temperature and humidity sensors. That said, any sensor with an analogous pin out and similar library should be compatible with what has already been written. I go into more detail on this point in Section 4.

**Disclaimer: It is likely illegal to use this kind of script/technique to automate advertising and the like, so just don't...**

### Key Steps:
1) Securing the Pi
2) Prototyping Set-Up
3) Establishing the Gmail Interface and Declaring Environmental Variables
4) Tweaking Specifics to Fit Your Needs
5) Forcing the Script to Run on Boot
6) Verifying Start on Boot
7) Final Set Up

## Securing the Pi

You may think "This is a simple Raspberry Pi project, who cares about hacking my single board computer?" and you've got a point, because most people are not hackers, and most hackers aren't interested in your project. That said, they may be interested in what your project can enable them to access once compromised. Take, for example, [this article](https://www.engadget.com/2019/06/20/nasa-jpl-cybersecurity-weaknesses/) detailing how NASA's Jet Propulsion Laboratory was breached via an unsecured Raspberry Pi. I don't mean to fear monger, but it is important that you consider the bigger picture, as you are adding a device to a larger network, which is almost certain to have more important devices and data attached to it than the Pi itself.

**That in mind, if you purchase the kit specified above, please begin this process by wiping the microSD card it comes with and reinstalling [Rasbian](https://www.raspberrypi.org/downloads/raspbian/) from scratch using [balenaEtcher](https://www.balena.io/etcher/), as this is a potential point of security concern; it is not clear who installed Rasbian there initially and what motives they may or may not have. This is a somewhat paranoid perspective, but, when protecting a larger network, it is advisable to account for this kind of thing. For more information on this process, please [see here](https://www.raspberrypi.org/documentation/installation/installing-images/).**

**Keep track of any changes you make when following the instructions below, as they will impact how we do things later. Specifically, after deleting the default user, note that anywhere a directory includes `/pi` you will need to, instead, use the username associated with the new account you have made, as in `/username`**

This section will configure the Pi in such a way that you will not be able to use `ssh`, `tcp`, etc. to connect to it; you will need physical access to the device to interface with it, and it will be near impossible to access remotely. If you do not wish to set the Pi up in this way, please do some independent research into how you might achieve the configuration you desire without introducing potential vulnerabilities to your network.

The first thing you should do in any situation like this is to change the default username and password for the Pi. To do so, we will create a new user with `sudo` (high level) privileges, then we will log in as the new user and delete the default account.

Begin by opening a terminal window and typing:

`sudo adduser __`

To create a new user, followed by:

`sudo adduser __ sudo`

To add that user to the "sudo" list

Where the blank is the new user's username. You will be prompted to enter, and confirm, a password for this user. Do not forget it. This new user, even though granted `sudo` (high level) privileges, will need to enter their password anytime they use a `sudo` command, thus adding an additional layer of security.

Next, navigate to the preferences pane and set "Auto login" to Disabled, before rebooting. Upon restart, log into the new user that you just made. Again, open a terminal window, this time typing:

`sudo userdel -r pi`

This will not only delete the default account, it also removes the associated home folder as well. If you see a message saying that it failed to locate that user's Mail Spool, or something to that effect, you can ignore it, as there was nothing to delete.

Finally, in the terminal, type the following to add the newly created user to the netdev group, which prevents the wireless interface icon from misbehaving (a reboot is required to see this change take effect in the GUI):

`sudo -i usermod -a -G netdev __`

Where, again, the blank is the new user's username.

Secondly, from the desktop, navigate to:

`Main Menu -> Preferences -> Raspberry Pi Configuration`

You can basically leave everything on the `System` tab alone. However, on the `Interfaces` tab, make sure everything is set to `Disable`.

Now we want to make sure the Pi automatically updates the operating system. To do this, we will use a single command:

`sudo apt-get install unattended-upgrades`

The default here is fine for most people, but, if you find it is not behaving as expected, try the following:

`sudo nano /etc/apt/apt.conf.d/50unattended-upgrades`

This tells the operating system that we have high level privilege (`sudo`), and that we'd like to use a text editor (`nano`) to access a file (`50unattended-upgrades`) in the specified location (the `apt.conf.d` folder). Once in that file, add:

`"origin=Raspbian codename=currentDistro label=Raspbian"`

Where `currentDistro` is the distribution of Raspbian you are using. As of the time of publication, the current distribution is named `Buster`.

If the above doesn't work for you, and you've confirmed that the `codename` you've provided is the same as the distribution you are using, try adding the following, in addition to the above line:

`"origin=Raspbian codename=currentDistro label=Raspberry Pi Foundation"`

Let's now set up a firewall using `ufw` (Uncomplicated Firewall) via these two commands:

`sudo apt install ufw`

Which downloads and installs Uncomplicated Firewall, and:

`sudo ufw enable`

Which enables the firewall and forces the operating system to start it on boot, so your Pi is protected as soon as it turns on. There are, of course, more complicated options, wherein you can specify ports that can or cannot be accessed, the protocols that are allowed to be used to access them, and much more, but, again, if you want a more detailed/customized set-up, I encourage you to research what exactly it is you need/want.

If you would like to allow SSH with caveats, [check out this guide](https://pimylifeup.com/raspberry-pi-ufw/), and remember to enable it in the settings. If you go this route, it does make a number of things easier, especially if you [install VSCode](https://code.visualstudio.com/docs/setup/raspberry-pi) and the [requisite Remote Development extensions](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack), which will enable you to develop on the Pi from a different machine.

## Prototyping Set-Up

This is relatively easy, especially if you purchase the DHT11/DHT22 as a module, rather than a stand alone sensor. The modules linked above include double sided bridge wires, which will make your life much easier during this stage, since you can use them to connect directly to both the module and GPIO pins you intend to use, for a more streamlined prototyping experience than using a breadboard. The module form of the sensor also allows you to avoid soldering on a pull-up resistor, since it is already included. If you did order the sensor alone, simply solder a 10k ohm resistor between the data and power pins, and then follow the below instructions.

Connect the power pin to either a 3.3 or 5v power pin, the ground pin to ground, and the data pin to one of the Pi's GPIO data pins. Be sure to note which data pin you've chosen, as you will need to alter the script to reflect that. In the script, I have specified GPIO pin four, which is physical pin 7, for all sensor instances in the script. This may be a bit confusing if you've never worked with electronics before, so I encourage you to review the Raspberry Pi's GPIO pinout documentation, which can be [found here](https://www.raspberrypi.org/documentation/usage/gpio/). In sum, it's important to realize that the physical pin numbering is independent of the GPIO number, since there is no need to count or refer to pins that do not handle data. After all, you'll likely never need to ping the voltage line for information.

Finally, I should mention that the script is set-up, initially, to pretend as if a single sensor is really two. This sounds way more confusing than it actually is; it is simply a proof of concept by way of software modeling, and is done by creating two instances with the same reference pin. Remember to change these reference pins as needed, or start with only a single sensor, otherwise you will receive some very confusing results.

## Establishing the Gmail Interface and Declaring Environmental Variables

**Note**: Because this program uses standard SMTP and IMAP interfaces, you are not constrained to using Gmail for this aspect of the project. You can use any email provider who will allow you to interface this way, though not all will provide API style tokens, requiring you to use your actual password. In the case where you choose, say, ProtonMail, you would need to interface with the [ProtonMail Bridge](https://protonmail.com/bridge/), which is only available to users who have purchased a subscription. However, using most other free providers should only require you to replace "gmail" with the domain of the provider you select. For example: imap.gmail.com and smtp.gmail.com become imap.(domain).com and smtp.(domain).com

To begin with, if you haven't already created a Gmail account, go do that now. It will require a verified phone number, so keep that in mind.

Once you have your Gmail account, go to [this link](https://myaccount.google.com/apppasswords), where you will be able to generate an app password. This is exactly what it sounds like -- a password to the account that is specific to a given app. I prefer to call this a "Token," so that's the term I will use from now on. The token you receive will be 16 characters long (any spaces included are purely for readability and are not part of the token itself), and you will only be shown once, so be sure to screenshot it or write it down.

There are a few major benefits to using a token, not the least of which is that you never risk exposing your real password. A few of the others include: being able to revisit the above link to monitor when the token was last used, the ability to generate multiple tokens for, and thus connect multiple projects/devices to a given account, and, again by visiting the same page, a single button to delete a given token and revoke access to the account.

I prefer holding the username and token I will be using to interface with the Gmail account in environmental variables. Unfortunately, I've not found a way to make environmental variables play nice with `systemd`, which is what we will be using to make this run on boot, so, even though I will initially ask you to add your Gmail username and token as environmental variables, they will need to be declared within the script itself later in this process, if you intend to use this in a headless configuration (no monitor, etc.) as we do. This is not as safe, especially if you're creating a repository and constantly uploading the script like I am. However, so long as you are mindful of this, it isn't a huge deal (i.e. don't forget to remove that info before sharing the script with anyone, or just point them here instead), and part of why using a token, rather than your password, boosts the overall security of the device/this project.

**Environmental variables are not necessary for the final implementation of this project, so, if you don't care about how to use them, you can skip ahead to the next section.**

So, what is an environmental variable? Basically, it is a variable that lives outside of your script, but which the script can still call and use when running. To hold the Gmail account information on the Raspberry Pi as such, open a terminal window and type:

`sudo nano /etc/profile`

When you hit enter, you will be faced with a fairly decent amount of text. Just ignore it. All we want to do is hit enter a few times to make some space at the top, and then type:

`export gmailUser="your_address@gmail.com"`

`export gmailToken="insert_token_generated_earlier_here"`

Once that is done, press `command + o` and then `enter` to confirm. This has written the file as specified into the location you originally passed in. Press `command + x` to exit the nano text editor. Just like that, you should are almost ready to try the script.

The only thing that is left is to ensure you have installed the proper libraries for this script to function as promised. Those are `Adafruit_DHT`, `Pandas`, and `email.message`, which can be installed via terminal using:

`sudo apt-get install ___`

If the above doesn't work, try:

`sudo pip3 install ___`

Where the blank is the library name. Then follow the on screen prompts.

## Tweaking Specifics to Fit Your Needs

Until this point, we've only really been talking about how to set up the computer that will run the script to monitor temperatures of interest. However, it is now time to start delving into the underlying assumptions and specifics of that code.

Your needs are likely different than ours, so let's outline the major places where changes will likely need to be made to the script itself. They are: your target temperature, the email account you wish to use with the Pi, and the contact information for the people whom you wish to notify. We've already touched on these things some above, but they deserve a bit more detail.

Let's start with the Pi's email account. While environmental variables have their merits, their use is an additional layer of complication here, so it is best to, at this point, to go ahead and change to declaring those variables in the script itself.

To do this, change the `gmailEmail` and `gmailPass` variables to the username and token associated with the account. These should be given as strings such that:

`gmailEmail = "email@gmail.com"`

`gmailPass = "gmailTokenHere"`

The values you provide should be in quotation marks as above.

For the temperatures you will be monitoring, I have created a class called Sensor which takes specific variables as input. The format for those is:

`variableName = Sensor("name/ID", sensorType, dataPinUsed)`

Where `"name/ID"` is a string that will be used to refer to the specific equipment being monitored, `sensorType` here is a DHT11, but that can be changed to DHT22 very easily by simply changing it to DHT22 anywhere the script says DHT11, and `dataPinUsed` refers to the GPIO pin the program should ping for data about a given temperature.

This class is meant to be flexible, and will work with any sensor that outputs a range of values. For example, and ease of use, the module that supports the DHT,[Adafruit Unified Sensor Driver](https://github.com/adafruit/Adafruit_Sensor), also supports other types, such as: Accelerometers, Gyroscopes, Photodetectors, Magnetometers, Barometers, and a few others.

These instances of the sensor class are not actually assigned to a variable in the script provided. Instead they are passed directly to the Thermostat class, as follows:

`variableName = Thermostat(targetTemp, Sensor1, Sensor2)`

Where `targetTemp` is an integer representing the desired temperature in degrees Fahrenheit (defaults to 68), `Sensor1` and `Sensor2` are instances of the Sensor class (instantiated as described above).

Finally, let's provide some contact info by creating a .csv files called "contacts" which should have Contact and Recipient headers. Under the Contact header, provide the individual's contact info, and a 1 or a 0 under the Recipient. A 1 indicates that the individual is to recieve notifications. It is easier to do things this way if you need to add more than one or two people. It is also required that there be at least one valid contact in this list from the beginning, or there will be no authorized contacts from which to recieve commands, including those used to add additional contacts to the dataframe.

Some of you might be confused here since I explicitly state that the notifications come through as text messages. This is true, but we're going to be very sneaky in how we make it happen. Rather than actually attaching a phone number to the Raspberry Pi by giving it a GSM/CDMA link, let's take advantage of a service the vast majority of carriers in the US, and likely other countries as well, already offer: Email -> Text. Within the script itself, and below, you will see an example phone number attached to the "vtext.com" domain via the @ symbol.

`8005882300@vtext.com`

This is a slight modification to the standard email address format, and, instead, uses the intended recipient's phone number attached to the domain their service provider offers for this transmutation from email to text message. In this case, the recipient uses Verizon, but I've included a list of domains for other (US) carriers in the comments of the code, as well as in more detail below.

```
Verizon: @vtext.com
ATT: @txt.att.net
GoogleFi: @msg.fi.google.com
Sprint: @messaging.sprintpcs.com
T-mobile: @tmomail.net
Cricket: @sms.cricketwireless.net
```

If you don't see your provider above, a simple [Google search](duckduckgo.com) will absolutely give you what you need.

Once that is done, open the script, hit run, and see what happens!

If you receive errors here, ensure that the name you provided for your environmental variable and what is being referenced within `os.environ.get(_)` (where the underscore is just a placeholder; `"gmailUser"`/`"gmailToken"`) are the same. If you want to confirm that there is an issue with your environmental variables, first confirm that the variable you have within `os.environ.get(_)` is a string (i.e. `os.environ.get("_")`). If you can confirm that, the next thing to try is commenting out the `os.environ.get(_)` lines entirely and providing the associated email and token to the script directly. Again, as a string.

If you skipped the environmental variables portion of this walkthrough and are having problems, make sure that the email address and token you provide in the script are spelled correctly and are declared as strings.

Otherwise, you, and any other specified recipients, should receive a text shortly notifying you that the system has started, as well as the date and time at start. This is only done the first time the script is run, and is meant to provide immediate feedback in a headless configuration, as well as a hedge against power outages, etc.

Even so, since there is no (built in) way for you to be notified if the script isn't running, you can always ensure the script is running by sending a text message to the Gmail account with a command, which are listed below.

```
set target: [int] <-- Used to change the target temperature (degrees Fahrenheit)
set interval: [int] <-- Used to change the frequency (in Seconds) at which requests are sent to the sensors

get target <-- Returns current target temperature
get current  <-- Returns current temperature and relative humidity values
get commands <-- Returns a list of recognized commands
get interval <-- Returns the current interval value
get feels like <-- Returns the apparent temperature and relative humidity values

add recipient: [contact] <-- Adds the provided contact to the Recipient list
drop recipient: [contact] <-- Drops the provided contact from the Recipient list
```

Multiple commands can be sent at once by including a return or ", " between them. Notice that the set and add/drop commands require ": " followed by user input. In the case of the set commands, the input expected is an integer value. For add/drop commands, it is a string which is evaluated with regex to ensure that it is likely a valid email address of format: (10 digit phone number)@(hostname). If you'd like to send messages to actual email address as well, I've included the regex for that as well, as a commented line. Add and drop alterations are saved in the previously mentioned contacts.csv, and so will persist in the event of power outage, etc. Other alterations are not current persisted.

**Disclaimer: There is not currently a process in place for a user added to these lists to be notified and confirm that they wish to be added. They may, however, drop themselves using the commands above. Even so, don't add people without their knowledge...**

## Forcing the Script to Run on Boot

As mentioned above, even though I initially asked you to add your Gmail username and token as environmental variables, they will now need to be declared within the script itself. This is not as safe if you're creating a repository and constantly uploading the script like I am, however, so long as you are mindful of this, it isn't a huge deal, just don't forget to remove that info before sharing the script with anyone, or point them here instead. On that note, this is another example of why using a token, rather than your password, is a boost to your security.

Create a folder in `/home/pi` and call it PassiveThermostat. Place the PassiveThermostat.py script there. Now, to reference this script in the future, we will provide this directory:

`/home/pi/PassiveThermostat/PassiveThermostat.py`

To make our `systemd` service, which is what will tell the operating system that our script is needed and should be run on boot, open Terminal and type the following command:

`sudo nano /etc/systemd/system/PassiveThermostat.service`

This tells the operating system that we have high level privilege (`sudo`), and that we'd like to use a text editor (`nano`) to access (in this case, we are actually creating) a file (`SmartLab.service`) in the specified location (the `system` folder, which is nested inside the `systemd` and `etc` folders).

Now, within terminal, type the following:
```
[Unit]
Description=Passive Thermostat Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u PassiveThermostat.py
WorkingDirectory=/home/pi/PassiveThermostat
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

>`After=network.target` tells the operating system that the script is to be run after the network connection has been verified. This is obviously important, because the first thing our script does is notify us that it is online.

>`ExecStart=/usr/bin/python3 -u PassiveThermostat.py` specifies that we are using Python 3 when we try to run our script, though I'm not sure what exactly the `-u` flag refers to here, and didn't have much success when looking it up.

>`Restart=always` tells the operating system to restart the script if there is ever an error with it. This is another place where I've hedged against the uncertainty inherent in a headless, autonomous system.

>`User=pi` refers to the account associated with the device from which you intend to run this script.

>`WantedBy=multi-user.target` is another place where we have told the operating system that we need a certain thing before running our script. In this case, I believe it is meant to restrict the script to being run after the user has successfully logged in/after the user interface has come online.

Once that is done, press `command + o` and then `enter` to confirm. This will write the file as specified into the location you originally passed in. Press `command + x` to exit the nano text editor.

Since we have made a change, we now need to ask the system to refresh some things and get this updated information. We do that by entering:

`sudo systemctl daemon-reload`

## Verifying Start on Boot

We are now ready to give everything a shot and verify that it works as expected. To do so, the following command is used:

`sudo systemctl start PassiveThermostat.service`

This should result in an identical outcome as when you ran this script in the Thonny IDE earlier. If this is not the case, there is an error somewhere, and I encourage you to review these instructions in order to retrace your steps. Alternatively, if I have omitted anything, made an error, and/or done a poor job with phrasing/conveying something, don't hesitate to contact me directly, and/or issue a pull request to address it directly.

When you have confirmed that it works as expected, you can use a slightly modified version of the previous command to stop the script from continuing to run:

`sudo systemctl stop PassiveThermostat.service`

Finally, to tell the operating system that we do in fact want this to run at boot every time, we need to provide the following:

`sudo systemctl enable PassiveThermostat.service`

And now, just to confirm this has worked, let's restart using:

`sudo reboot`

If everything is doing what it is supposed to, you should start receiving notifications once the Pi has booted in. To stop this, but leave start on boot enabled, use:

`sudo systemctl stop PassiveThermostat.service`

To disable it on boot, use:

`sudo systemctl disable PassiveThermostat.service`

That's it! You are now ready to wire everything up and start maintaining a livable temperature in your space through passive heating and cooling.

## Final Set Up

My recommendation here is very simple: take the double sided bridge wires included with the sensors, cut them in half, and use the four wire ribbon cable (linked above) to, essentially, just extend their range by soldering one end to one side and vice versa. You should be left with an extremely long version of the initial bridge wires, which will allow you to quickly assemble, replace failed parts, and/or disassemble the project. If you do use the ribbon cable specified above, you should only need three of the four wires. This is regardless of whether or not you are using the module form of the sensor.

Congrats on finishing this walkthrough and good luck!
