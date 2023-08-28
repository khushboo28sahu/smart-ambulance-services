import PySimpleGUI as sg
import requests
import json
import time
import subprocess
from threading import Thread
import threading

# from flask_server import ambulance_location
from multiprocessing import Process
import os

# from cameraChk import camTest

# import gps
# URL = 'http://127.0.0.1:5000'
# URL = 'http://10.1.11.8:8001'
URL = "http://14.139.54.203:5076"
# URL = 'http://10.3.32.146:8001'
# URL = 'http://10.3.53.16:9005'

hospRes = {}
ambinfo = {}
location = [21.0, 81.0]
# Ambulance_capability
amb_cap = [
    "eeg",
    "ecg",
    "emg",
]
strm_sts = "no"
submit_flag = 0
stream_flag = 0
stop = False
window = 0
values = 0
exit_sending = 0
case_accepted = 0
print("Ambulance")


################### Back end #####################################
def info():
    print("Inside info")
    while True:
        print(ambinfo)
        time.sleep(5)
        if bool(ambinfo):
            sendAmbInfo()
            break


def sendAmbInfo():
    global hospRes
    print(ambinfo)
    # print("Sending Ambulance info, \n {payload} \t to server".format(payload = ambinfo))
    r = requests.post(URL + "/ambulance/details", json=json.dumps(ambinfo))
    hospRes = json.loads(r.text)  # Response
    print(hospRes)
    amb_id = list(ambinfo.keys())[0]
    hosp_id = list(hospRes[amb_id].keys())[0]  # From the server response
    if hospRes[amb_id][hosp_id]["Amb_status"] == "CASE ACCEPTED":
        global case_accepted
        case_accepted = 1
        t2.start()
        requestStream(hospRes)
        time.sleep(3)
    else:
        time.sleep(3)
        sendAmbInfo()


# Comment below when using RPi
def sendLocation():
    global exit_sending
    while exit_sending == 0:
        # Update Location
        amb_id = list(ambinfo.keys())[0]
        amb_loc = json.dumps({amb_id: location})
        time.sleep(5)


# When using RPi, uncomment below and comment above:

# def sendLocation():
#     global exit_sending
#     while exit_sending==0:
#         # Update Location
#         try:
#             location = location_data()
#             amb_id = list(ambinfo.keys())[0]
#             amb_loc = json.dumps({amb_id:location})
#         except:
#             pass
#         print(location)
#         time.sleep(5)


def requestStream(hospRes):
    global strm_sts
    print("Inside Request Stream")
    amb_id = list(ambinfo.keys())[0]
    hosp_id = list(hospRes[amb_id].keys())[0]
    hospRes[amb_id][hosp_id]["stream"] = "Stream_Available"
    print(hospRes)
    r = json.loads(
        (
            requests.post(URL + "/ambulance/stream_request", json=json.dumps(hospRes))
        ).text
    )
    print(f"Hospital response is : \n{r}\n")
    stream_status = r[amb_id][hosp_id]["stream"]
    if stream_status == "start streaming":
        global strm_sts, event
        strm_sts = "yes"
        print("stream status flag", strm_sts)
        # window['-STREAM-'].update(disabled=False, button_color='green')
        # print(event,values)
        # if event == 'Start Streaming':
        #     t=Thread(target=startStream)
        #     t.start()
        #     t.join()
    else:
        time.sleep(3)
        requestStream(hospRes)


def run_Rpi2():
    print("Calling Rpi_2")
    subprocess.call(["sh", "./Rpi2.sh"])


def run_Rpi1():
    print("Calling Rpi_1")
    subprocess.call(["sh", "./Rp1.sh"])


def startStream():
    amb_id = list(ambinfo.keys())[0]
    hosp_id = list(hospRes[amb_id].keys())[0]
    r_stream = requests.post(
        URL + "/ambulance/start_stream",
        json=json.dumps({amb_id: {hosp_id: {"stream": "Video_Streaming"}}}),
    ).text
    print(r_stream)
    # subprocess.call(['sh', './gst.sh'])
    ts1 = Thread(target=run_Rpi2)
    ts2 = Thread(target=run_Rpi1)
    ts1.start()
    ts2.start()
    ts1.join()
    ts2.join()
    # os.system('gst-launch-1.0 v4l2src device="/dev/video0" ! videoconvert ! clockoverlay ! autovideosink')


###################### FRONT END GUI ####################################
def server_status():
    a = requests.get(URL).status_code
    if a == 200:
        return "UP"
    else:
        return "DOWN"


def gps_status():
    return "DOWN"


# def camera_status():
#     return 'DOWN'


def network_status():
    return "DOWN"


initialization = {
    "server": server_status(),
    "gps": gps_status(),
    "camera": "DOWN",  # camTest(),
    "Network": network_status(),
}


def create_window():
    global strm_sts
    # Add some color to the window
    sg.theme("DarkTeal9")
    global strm_sts
    layout = [
        [sg.Text("Please fill out the following fields:")],
        [
            sg.Text("Emergency: "),
            sg.Combo(["High", "Low"], enable_events=True, key="-EMERGENCY-"),
        ],
        [
            sg.Text("Case: "),
            sg.Combo(
                ["Ortho", "Cardio", "Opthalmo", "Respiratory", "Gastro"],
                enable_events=True,
                key="-CASE-",
            ),
        ],
        [
            sg.Text("Server:{}".format(initialization["server"])),
        ],
        [sg.Text("GPS:{}".format(initialization["gps"]), key="-GPS-")],
        [sg.Text("Camera:{}".format(initialization["camera"]), key="-CAMERA-")],
        [sg.Text("Network:{}".format(initialization["Network"]), key="-NETWORK-")],
        [
            sg.Submit(disabled=True, button_color="red"),
            sg.Button("Clear"),
            sg.Button("Reset"),
        ],
        # [sg.Text('Case Accepted: {}'.format((lambda c : 'YES' if case_accepted==1 else 'NO')(case_accepted)), key='-CASEAC-')]
        # [sg.Text('Streaming Status:{}'.format((lambda ss : 'Available' if strm_sts == 'yes' else 'NA')(strm_sts)))],
        # [sg.Button('Start Streaming',
        #     button_color='{}'.format((lambda clr : 'green' if strm_sts == 'yes' else 'red')(strm_sts)),
        #     disabled = (lambda bl : False if strm_sts == 'yes' else True)(strm_sts),)],
        [sg.Button("Check Stream", key="-CHKSTRM-")],
        [
            sg.Button(
                "Start Streaming", key="-STREAM-", disabled=True, button_color="red"
            )
        ],
    ]
    return sg.Window("AMBULANCE DASHBOARD", layout, size=(640, 480))


def clear_input():
    for key in values:
        window[key]("")
    return None


if __name__ == "__main__":
    t1 = Thread(target=info, daemon=True)
    t2 = Thread(target=sendLocation, daemon=True)
    t1.start()
    # info()
    # global window, values,ambinfo, event
    window = create_window()
    while True:
        print("INSIDE WHILE")
        print("STREAM STATUS UPDATE: ", strm_sts)
        event, values = window.read()
        print("event,value:", event, values)
        if len(values["-EMERGENCY-"]) != 0 and len(values["-CASE-"]) != 0:
            window["Submit"].update(disabled=False, button_color="green")
            window.refresh()
        if event == "Reset":
            # global exit_sending
            exit_sending = 1
            window.close()
            window = create_window()
        if event == sg.WIN_CLOSED:
            break
        if event == "Clear":
            # global exit_sending
            exit_sending = 1
            clear_input()
            window["Submit"].update(disabled=True, button_color="red")

        if event == "Submit":
            print("Information Submitted")
            ambinfo = {
                "AMB01": {
                    "Amb_status": "CASE_AVAILABLE",
                    "ambulance_capability": amb_cap,
                    "case": values["-CASE-"],
                    "emergency": values["-EMERGENCY-"],
                    "location": location,
                    # menu
                }
            }
            # time.sleep(5)
            window.refresh()
        # window['-CASEAC-'].update('')

        print(strm_sts)
        print("\n", event)

        # if strm_sts == 'yes':
        #     print("StrmbuttonHere")
        #     window['-STREAM-'].update(disabled=False, button_color='green')
        #     print(event, values)
        if event == "-CHKSTRM-":
            if strm_sts == "yes":
                window["-STREAM-"].update(disabled=False, button_color="green")
        # window.refresh()
        # if strm_sts == 'yes':
        #     window['-STREAM-'].update(disabled=False, button_color='green')
        if event == "-STREAM-":
            ts = Thread(target=startStream, daemon=True)
            ts.start()
            ts.join()
            # break

        window.refresh()

    # time.sleep(2)
    window.close()
    t1.join()
    t2.join()
