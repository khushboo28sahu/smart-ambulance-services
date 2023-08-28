function streaming(){
    console.log(stream_response);
    return stream_response;
}

function stream_update(value){
    Document.getElementById("stream").innerHTML = value;
    // console.log(value)
}

var stream_response = Document.getElementbyname("response").value;
console.log(stream_response);
export {streaming};