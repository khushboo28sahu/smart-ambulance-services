from time import time
from flask import Flask, request, jsonify, redirect, url_for
import requests, urllib, json, subprocess, os, time
import urllib.request
from flask import Flask, render_template
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread
from multiprocessing import Process
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# global variable's
Hospital = {}
Ambulance = {}
case_Accepted = {}
stream_req = {}
streams = {}
location = {}
global active


# --------------------  SERVER STATUS CHECK  --------------------------------------------------
def multiport_forward():
    subprocess.call("sudo python3 Receiver_ISC.py", shell=True)
    # subprocess.call("sudo ../../khushboo/bin/python Receiver_ISC.py", shell=True)


def gst():
    print("Gstreammer")
    # subprocess.call(['sh', './Gstreammer/GST_hls.sh'])
    # os.system('gst-launch-1.0 -v udpsrc port=4567 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000,encoding-name=(string)H264, payload=(int)96" ! rtpjitterbuffer latency = 0 ! rtph264depay ! decodebin ! videoconvert ! clockoverlay ! x264enc tune = zerolatency ! mpegtsmux ! hlssink playlist-root = http://10.3.53.16:9006 location=segment_%05d.ts target-duration=3 max-files=5')  # 5082 previos open port
    os.system(
        'gst-launch-1.0 -v udpsrc port=4567 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000,encoding-name=(string)H264, payload=(int)96" ! rtpjitterbuffer latency = 0 ! rtph264depay ! decodebin ! videoconvert ! clockoverlay ! x264enc tune = zerolatency ! mpegtsmux ! hlssink playlist-root = http://10.3.53.16:5082 location=segment_%05d.ts target-duration=3 max-files=5'
    )  # 5082 previos open port


""" SERVER STATUS"""


@app.get("/")
def status_req():
    return "200"


@app.route("/hospital")
def login():
    print("render template")
    return render_template("Login.html")


@app.route("/validate", methods=["POST"])
def validate():
    if request.method == "POST":
        print("validate")
        return redirect(url_for("hosp_information"))


@app.route("/hospital/information")
def hosp_information():
    return render_template("Info_Stream.html")


@app.route("/ambulance_stream")
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, **kwargs)


def run(server_class=HTTPServer, handler_class=Handler):
    # server_address = ('10.3.53.16',9006)    #'14.139.54.203'  port 5082
    server_address = ("10.3.53.16", 5082)  #'14.139.54.203'  port 5082
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


# ------------------------  AMBULANCE   ----------------------------------------------------------
""" Ambulance API's"""


@app.post("/ambulance/details")
def ambulance_handler():
    msg = json.loads(request.json)  # Getting msg
    print(msg)
    Ambulance.update(msg)
    Ambid = list(Ambulance.keys())[0]
    # check if the case is accepted
    if Ambid in case_Accepted:
        return case_Accepted
    else:
        return jsonify({"AMB01": {"HOSP01": {"Amb_status": " Hold on!!"}}})


""" Ambulance Stream Request API : Handle the stream request's"""


@app.post("/ambulance/stream_request")
def stream_request():
    print("Stream Request \n")
    req = json.loads(request.json)
    stream_req.update(req)
    print(stream_req)
    if bool(streams):
        amb_id = list(streams.keys())[0]
        hosp_id = list(streams[amb_id].keys())[0]
        if streams[amb_id][hosp_id]["stream"] == "start streaming":
            print({"AMB01": {"HOSP01": {"stream": "start streaming"}}})
            return jsonify({"AMB01": {"HOSP01": {"stream": "start streaming"}}})
    else:
        return jsonify({"AMB01": {"HOSP01": {"stream": " Dont start streaming"}}})


@app.post("/ambulance/start_stream")
def start_stream():
    stream = json.loads(request.json)
    print(stream)
    amb_id = list(stream.keys())[0]
    hosp_id = list(stream[amb_id].keys())[0]
    if stream[amb_id][hosp_id]["stream"] == "Video_Streaming":
        t3.start()
        t1.start()
        t2.start()
        return "Ok"


"""Location Updation"""


@app.post("/ambulance/location_update")
def ambulance_location():
    loc = json.loads(request.json)
    location.update(loc)
    # print(loc)
    return "OK"


# -----------------------  HOSPITAL  ----------------------------------------------------------

""" GET : Ambulance location """


@app.get("/hospital/send_location")
def get_ambulance_location():
    if bool(location):
        return location
    else:
        return jsonify({"Location": "Not Available"})


""" Hospital details API : Handles the Hospital information & Response back to hospital about the Ambulance"""


@app.post("/hospital/details")
def process_hosp():
    # print(request.json)
    hosp_info = request.json
    # hosp_info = json.loads(request.json)
    print(f"{hosp_info}\n")
    Hospital.update(hosp_info)
    key = list(Hospital.keys())[0]
    Ambu_list = {}
    if bool(Ambulance):
        amb_ID = list(Ambulance.keys())  # List of ambulance's
        Hosp_ID = list(Hospital.keys())  # List of Hospital's
        # Check if there is a case available for Hospital
        for i in amb_ID:
            i = list(Ambulance.keys())[0]
            if Ambulance[i]["Amb_status"] == "CASE_AVAILABLE":
                case = Ambulance[i]["case"]
                for j in Hosp_ID:
                    print("Inside the hospital detail \n\n")
                    speciality = list(Hospital[j]["doctors"].keys())
                    print(speciality)
                    if case in speciality:
                        print(case)
                        print("\n\n")
                        Ambu_list[i] = Ambulance[i]
                        print("sending Ambulance Information!")
                return Ambu_list
    else:
        # print("Sending the response!!!")
        return jsonify({key: {"Amb_status": "No Case Available"}})


""" Case_accepted API : It will handle the hospitals case information and response back with the STREAM AVAIlable msg"""


@app.post("/hospital/case_accepted")
def Case_Accepted():
    case_msg = request.json
    # case_msg = json.loads(request.json)
    print(case_msg)
    amb_id = list(case_msg.keys())[0]
    hosp_id = list(case_msg[amb_id].keys())[0]
    # store th case accepted msg
    if amb_id in list(Ambulance.keys()):
        case_Accepted[amb_id] = case_msg[amb_id]
    # Check if the stream is available or not
    if bool(stream_req):
        if stream_req[amb_id][hosp_id]["stream"] == "Stream_Available":
            return jsonify({amb_id: {hosp_id: {"stream": "Stream_Available"}}})
    else:
        return jsonify({amb_id: {hosp_id: {"stream": "No_Stream_Available"}}})


"""Hospital Start stream : Handle the start stream request"""


@app.post("/hospital/Send_Stream")
def Start_streaming():
    start_stream = request.json
    amb_id = list(start_stream.keys())[0]
    hosp_id = list(start_stream[amb_id].keys())[0]
    streams[amb_id] = start_stream[amb_id]
    print(streams)
    time.sleep(2)
    return jsonify(
        {amb_id: {hosp_id: {"stream": "http://10.3.53.16:5082"}}}
    )  # 14.139.54.203


if __name__ == "__main__":
    t1 = Process(target=gst)
    t2 = Process(target=run)
    t3 = Process(target=multiport_forward)
    # app.run(host="10.3.53.16", port ="9005", debug =True,threaded=True)
    app.run(host="10.3.53.16", port="5076", debug=True, threaded=True)  # 5076
    t1.join()
    t2.join()
    t3.join()

"""
PUBLIC IP : "http://14.139.54.203:5076"        
Open Port range : 5076 - 5082
"""
