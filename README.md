# HOW TO INSTALL & USE

>## A. CLONE THE REPO  

 >> 1. git clone https://github.com/ftruvian/spudsense_full.git
 >> 2. cd spudsense_full  
    
>## B. SETUP PYTHON ENVIRONMENT  

 >> 1. python3 -m venv .
 >> 2. source bin/activate
    
>## C. INSTALL PYTHON DEPENDENCIES  

 >> 1. pip3 install pyserial  

>## D. ARDUINO INTEGRATION

 >> 1. Connect ung arduino sa computer tas check kung nagpakita na ung ttyUSB0 sa linux or di ko alam sa windows
 >> 2. Open mo arduino ide tas iopen mo ung getDataIR folder tas ung .ino file sa loob nun.
 >> 3. Iflash mo un sa arduino
 >> 4. Ung sa wiring lahat nakalagay sa Analog pins lahat wag isolder kasi pangkuha lang yan ng data
 >> 5. Ayusin nlng ung code depende sa kung anong pin nakalagay 

>## E. PYTHON
 
 >> 1. kung ok na punta ka sa datacollect.py tas ilagay mo dun sa taas ung nagpakita sa step 1 kung ttyUSB0, ttyUSB1 etc.
 >> 2. save mo
 >> 3. python datacollect.py tas check mo kung may nagappear na .csv file doon
 >> 4. Kung may errors send mo sakin ung error message
