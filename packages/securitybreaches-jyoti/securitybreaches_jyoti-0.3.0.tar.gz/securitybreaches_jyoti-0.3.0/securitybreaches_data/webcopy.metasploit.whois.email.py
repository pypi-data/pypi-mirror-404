Website Copier Tool – HTTrack
Download and Install the WinHTTrack Website Copier Tool from the website 
http://www.httrack.com. 
1. Enter Project Name and click next 
2. Enter the target website URL and click on Set options 
3. Click on Scan Rules, select all checkboxes and Click ok
4. Click Next and Finish 
5. Click on Browse Mirrored Website to view the local copy of the target website 

Metasploit (for information gathering)
1. Open Kali Linux and Run Metasploit Framework.    
Execute the following commands: 
    db_status
    i. nmap -Pn -sS -T4 -sV --top-ports 100 -oX Test 10.10.50.0/24  
    ii. db_import Test 
    iii. hosts 
    iv. db_nmap -sS -A 10.10.50.2 
    v. services
    vi. msf6 > use scanner/smb/smb_version 
        msf6 auxiliary(scanner/smb/smb_version) > show options 
    vii. msf6 auxiliary(scanner/smb/smb_version) > set RHOSTS 
         10.10.50.1-11 
         RHOSTS => 10.10.50.1-11 
         msf6 auxiliary(scanner/smb/smb_version) > set THREADS 
         100 
         THREADS => 100 
         msf6 auxiliary(scanner/smb/smb_version) > show options 
    viii. run
    ix. hosts

Smart Whois  
Download software “SmartWhois” https://www.tamos.com/products/legacy for Whois lookup 
1. Type an IP address, hostname, or domain name in the address bar 
2. Query >  IP Address / Hostname Query results

eMailTracker Pro 
1. Open emailTracker. 
2. Check if there are any reports generated previously. 
3. Check for My trace Reports.
4. Click on Trace address, a new window will open.
5. Click on second option and enter email address you want to trace and click on trace button.
6. The eMailTracker will search for the location and information about the email address entered.
7. Now click on View report and the report will be generated in browser.