#!/bin/bash

#sshpass -vvv -p raspberry ssh pi@169.254.219.242

#sudo kill -9 $(ps aux | grep python | awk '{print $2}')  &&

sshpass -p 'imprint' ssh -o StrictHostKeyChecking=no -t imprint@169.254.219.242  'sudo python3 Slave_RPI/RPi2_Tx_streaming.py'

#sshpass -p 'raspberry' ssh -o StrictHostKeyChecking=no -t pi@169.254.30.193  'sudo python3 RPi2_Tx_streaming.py'
