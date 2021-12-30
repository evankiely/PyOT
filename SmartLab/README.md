# Smart Lab
### Autonomous Monitoring of Laboratory Equipment with Text Message Notifications

**Materials and Cost** (as of 06/20/2021)
 - Raspberry Pi (or other [SBC](https://en.wikipedia.org/wiki/Single-board_computer))
   - [Raspberry Pi 3 B+ Kit](https://www.pishop.us/product/raspberry-pi-3-b-plus-starter-kit/): $65
   - [Raspberry Pi Zero W Kit](https://www.amazon.com/CanaKit-Raspberry-Wireless-Complete-Starter/dp/B07CMVDHWB/ref=pd_sbs_14/131-4316577-2525250?pd_rd_w=3SNDc&pf_rd_p=f8e24c42-8be0-4374-84aa-bb08fd897453&pf_rd_r=VJK610W0FARTBCNVHG0E&pd_rd_r=4eb32cbc-b5be-43f0-a489-93ce3fc763ef&pd_rd_wg=fesic&pd_rd_i=B07CMVDHWB&psc=1): $35
 - [DHT22 Sensor Module (Pack of 5)](https://www.amazon.com/gp/product/B01DKC2GQ0/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1): $12
 - [4 Wire Ribbon Cable (20 Meters)](https://www.amazon.com/65-6-Color-Extension-Cable-Strip/dp/B00L67YQ9W/ref=sr_1_3?keywords=3+wire+ribbon+cable&qid=1579014504&sr=8-3): $10
 - [Soldering Iron and Solder](https://www.amazon.com/Soldering-Kit-Temperature-Desoldering-Electronics/dp/B07XKZVG8Z/ref=sr_1_9?keywords=soldering+iron&qid=1580765871&sr=8-9): $11

 **Total: $68 - $98**

**Note 1:** As this was originally written during my time in the [Gilbert-Ross Lab](https://www.gilbertrosslab.com), acknowledgement/citation would be appreciated if used in a meaningful way to facilitate research culminating in a publication, and/or if modified to serve such a purpose.

**Note 2:** This script was written to work with, and has only been tested using, the DHT11 and DHT22 temperature and humidity sensors. That said, any sensor with an analogous pin out and similar library should be compatible with what has already been written. I go into more detail on this point in Section 5.

**Disclaimer: It is likely illegal to use this kind of script/technique to automate advertising and the like, so just don't...**

### Key Steps:
1) Modifying the Pi for Enterprise Networking (Incomplete)
2) Securing the Pi for Institutional Use (Incomplete/Under Review)
3) Prototyping Set-Up
4) Establishing the Gmail Interface and Declaring Environmental Variables
5) Tweaking Specifics to Fit Your Needs
6) Forcing the Script to Run on Boot
7) Verifying Start on Boot
8) Final Set Up

## Modifying the Pi for Enterprise Networking (Incomplete)

There is a good chance that the Pi does not play nice with your institution's wireless network out of the box. Typically, this is a result of the institution making use of an Enterprise network, which requires a set of certificates that allow you to connect, in addition to a username and password. Every institution is different, so I recommend, if you're having trouble connecting, that you contact your IT department for assistance. If you're adventurous, more knowledgable about this kind of thing, or just curious, you can try the following, which worked for me. Alternatively, feel free to omit the wireless component all together and skip this if using ethernet.

First though, please begin the security process outlined below. You should complete all the steps that can be done without an internet connection, up to the point where you have successfully created a new user profile, at which point you will be directed to return here.

## Securing the Pi for Institutional Use (Incomplete/Under Review)

If you are planning to do this project, I strongly encourage you to reference the Standard Operating Procedures for your institution, when it comes to adding devices to the network. You may think "This is a simple Raspberry Pi project, who cares about hacking my single board computer?" and you've got a point, because most people are not hackers, and most hackers aren't interested in your project. That said, they may be interested in what your project can enable them to access once compromised. Take, for example, [this article](https://www.engadget.com/2019/06/20/nasa-jpl-cybersecurity-weaknesses/) detailing how NASA's Jet Propulsion Laboratory was breached via an unsecured Raspberry Pi. I don't mean to fear monger, but it is important that you consider the bigger picture, as you are adding a device to a larger network, which is almost certain to have more important devices and data attached to it than the Pi itself.

**That in mind, if you purchase the kit specified above, please begin this process by wiping the microSD card it comes with and reinstalling [Rasbian](https://www.raspberrypi.org/downloads/raspbian/) from scratch using [balenaEtcher](https://www.balena.io/etcher/), as this is a potential point of security concern; it is not clear who installed Rasbian there initially and what motives they may or may not have. This is a somewhat paranoid perspective, but, when protecting a larger network, it is advisable to account for this kind of thing. For more information on this process, please [see here](https://www.raspberrypi.org/documentation/installation/installing-images/).**

**Keep track of any changes you make when following the instructions below, as they will impact how we do things later. Specifically, after deleting the default user, note that anywhere a directory includes `/pi` you will need to, instead, use the username associated with the new account you have made, as in `/username`**

Furthermore, this section will configure the Pi in such a way that you will not be able to use `ssh`, `tcp`, etc. to connect to it; you will need physical access to the device to interface with it, and it will be near impossible to access remotely. If you do not wish to set the Pi up in this way, please do some independent research into how you might achieve the configuration you desire without introducing potential vulnerabilities to your network. We are choosing this configuration not because it is the best option for the most people, nor because our institution requires it, but because we have no need to keep these potential security vulnerabilities open, since we will be able to access the device quickly and move it to a location where it can be attached to a display for diagnostics, etc. Additionally, this project is designed to be "Set and Forget," so it is unlikely that need will arise, as the script will notify you of anything that may require your attention, and will return to a homeostatic state when the reported problem has been addressed.

Even so, we do firmly believe this is the ideal configuration for most of the individuals in our target audience. That is, we believe the individuals reading this guide are likely to be scientists not well versed in electronics and/or programming, let alone cybersecurity, and, thus, have neither the technical know-how to use a remote interface protocol, nor the desire to spend the time learning the details of how to do so in an optimal (read: secure) way.

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

**From here, if you have not already set the Pi up for Enterprise Networking, and you don't have an alternative method for connecting the Pi to the internet, jump back up to, and complete, the first section, because an internet connection is required for what we will be doing next.**

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

Which enables the firewall and forces the operating system to start it on boot, so your Pi is protected as soon as it turns on. There are, of course, more complicated options, wherein you can specify ports that can or cannot be accessed, the protocols that are allowed to be used to access them, and much more, but, again, if you want a more detailed/customized set-up, I encourage you to research what exactly it is you need/want and, if necessary, reach out to your institution's IT department.

If you would like to allow SSH with caveats, [check out this guide](https://pimylifeup.com/raspberry-pi-ufw/), and remember to enable it in the settings

## Prototyping Set-Up

This is relatively easy, especially if you purchase the DHT11/DHT22 as a module, rather than a stand alone sensor. The modules linked above include double sided bridge wires, which will make your life much easier during this stage, since you can use them to connect directly to both the module and GPIO pins you intend to use, for a more streamlined prototyping experience than using a breadboard. The module form of the sensor also allows you to avoid soldering on a pull-up resistor, since it is already included. If you did order the sensor alone, simply solder a 10k ohm resistor between the data and power pins, and then follow the below instructions.

Connect the power pin to either a 3.3 or 5v power pin, the ground pin to ground, and the data pin to one of the Pi's GPIO data pins. Be sure to note which data pin you've chosen, as you will need to alter the script to reflect that. In the script, I have specified GPIO pin four, which is physical pin 7, for all equipment variables in the script. This may be a bit confusing if you've never worked with electronics before, so I encourage you to review the Raspberry Pi's GPIO pinout documentation, which can be [found here](https://www.raspberrypi.org/documentation/usage/gpio/). In sum, it's important to realize that the physical pin numbering is independent of the GPIO number, since there is no need to count or refer to pins that do not handle data. After all, you'll likely never need to ping the voltage line for information.

Finally, I should mention that the script is set-up, initially, to pretend as if a single sensor is really four. This sounds way more confusing than it actually is; it is simply a proof of concept by way of software modeling, and is done by creating four instances with the same reference pin. Remember to change these reference pins as needed, or start with only a single sensor, otherwise you will receive some very confusing results.

## Establishing the Gmail Interface and Declaring Environmental Variables

To begin with, if you haven't already created a Gmail account, go do that now. It will require a verified phone number, so keep that in mind.

Once you have your Gmail account, go to [this link](https://myaccount.google.com/apppasswords), where you will be able to generate an app password. This is exactly what it sounds like -- a password to the account that is specific to a given app. I prefer to call this a "Token," so that's the term I will use from now on. The token you receive will be 16 characters long (any spaces included are purely for readability and are not part of the token itself), and you will only be shown once, so be sure to screenshot it or write it down.

There are a few major benefits to using a token, not the least of which is that you never risk exposing your real password. A few of the others include: being able to revisit the above link to monitor when the token was last used, the ability to generate multiple tokens for, and thus connect multiple projects/devices to a given account, and, again by visiting the same page, a single button to delete a given token and revoke access to the account.

I prefer holding the username and token I will be using to interface with the Gmail account in environmental variables. Unfortunately, I've not found a way to make environmental variables play nice with `systemd`, which is what we will be using to make this run on boot, so, even though I will initially ask you to add your Gmail username and token as environmental variables, they will need to be declared within the script itself later in this process, if you intend to use this in a headless (no monitor, etc.) configuration as we do. This is not as safe, especially if you're creating a repository and constantly uploading the script like I am. However, so long as you are mindful of this, it isn't a huge deal (i.e. don't forget to remove that info before sharing the script with anyone, or just point them here instead), and part of why using a token, rather than your password, boosts the overall security of the device/this project.

**Environmental variables are not necessary for the final implementation of this project, so, if you don't care about how to use them, you can skip ahead to the next section.**

So, what is an environmental variable? Basically, it is a variable that lives outside of your script, but which the script can still call and use when running. To hold the Gmail account information on the Raspberry Pi as such, open a terminal window and type:

`sudo nano /etc/profile`

When you hit enter, you will be faced with a fairly decent amount of code. Just ignore it. All we want to do is hit enter a few times to make some space at the top, and then type:

`export gmailUser="your_address@gmail.com"`

`export gmailToken="insert_token_generated_earlier_here"`

Once that is done, press `command + o` and then `enter` to confirm. This has written the file as specified into the location you originally passed in. Press `command + x` to exit the nano text editor. Just like that, you should are almost ready to try the script.

The only thing that is left is to ensure you have installed the proper libraries for this script to function as promised. Those are `Adafruit_DHT` and `email.message`, which can be installed via terminal using:

`sudo apt-get install ___`

If the above doesn't work, try:

`sudo pip3 install ___`

Where the blank is the library name. Then follow the on screen prompts.

## Tweaking Specifics to Fit Your Needs

Until this point, we've only really been talking about how to set up the computer that will run the script to monitor the equipment of interest, however, it is now time to start delving into the underlying assumptions and specifics of that code.

Your needs are likely different than ours, so let's outline the major places where changes will likely need to be made to the script itself. They are: your equipment, and the range values associated with them, the email account you wish to use with the Pi, and the contact information for the people whom you wish to notify. We've already touched on these things some above, but they deserve a bit more detail.

Let's start with the Pi's email account. While environmental variables have their merits, their use is an additional layer of complication here, so it is best to, at this point, to go ahead and change to declaring those variables in the script itself.

To do this, change the `gmailEmail` and `gmailPass` variables to the username and token associated with the account. These should be given as strings such that:

`gmailEmail = "email@gmail.com"`

`gmailPass = "gmailTokenHere"`

The values you provide should be in quotation marks as above.

For the equipment you will be using, I have created a class called Equipment that takes specific variables as input. The format for those is:

`variableName = Equipment("name/ID", sensorType, dataPinUsed, lowerBound, upperBound)`

Where `"name/ID"` is a string that will be used to refer to the specific equipment being monitored, `sensorType` here is a DHT11, but that can be changed to DHT22 very easily by simply changing it to DHT22 anywhere the script says DHT11, `dataPinUsed` refers to the GPIO pin the program should ping for data about a given piece of equipment, and the `upper/lowerBound` variables dictate the minimum and maximum values of the acceptable temperature range for that piece of equipment.

This class is meant to be flexible, and will work with any sensor that outputs a range of values. For example, and ease of use, the module that supports the DHT,[Adafruit Unified Sensor Driver](https://github.com/adafruit/Adafruit_Sensor), also supports other types, such as: Accelerometers, Gyroscopes, Photodetectors, Magnetometers, Barometers, and a few others.

Finally, let's provide the contact info for our lab members by making a slight change to lines 94 and 95, where we specify the recipient email address, and where you will now enter your contact info. Some of you might be confused here since I explicitly state that the notifications come through as text messages. This is true, but we're going to be very sneaky in how we make it happen.

Rather than actually attaching a phone number to the Raspberry Pi by giving it a GSM/CDMA link, let's take advantage of a service the vast majority of carriers in the US, and likely other countries as well, already offer: Email -> Text. Within the script itself, and below, you will see an example phone number attached to the "vtext.com" domain via the @ symbol.

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

It's now really as easy as adding them, as strings, to the `recipientEmail` and/or `emergencyContact` lists, which can accept more than one recipient (and technically up to hundreds+). Keep in mind that anyone who is an emergency contact will receive special notifications when a sensor failure is detected. If you wish to receive both standard power on and temperature warnings, in addition to notifications about sensor failure, you must be included in both lists.

Once that is done, open the script in the Thonny IDE that comes with Raspbian, hit run, and see what happens!

If you receive errors here, ensure that the name you provided for your environmental variable and what is being referenced within `os.environ.get(_)` (where the underscore is just a placeholder; `"gmailUser"`/`"gmailToken"`) are the same. If you want to confirm that there is an issue with your environmental variables, first confirm that the variable you have within `os.environ.get(_)` is a string (i.e. `os.environ.get("_")`). If you can confirm that, the next thing to try is commenting out the `os.environ.get(_)` lines entirely and providing the associated email and token to the script directly. Again, as a string. If you skipped the environmental variables portion of this walkthrough and are having problems, make sure that the email address and token you provide in the script are spelled correctly and are declared as strings.

Otherwise, you, and any other specified recipients, should receive a text shortly notifying you that the system has started, as well as the date and time at start. This is only done the first time the script is run, and is meant to provide immediate feedback in a headless configuration, as well as a hedge against power outages, etc. Even so, since there is no (built in) way for you to be notified if the script isn't running, you can always ensure the script is running by purposefully exposing a sensor to a temperature it is not coded for, or turning the Pi off and then back on again.

I have also implemented a check that tracks the number of times in a row a given sensor has been pinged, and which will notify the emergency contact of a potential sensor failure, if a given threshold is reached, and a preventative check that turns off monitoring for a given piece of equipment for a set time, if that piece of equipment had previously found to be malfunctioning. This is to prevent multiple notifications about the same issue within a short period of time, and does not impede/disable checking the remaining equipment.

## Forcing the Script to Run on Boot

As mentioned above, even though I initially asked you to add your Gmail username and token as environmental variables, they will now need to be declared within the script itself. This is not as safe if you're creating a repository and constantly uploading the script like I am, however, so long as you are mindful of this, it isn't a huge deal, just don't forget to remove that info before sharing the script with anyone, or point them here instead. On that note, this is another example of why using a token, rather than your password, is a boost to your security.

Create a folder in `/home/pi` and call it SmartLab. Place the SmartLab.py script there. Now, to reference this script in the future, we will provide this directory:

`/home/pi/SmartLab/SmartLab.py`

To make our `systemd` service, which is what will tell the operating system that our script is needed and should be run on boot, open Terminal and type the following command:

`sudo nano /etc/systemd/system/SmartLab.service`

This tells the operating system that we have high level privilege (`sudo`), and that we'd like to use a text editor (`nano`) to access (in this case, we are actually creating) a file (`SmartLab.service`) in the specified location (the `system` folder, which is nested inside the `systemd` and `etc` folders).

Now, within terminal, type the following:
```
[Unit]
Description=Smart Lab Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u SmartLab.py
WorkingDirectory=/home/pi/SmartLab
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

>`After=network.target` tells the operating system that the script is to be run after the network connection has been verified. This is obviously important, because the first thing our script does is notify us that it is online.

>`ExecStart=/usr/bin/python3 -u SmartLab.py` specifies that we are using Python 3 when we try to run our script, though I'm not sure what exactly the `-u` flag refers to here, and didn't have much success when looking it up.

>`Restart=always` tells the operating system to restart the script if there is ever an error with it. This is another place where I've hedged against the uncertainty inherent in a headless, autonomous system.

>`User=pi` refers to the account associated with the device from which you intend to run this script.

>`WantedBy=multi-user.target` is another place where we have told the operating system that we need a certain thing before running our script. In this case, I believe it is meant to restrict the script to being run after the user has successfully logged in/after the user interface has come online.

Once that is done, press `command + o` and then `enter` to confirm. This will write the file as specified into the location you originally passed in. Press `command + x` to exit the nano text editor.

Since we have made a change, we now need to ask the system to refresh somethings and get this updated information. We do that by entering:

`sudo systemctl daemon-reload`

## Verifying Start on Boot

We are now ready to give everything a shot and verify that it works as expected. To do so, the following command is used:

`sudo systemctl start SmartLab.service`

This should result in an identical outcome as when you ran this script in the Thonny IDE earlier. If this is not the case, there is an error somewhere, and I encourage you to review these instructions in order to retrace your steps. Alternatively, if I have omitted anything, made an error, and/or done a poor job with phrasing/conveying something, don't hesitate to contact me directly, and/or issue a pull request to address it directly.

When you have confirmed that it works as expected, you can use a slightly modified version of the previous command to stop the script from continuing to run:

`sudo systemctl stop SmartLab.service`

Finally, to tell the operating system that we do in fact want this to run at boot every time, we need to provide the following:

`sudo systemctl enable SmartLab.service`

And now, just to confirm this has worked, let's restart using:

`sudo reboot`

If everything is doing what it is supposed to, you should start receiving notifications once the Pi has booted in. To stop this, but leave start on boot enabled, use:

`sudo systemctl stop SmartLab.service`

To disable it on boot, use:

`sudo systemctl disable SmartLab.service`

That's it! You are now ready to wire everything up and start monitoring your newly "Smart" Lab.

## Final Set Up

My recommendation here is very simple: take the double sided bridge wires included with the sensors, cut them in half, and use the four wire ribbon cable (linked above) to, essentially, just extend their range by soldering one end to one side and vice versa. You should be left with an extremely long version of the initial bridge wires, which will allow you to quickly assemble, replace failed parts, and/or disassemble the project. If you do use the ribbon cable specified above, you should only need three of the four wires. This is regardless of whether or not you are using the module form of the sensor.

Congrats on finishing this walkthrough and good luck!
