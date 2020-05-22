# Traceroute

Get tracroute info by command line interface

Grab source Ip, packet, AS number, and output as a JSON file.

Download File:

clone the file to local

`https://github.com/klauswong123/routertracert.git`


**1. Prerequisite**

- Python: 3.6 or above

- Linux Kernel

 
**2. Install Packages**

**- Debian/Ubuntu**

```
sudo add-apt-repository universe

sudo apt update

sudo apt-get install inetutils-traceroute

sudo apt install python3-pip

pip3 install requests
```


**- CentOS 7**

```
yum -y update

yum install traceroute -y

sudo yum install python36-setuptools

sudo easy_install pip

pip3 install requests
```



**3. Run Program**

Type 'python3 traceroute -help' to get the help interface like following:
```

Usage: python3 traceroute.py [-o output-file] [-ia] [-is] target-name(>=1)
                
Options:" 
                
    -o output-file                Default: $host-name-$date.json. Only Json file is available.
            
    -ia                           Ignore AS number: Don't show AS number in the output file
           
    -is                           Ignore ServiceProvider: Don't show service provider
               
    -help                         show help interface
                
    target-name                   IP address or domain name. Available for multiple input
                
"Example: python3 traceroute.py -o this-machine.json -ia -is 111.111.111.111 127.0.0.1" 
                

Input the ip and args you want to traceroute, and wait a minute to finish.

```

**4. Output**


File Output: 


AsNumber.txt: File to store AS number and Service Provider


$hostname-$time/input_name.json: Data convert to json form, and AS number is added in hop


routers.log: a log file contains all running record. Clear the oldest one if size exceed **1000** blocks.




