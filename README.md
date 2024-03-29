# tumour-evolution-server

## Running locally
Run the webserver: `python web_server.py`

## Getting a Nectar VM:
- In Nectar, apply for allocation and enter the project details.
- Approval can take anywhere from a few minutes to a few days.
- Navigate into allocation (project) in the Nectar portal. The project name is tumour-evolution.

## Launch instance:
- Name: tumour-evolution
- OS: ubuntu 20.04
- Flavor: m3.medium (4 CPU, 8GB RAM)
- Add or create an ssh key by going to Compute > Key Pairs > Create Key pair, use this as the key when the instance is created.*
- Once launched, take note of the IP address (130.216.216.141)

*SSH key is in SecretServer: https://secretserver.auckland.ac.nz/secretserver/SecretView.aspx?secretid=33196
## Create DNS record:
- Go to DNS -> zones
- click Create Record Set on the auckland-cer.cloud.edu.au. zone
- Type is A
- name the record set: server.tumour-evolution.cloud.edu.au. (note the dot at the end)
- leave default ttl
- in the record, add the IP address of the newly launched instance
- Submit
-> you can now see your record under Record Sets if you go into the zone

## Create a security group for http and https:
- the instance already has the default sec group.
- Create a new security group: Network -> Security Groups
- Create security group..
- Call it 'http and https'
- Add rules using the existing dropdowns, add on http and https
- Save

## Edit the default security group:
- remove the two rules for ingress from anywhere
- add the SSH rule from the dropdown
- add the ICMP rule from the dropdown

Now add the new security group to the instance:
- Go to instance, edit security groups, add the http and https group

We should now be able to SSH into our instance at *server.tumour-evolution.cloud.edu.au*

## SSH into instance
Using Mobaxterm, create a new SSH session:
- remote host = server.tumour-evolution.cloud.edu.au
- username = ubuntu
- port = 22
under advanced settings, enter the path to the SSH key:
e.g. C:\Users\rmcc872\.ssh\tumourevokey.txt

Now we are in, we need to do some updates, and install some stuff:
```
sudo apt-get update
sudo apt install git python3 python3-pip htop
python3 -V
```

## Clone our webserver repo:
```
git clone https://github.com/UoA-eResearch/tumour-evolution-server.git
```

Install dependencies
```
cd tumour-evolution-server/
sudo pip3 install -r requirements.txt
```

## Run server in the background
Get nohup, so we can run the webserver as a background task:
```
sudo apt-get install nohup
nohup
nohup --help
```

Make the webserver file executable: `chmod +x ./web_server.py`

Run the webserver: `./web_server.py`
- use ctrl-c to quit once you're done

List files: `ls -lah`
- should now be a db.json file

Now run the webserver as a background process: `nohup ./web_server.py &`

View running python tasks: `ps aux | grep python`

```
root         538  0.0  0.2  31656 18164 ?        Ss   22:20   0:00 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers
root         544  0.0  0.2 398660 20712 ?        Ssl  22:20   0:03 /usr/bin/python3 /usr/bin/fail2ban-server -xf start
root         575  0.0  0.2 110472 21140 ?        Ssl  22:20   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
ubuntu      6675  0.0  0.2  30104 18196 pts/0    S    23:37   0:00 python3 ./web_server.py
ubuntu      6678  0.0  0.0   9036   728 pts/0    S+   23:40   0:00 grep --color=auto python
```

webserver = process id 6675

## Configure the timezone (optional):
`sudo dpkg-reconfigure tzdata`

```
Current default time zone: 'Pacific/Auckland'
Local time is now:      Tue Mar  9 12:42:09 NZDT 2021.
Universal Time is now:  Mon Mar  8 23:42:09 UTC 2021.
```

## Apache HTTP Server
Install Apache, we will use this as our proxy so we can have secure websockets:
```
sudo apt install apache2
sudo a2enmod
-- choose proxy_wstunnel

sudo systemctl restart apache2
sudo service apache2 status
```


## Set up an SSL certificate
```
sudo apt install certbot
apt-cache search certbot
sudo apt install python3-certbot-apache
sudo certbot --apache
-- enter an email address
-- agree to t&c's
-- choose option 2 for only allowing https traffic
```

You can check the SSL is working properly (here)[https://www.ssllabs.com/ssltest/analyze.html?d=server.tumour-evolution.cloud.edu.au]

## Configure the apache proxy:
Create a file proxy.conf and open with nano: `sudo nano /etc/apache2/sites-available/proxy.conf`

- Add the following lines:
```
ProxyPass / ws://localhost:6789
Header set Access-Control-Allow-Origin "*"
```
- save the file
- Enable headers module: `sudo a2enmod headers`
- Enable the site: `sudo a2ensite` (choose proxy)

## Restart:
`sudo systemctl restart apache2`
`systemctl status apache2.service`

```
apache2.service - The Apache HTTP Server
     Loaded: loaded (/lib/systemd/system/apache2.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2021-03-09 13:19:48 NZDT; 4s ago
       Docs: https://httpd.apache.org/docs/2.4/
    Process: 8903 ExecStart=/usr/sbin/apachectl start (code=exited, status=0/SUCCESS)
   Main PID: 8920 (apache2)
      Tasks: 55 (limit: 9521)
     Memory: 6.7M
     CGroup: /system.slice/apache2.service
             +-8920 /usr/sbin/apache2 -k start
             +-8921 /usr/sbin/apache2 -k start
             +-8922 /usr/sbin/apache2 -k start

Mar 09 13:19:48 tumour-evolution systemd[1]: Starting The Apache HTTP Server...
Mar 09 13:19:48 tumour-evolution apachectl[8911]: AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 12>
Mar 09 13:19:48 tumour-evolution systemd[1]: Started The Apache HTTP Server.
```

We now have all requests to our websocket server going via our apache proxy, allowing https traffic only
We use wss protocol, so our sockets endpoint is:
*wss://server.tumour-evolution.cloud.edu.au*



## Stop and restart the webserver process

### Find the process id of ./web_server.py:
`ps aux | grep python`

### Kill the process:
`kill -9 <PROCESS_ID>`

### Restart the webserver in background:
`nohup ./web_server.py &`

### Restart the Apache server:
`sudo systemctl restart apache2`

## Permission Errors 
If you get any permission errors (could especially happen after any updates to the web_server file, e.g. after a git pull), 
you might need to change the file permissions:
`chmod +x ./web_server.py`

## Renew the SSL certificate
certbot should be set up to auto renew - see https://eff-certbot.readthedocs.io/en/stable/using.html#automated-renewals)

However, if it needs to be manually renewed, run the following command once the certificate is due for renewal:
`sudo certbot renew`
