 

Hping2 / Hping3 
To create an ACK packet:   
root@kali:~# hping3 -A 192.168.0.1
To Create SYN scan against different ports: 
root@kali:~# hping3 -8 1-600 –S 192.168.0.1 
To create a packet with FIN, URG, and PSH flags sets:
root@kali:~# hping3 -F -P -U 192.168.0.1

Advanced IP Scanner 
https://www.advanced-ip-scanner.com/download/

Angry IP Scanner 
https://angryip.org/download/#windows

masscan
root@kali:~# masscan -p 22,80,445 192.168.0.0/24 

Neet (Network Enumeration and Exploitation Tool)
1. git clone https://github.com/JonnyHightower/neet.git
2. cd neet
3. ./install.sh


CurrPorts
1. Run the application Currports and observe the processes. 
2. You can observe the process name, Protocol, Local and remote port and IP address 
information. 
3. Select any process, right click and Kill the process.

Colasoft Packet Builder    
https://www.colasoft.com/download/products/download_packet_builder.php
1. Add a new packet by clicking Add/button. Select the Packet type from the drop-down option. 
    Available options are: -  
    •  ARP Packet   
    •  IP Packet   
    •  TCP Packet   
    •  UDP Packet  
2. After Selecting the Packet Type, now you can customize the packet, Select the NetworkAdapter and Send it 
towards the destination. 

The Dude 
https://mikrotik.com/download/chr
Server: Ova file > virtualbox import > network adapter 1 set usb gbe > start vm
        user : admin, password:[blank] > yes > ip address print > dude set enable=yes

Network View
1. Open Network View
2. Enter map information and select start and end addresses 
3. Wait for Scan to Complete 
4. A map of the network is created  

LANState Pro 
https://www.10-strike.com/lanstate/download78.shtml
1. Click on create a new Map and select Scan IP Addresses click next.
2. Specify Address range and click next 
3. Specify scanning methods and parameters. 
4. The host search begins 
5. A Map of Local Area Network(LAN) will be created.