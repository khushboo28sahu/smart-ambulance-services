// import { streaming, stream_update} from "./stream.js";
var xhttp = new XMLHttpRequest();
var url = "http://10.3.53.16:5076"
// "http://14.139.54.203:5076" 

var doctors = {};
var Ambulance = {};
var Hosp_info = {};
var Ambulance_case_accept = {};
var ambdata;
var Hosp_Id; 
var stream_request = {};
var start_streming={};
var streaming_URL;
function stream(){
    location.href = streaming_URL;
}
function Post_start_streaming(){
    var amb_id = Object.entries(stream_request)[0][0];
    start_streming[amb_id] = {};
    start_streming[amb_id][Hosp_Id]={};
    start_streming[amb_id][Hosp_Id]["stream"] = "start streaming";
    console.log(start_streming)
    // stream[AmbId] = { hosp_id: { "stream" : "start streaming"}} 
    xhttp.open("POST", url+"/hospital/Send_Stream", false);
    xhttp.setRequestHeader("Accept", "application/json");
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send(JSON.stringify(start_streming));
    xhttp.onload;
    var res = xhttp.responseText;
    console.log(res);
    let url_response = JSON.parse(res);
    streaming_URL = url_response[amb_id][Hosp_Id]["stream"];
    let text = "<button id=\"streamurl\" onclick=\"stream()\">Stream</button>";
    document.getElementById("streaming").innerHTML = text;
}

function Post_case_Accepted(){
    console.log("post case accepted!!");
    let amb_id = (Object.entries(Ambulance))[0][0];
    console.log(amb_id);

    var data = Object.entries((Object.entries(Ambulance))[0][1]);
    console.log(data);

    var amb_case = data[2][1];
    console.log(doctors[amb_case]);

    Ambulance_case_accept[amb_id] = {};
    Ambulance_case_accept[amb_id][Hosp_Id] = {};
    Ambulance_case_accept[amb_id][Hosp_Id]["Amb_status"] = "CASE ACCEPTED";
    Ambulance_case_accept[amb_id][Hosp_Id][amb_case] = doctors[amb_case];
    console.log(Ambulance_case_accept);

    while(1){
        var check=0;
        xhttp.open("POST", url+"/hospital/case_accepted", false);
        xhttp.setRequestHeader("Accept", "application/json");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify(Ambulance_case_accept));
        xhttp.onload;
        var res = xhttp.responseText;
        console.log(res);

        stream_request = JSON.parse(res);
        // let key = (Object.keys(Ambulance))[0];
      
        if (stream_request[amb_id][Hosp_Id]["stream"] == "Stream_Available"){

            var stream = Object.entries(stream_request);
            let amb_id= stream[0][0];
           
            let text = "<table border='1'>"
            text +="<h2><b>"+"Stream Available";
            text += "<tr>"+"<td>"+"Ambulance Id"+"</td>"+"<td>"+Hosp_Id+"</td>"+
                    "<td>"+"stream"+"</td>"+"<td>"+"Do you like to Stream?"+
                    "</td>"+"</tr>";

            text += "<tr>"+"<td>"+amb_id+"</td>"+"<td>"+Hosp_Id+"</td>"+
                    "<td>"+stream_request[amb_id][Hosp_Id]['stream']+
                    "</td>"+"<td> <input type=\"checkbox\" onclick=\"Post_start_streaming() \"> </td>"+"</tr>";

            text += "</table>"
            check =1;
            document.getElementById("streaming").innerHTML = text;
                       
        }else
        {
            check = 0;
            document.getElementById("streaming").innerHTML =res;
            
        }
        if (check == 1){
            break;
        }
        
    }
   
}

function Post_Hospital_Info(){
    var result = 0;
    Hosp_info[Hosp_Id] = {"status" : Hosp_status, "doctors" : doctors }
    
    while(1){ 
        xhttp.open("POST", url+"/hospital/details", false);
        xhttp.setRequestHeader("Accept", "application/json");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify(Hosp_info));
        xhttp.onload;
        var res = xhttp.responseText;

        console.log(res);
        Ambulance = JSON.parse(res);
        let key = (Object.keys(Ambulance))[0];

        if(Ambulance[key]["Amb_status"] == "CASE_AVAILABLE" )
        {   
            let ambid = Object.entries(Ambulance);
            let ambdata = Object.entries(ambid[0][1]);
            amb_status = ambdata[0][0];
            let ambulance_capability = ambdata[1][0];
            let case_info = ambdata[2][0];
            let emergency = ambdata[3][0];
            let location = ambdata[4][0];

            let text = "<table border='1'>"
            text+="<h2><b>"+"Ambulance case Information";
            text += "<tr>"+"<td>"+"Ambulance ID"+"</td>"+"<td>"+amb_status+"</td>"+ 
                    "<td>"+ambulance_capability+"</td>"+"<td>"+case_info+"</td>"+
                    "<td>"+emergency +"</td>"+"<td>"+location+"</td>"+
                    "<td>"+"CheckBox"+"</td>"+"</tr>";

            text += "<tr>"+"<td>"+ambid[0][0]+"</td>"+"<td>"+ambdata[0][1]+"</td>"+
                    "<td>"+ambdata[1][1]+"</td>"+"<td>"+ambdata[2][1]+"</td>"+
                    "<td>"+ambdata[3][1]+"</td>"+"<td>"+ambdata[4][1]+"</td>"+
                    "<td> <input type=\"checkbox\" onclick=\"Post_case_Accepted() \"> </td>"+"</tr>";

            text += "</table>"
            result = 1;
            document.getElementById("demo").innerHTML = text;
        
        } else 
        {
            result=0;
            document.getElementById("demo").innerHTML = res;  
            
        }   

        if (result == 1){
            break;
        }    
    }
   
} 

// HospitalID
var Hosp_select = document.getElementById("Hospital_List")
var Hosp_Id = Hosp_select.options[Hosp_select.selectedIndex].value;

// Status
var Hosp_status = (document.getElementById("status")).options[document.getElementById("status").selectedIndex].value;

// Doctors list
doctors['Ortho'] = document.getElementById("Ortho").value;
doctors['Cardio'] = document.getElementById("Cardio").value
doctors['Opthalmo'] = document.getElementById("Opthalmo").value;
doctors['Neuro'] = document.getElementById("neuro").value;
document.getElementById("submit").addEventListener("click", Post_Hospital_Info);

