A) Recon-ng 
recon-ng
marketplace search
marketplace install hackertarget
modules load hackertarget 
options set SOURCE tesla.com
info
input
run
show hosts
back

B) FOCA Tool 
1- Download the software FOCA from https://www.elevenpaths.com. Now,Go to  
2- Now, Enter the Project Name, Domain Website, Alternate Website (if required),Directory to save the results, Project Date. Click Create to proceed. 
3- Select the Search Engines, Extensions, and other parameters as required. Click on Search All Button. 
4- Once Search completes, the search box shows multiple files. You can select the file, download it, Extract Metadata, and gather other information like username, creation date, and Modification.   

C) Windows Command Line Utilities
Ping
1. Open Windows Command Line from windows pc
2. Enter the command “ping google.com” to ping 
3. From the output, you can observe and extract the following information: 
    • google.com is live 
    • IP address of google.com 
    • Round Trip Time 
    • TTL value 
    • Packet loss statistics
4. Now, enter the command for maximum transmission unit (MTU), “ping google.com –f -l 1200” to check the value of fragmentation. 

Tracert
1. Enter the command “ tracert google.com” to trace the target.

Tracert using Ping 
ping google.com -l 1200 -n 1 -f

NsLookup
1. Go to Windows command line (CMD) and enter Nslookup and press Enter.  
2. Command prompt will proceed to " > " symbol.  
3. Enter "server <DNS Server Name>" or "server <DNS Server Address> ".   
4. Enter "set type=any" and press Enter. It will retrieve all records from a DNS server, We can set the query type as A, ANY, CNAME, MX, NS, PTR, SOA, SRV.   
5.Enter "ls -d google.com" this will display the information from the target domain (if allowed). 
