import subprocess
import requests
import re
import json
import logging
from datetime import datetime,timedelta, timezone
import sys
import os

def timetz(*args):
    return (datetime.now()+timedelta(hours=8)).timetuple()
logging.Formatter.converter = timetz
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='router.log')


class Router:
    def __init__(self, inputIp, filename,ignore_is,ignore_ia):
        self.logfile = "router.log"
        self.filename= filename
        self.ignore_is = ignore_is
        self.ignore_ia = ignore_ia
        self.currentDir = os.path.dirname(os.path.abspath(__file__))
        self.rttList=[]
        self.ip = inputIp
        self.ipList = []
        self.ipApi = []
        self.newIp = []
        self.reqStatus = []
        self.asList = []
        self.asProvider = []
        self.asIp = []
        self.jsonFile = self.fileProcess()

    def fileProcess(self):
        if not os.path.exists(self.currentDir+'/'+self.ip):
            os.makedirs(self.currentDir+'/'+self.ip)
        filepath = self.currentDir+'/'+self.ip+'/'
        nowTime = (((str(datetime.now()+timedelta(hours=8))).replace(" ","-").replace(":","-"))).split(".")[0]
        jsonFile = filepath+self.ip+'-'+str(nowTime)+'.json' if not self.filename else filepath+self.filename
        return jsonFile

    def runTraceroute(self):
        logging.info("Run Program with ip {}".format(self.ip))
        #run traceroute command
        self.cmdOutput()
        #if not new ip which not in AsNumber.txt, skip this function
        self.getAS() if len(self.newIp)>0 else None
        #extract data from AsNumber.txt and generate required data format
        self.parseAS() if len(self.ipList)>0 else logging.warning("The ip list is empty, please check command output!!!")
        #write data into Json file
        self.outputFile() if len(self.asList)>0 else logging.warning("No AS number matches, please check ASnumber.txt file!!!")

    def cmdOutput(self):
        print("-> Traceroute from command, this may cost minutes.")
        logging.info("Input command 'traceroute -I {}'".format(self.ip))
        try:
            #AsNumber is a file which store the ip, ASnumber and service provider.
            f = open(self.currentDir+'/AsNumber.txt','r')
            currentIp  = f.readlines()
            f.close()
        except:
            currentIp = []
            logging.info("The ASnumber.txt file is empty, please check!")
        #run command by subprocess: traceroute -I xxx.xx.xx.xx
        self.result = subprocess.run(['traceroute','-I',self.ip], stdout=subprocess.PIPE)
        for i in self.result.stdout.decode("utf-8").split("\n")[1:]:
            if re.search("\d+\.\d+\.\d+\.\d+", i):
                #check if traceroute has multipath
                if len(re.findall("\d+\.\d+\.\d+\.\d+", i))>1:
                    print("This {} has mutilpath traceroute [{}], only the first one is selected".format(self.ip, re.findall("\d+\.\d+\.\d+\.\d+", i)))
                    logging.warning("This {} has mutilpath traceroute [{}], only the first one is selected".format(self.ip, re.findall("\d+\.\d+\.\d+\.\d+", i)))
                tempIP = re.search("\d+\.\d+\.\d+\.\d+",i)[0]
                self.ipList.append(tempIP)
                exist = False
                #check if ip info in AsNumber.txt
                for Ip in currentIp:
                    if tempIP == re.search("\d+\.\d+\.\d+\.\d+", Ip)[0]:
                        exist=True
                if not exist:
                    self.newIp.append(tempIP)
            if re.search('\d+\.\d+ms',i):
                rtt = re.findall('\d+\.\d+ms',i)
                self.rttList.append(rtt)

    def getAS(self):
        print("-> Call AS from ipApi")
        f = open(self.currentDir+'/AsNumber.txt','a')
        logging.info("Writting new AS number into AsNumber.txt")
        for ip in self.newIp:
            #request api by ip to get ASnumber and service provider
            data = requests.get("http://ip-api.com/line/" + ip).text
            #request fail for some special ip
            if 'fail' in data:
                f.write("{} fail,{}\n".format(ip,data.split("\n")[1]))
            else:
                rawAs = data.split("\n")
                try:
                    AS = rawAs[-3].split()[0]
                #some ip may lose ASnumber
                except:
                    AS = ""
                try:
                    org = rawAs[-5]
                #some ip may lose service provider
                except:
                    org = ""
                f.write("{} as:{} org:{}\n".format(ip,AS,org))
                logging.info("New ip:{} as:{} org:{} is writtin to ASnumber.txt\n".format(ip,AS,org))
        f.close()
        logging.info("New AS number input finished")

    def parseAS(self):
        print("-> Extract wanted data from AS list")
        f = open(self.currentDir+'/AsNumber.txt','r')
        currentIp = f.readlines()
        f.close()
        #get all ip info
        for reqIp in self.ipList:
            for currentip in currentIp:
                if reqIp == re.search("\d+\.\d+\.\d+\.\d+",currentip)[0]:
                    if currentip not in self.ipApi:
                            self.ipApi.append(currentip)
        #generate data format of fail call and success call
        for rawAs in self.ipApi:
            AS = None
            if 'fail' in rawAs:
                status = ' '.join(rawAs.split()[1:]).strip()
                ip = rawAs.split()[0].strip()
                AS = ""
                org = ""
                logging.info("{} has failed to get AS number".format(ip))
            else:
                status = "success"
                ip = rawAs.split()[0].strip()
                AS = rawAs.split()[1][3:].strip() if len(rawAs.split()[1])>3 else ""
                org = rawAs.split()[2][4:].strip() if len(rawAs.split()[2])>4 else ""
            #append to list for call by outputFile
            if rawAs:
                self.reqStatus.append(status)
                self.asList.append(AS)
                self.asProvider.append(org)
                self.asIp.append(ip)

    def outputFile(self):
        print("-> Wrting data into JSON file")
        hops = []
        for i in range(len(self.asList)):
            try:
                self.rttList[i][2]
            except:
            #some time the program will lose rtt3, just run the program one more time to solve the problem
                print("rtt3 is missing, Please run again")
                logging.warning("rtt3 is missing, please run again to get complete data!")
                self.rttList[i].append("")
            #output json format
            if ignore_ia:
                hops.append({
                    'IP address': self.asIp[i],
                    'rtt1': self.rttList[i][0],
                    'rtt2': self.rttList[i][1],
                    'rtt3': self.rttList[i][2],
                })
            elif ignore_is:
                hops.append({
                    'IP address': self.asIp[i],
                    'rtt1': self.rttList[i][0],
                    'rtt2': self.rttList[i][1],
                    'rtt3': self.rttList[i][2],
                    'Request AS': self.reqStatus[i],
                    'AS number': self.asList[i],
                })
            else:
                hops.append({
                    'IP address': self.asIp[i],
                    'rtt1':self.rttList[i][0],
                    'rtt2': self.rttList[i][1],
                    'rtt3': self.rttList[i][2],
                    'Request AS':self.reqStatus[i],
                    'AS number': self.asList[i],
                    'Service Provider': self.asProvider[i]
                })
        output = {
            'query': self.ip,
            'hops': hops
        }
        f = open(self.jsonFile, 'w')
        json.dump(output, f, indent=2)
        logging.info("Data processing finished. All data is writtin into file")


helpInterface = "\n{}\n\n" \
                "Usage: python3 traceroute.py [-o output-file] [-ia] [-is] target-name(>=1)\n\n" \
                "Options:\n" \
                "    -o output-file                Default: $host-name-$date.json. Only Json file is available.\n" \
                "    -ia                           Ignore AS number: Don't show AS number in the output file\n" \
                "    -is                           Ignore ServiceProvider: Don't show service provider\n" \
                "    -help                         show help interface\n" \
                "    target-name                   IP address or domain name. Available for multiple input\n\n" \
                "Example: python3 traceroute.py -o this-machine.json -ia -is 111.111.111.111 127.0.0.1\n" \
                "\n{}\n".format('='*120,'='*120)

if __name__ == '__main__':
    #example input : 209.58.184.100
    args = sys.argv
    filename=None
    ipList = []
    for arg in reversed(args):
        if re.search("\d+\.\d+\.\d+", arg):
            ipList.append(arg)
        else:
            break
    error= False
    if '-o' in args:
        index = args.index('-o')+1
        filename = args[index]
        if re.search("\.json",filename):
            pass
        else:
            error= True
            errorInfo = 'Please input a correct file name'
    ignore_ia = True if '-ia' in args else False
    ignore_is = True if '-is' in args else False
    if '-help' in args:
        print(helpInterface)
    elif not error:
        if len(ipList)<1:
            print("Error Input. Your Input: {}".format(args))
            print("Find instruction by: 'python traceroute.py -help'")
            logging.info("Wrong Input: {}\n".format(args))
        else:
            for ip in ipList:
                router = Router(ip,filename, ignore_ia,ignore_is)
                router.runTraceroute()
                print("-> Program Finished")
                logging.info("Program Done\n")
