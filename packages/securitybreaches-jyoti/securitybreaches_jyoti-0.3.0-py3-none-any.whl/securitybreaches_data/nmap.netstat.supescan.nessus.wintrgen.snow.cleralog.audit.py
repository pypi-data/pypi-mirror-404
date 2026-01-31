nmap target_ip   defaultbscan top 1000/ nmap -p 80 target_ip  - scann specidfic port / 
nmap -F target_ip -gast scann commands ports  /
nmap -O target_ip - os detection  / 
nmap -A target_ip - enable os detect . version detection

netstat -a  ,-o,-p,-s,-n
netstat /? - give list ofcoamnds 


Prac 4
Perform Enumeration using the following tools:

Nmap
nmap -O 198.164.0.1

NetBIOS Enumeration Tool
netstat -a

SuperScan

Hyena
https://www.systemtools.com/hyena/download.htm

SoftPerfect Network Scanner Tool  
https://www.softperfect.com/products/networkscanner/

OpUtils
https://www.manageengine.com/products/oputils/download-free.html
localhost:8060 > login(user: admin, password: admin) > oberve the screen (Dashboard, ipaddress manager, etc.)

Wireshark testphp.vulnweb.com
https://www.wireshark.org/#download
open wireshark > click ethernet > minimize and search http websites(https://info.cern.ch/) > Apply filter http > click on any packet > follow > http stream, view all details about packet.

Nessus
http://localhost:8834 > My scans > create a new scan > Enter filename, description, foldertosave, targets > Targets : 192.168.0.1 > Save
> check hosts, vulnerabilities, history in foldertosave (it will show critical, high, medium, low, info vulnerabilities levels)

Winrtgen
1. To generate rainbow tables first we will have to modify the properties of WinRTGen accordingto our need, and to do so Click on “Add Table“. After this, a new box will appear named “Rainbow Table Properties” 
2. In the “Rainbow Table Properties” window we have the option to modify settings in order togenerate rainbow tables according to our needs.
3. After assigning the values to the properties according to our needs click on “Benchmarks”. Thiswill show the estimated time, Hash speed, Step speed, Table Pre-computing time, etc. that will be required to generate the Rainbow Table according to assigned properties
4. After “Benchmark” click on “Ok”. This will add the Rainbow Table to the queue in the main 
window of WinRTGen
5. After this click on “Rainbow Table” You want to start processing and click “OK”. 
6. After clicking on ‘OK’ the WinRTGen” will start generating a rainbow table. This table will be saved to your WinRTGen Directory. 

PWDump
cd pwdump.exc in cmd > paste the passwords.txt > open passwords.txt it will get encrypted.

Ophcrack
Step 1: Since we are assuming that your Windows PC is locked and you do not know the 
password, the first step needs to be carried out on a different PC with internet access and 
administrator privileges.    
Step 2: Download the correct version of Ophcrack Live CD from the official website to the 
second PC.   
Step 3: Burn the ISO file to a USB or CD. To do this, you will need an ISO burning 
application. Now proceed to the next step of the password reset process.   
Step 4: Remove the bootable media from the second PC and insert it into your locked 
Windows machine. Let the computer boot up from this media instead of the native Windows 
installation. This is made possible by the fact that Ophcrack itself contains a small operating 
system that can run independently of your Windows OS. In a few moments, you will see the 
Ophcrack interface on your computer.   
Step 5: You will now see a menu with 4 options. Leave it on the default option, which is 
automatic. After a few seconds, you will see the Ophcrack Live CD loading and then the disk 
partition information being displayed as Ophcrack identifies the one with the SAM file.   
Step 6: Once the process has been complete, you will see a window with several user accounts 
and their passwords displayed in column format. Against the previously locked username, look 
for an entry in the NT Pwd column.    
Step 7: This will be your recovered password, so note it down. You can now remove the Live 
CD from the drive and restart your computer. You will be able to login to your user account 
using the password that was recovered by Ophcrack.

Flexispy
FlexiSPY is a phone application which comes with an android keylogger for the phone as a feature. It will help you record phone calls, capture SMS, WhatsApp messages, even capture keystrokes,allow you to read 
emails, read Facebook messages. 

ADS Spy   

Snow
1.Navigate to the directory where the SNOW tool is installed.   
2. Create a new text file named:bank_details.txt with data  
 go to cmd  and location of snow .cd C:\snow
3.snow -C -m "text to be hide" -p "password" bank_details.txt hidden.txt 
4. The source file is a bank_details.txt file as shown above. Destination file will be the exact copy 
of source file containing hidden information.  
5. Go to the directory; you will a new file hidden.txt, Open the File.

Quickstego
1. Open QuickStego Application   
2. Upload an Image. This Image is term as Cover, as it will hide the text.   
3. Enter the Text or Upload Text File   
4. Click Hide Text Button   
5. Save Image This Saved Image containing Hidden information is termed as Stego Object. 
Recovering Data from Image Steganography using QuickStego 
1. Open QuickStego →Click Open Image and open the image generated by quickstego(Stego 
Picture.bmp)
2. Click Get Text to extract hidden text 

Clearing Audit Policies   
1. C:\Windows\system32> auditpol /?   
2. auditpol /set /category:"System","Account logon"/success:enable /failure:enable 
3. To check Auditing is enabled, enter the command:  
   C:\WINDOWS\system32>auditpol /get /category:"Account Logon","System"
4. Clear audit pol 
   C:\WINDOWS\system32>auditpol /clear
5. To check auditing enter the command 
   C:\WINDOWS\system32>auditpol /get /category:"Account logon","System"

Clearing Logs
1. Go to Kali Linux Machine  → Open File System 
2. Open the /var directory: 
3. Go to Logs folder: 
4. Select any log file → Open it