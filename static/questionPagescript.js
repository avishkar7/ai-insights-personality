'use strict';

/* globals MediaRecorder */

let mediaRecorder;
let recordedBlobs;
let count = 1;
const que = ['Question: What are the qualities which you believe describe you the best?']
const questions = ['Question 1: Tell us something about yourself', 'Question 2: What is the most stressful situation you have encountered at work?', 'Question 3: What is your ideal workspace?']
const errorMsgElement = document.querySelector('span#errorMsg');
const recordedVideo = document.querySelector('video#recorded');
const recordButton = document.querySelector('button#record');
const downloadButton = document.querySelector('button#download');
const nextButton = document.getElementById('next');
const facts = ['Please wait till we save your responses.']
const time = [];


document.querySelector('button#start').addEventListener('click', async () => {// start button to trigger camera
  const hasEchoCancellation = document.querySelector('#echoCancellation').checked;
  const hasnoiseSuppression = document.querySelector('#noiseSuppression').checked;
  const hasAutoGainControl = document.querySelector('#autogaincontrol').checked;
  console.log(hasEchoCancellation);
  console.log(hasnoiseSuppression);
  console.log(hasAutoGainControl);
  document.querySelector('button#start').style.display = 'none';
  const constraints = {
    audio: {
      echoCancellation: { exact: hasEchoCancellation },
      autoGainControl:{ exact:hasAutoGainControl },
      noiseSupperssion:{ exact:hasnoiseSuppression }
    },
    video: {
      width: 1280, height: 720
    }
  };
  console.log('Using media constraints:', constraints);
  await init(constraints);
});

async function init(constraints) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    handleSuccess(stream);
  } catch (e) {
    console.error('navigator.getUserMedia error:', e);
    errorMsgElement.innerHTML = `navigator.getUserMedia error:${e.toString()}`;
  }
}

function handleSuccess(stream) {// set video stream to video tag
  recordButton.disabled = false;
  console.log('getUserMedia() got stream:', stream);
  window.stream = stream

  const gumVideo = document.querySelector('video#gum');
  gumVideo.srcObject = stream;
}

recordButton.addEventListener('click', () => {// to start the camera for recording
  if (recordButton.textContent === 'Record') {
    time.push(Date());
    console.log(time);
    startRecording();
  } else {
    stopRecording();
    time.push(Date());
    recordButton.textContent = "Record";
    downloadButton.disabled=false
  }
}); 

function startRecording() {// start camera
  showNextBtn();
  //document.getElementById('question').innerText = que[0];   //for single question
  document.getElementById('question').innerText = questions[0];  //for multiple questions
  recordedBlobs = [];
  //let options = { mimeType: 'video/webm;codecs=vp9,opus',audioBitsPerSecond:128000,videoBitsPerSecond:2500000 };
  let options = { mimeType: 'video/webm;codecs=vp9,opus' };
  try {
    mediaRecorder = new MediaRecorder(window.stream, options);
  } catch (e) {
    console.error('Exception while creating MediaRecorder:', e);
    errorMsgElement.innerHTML = `Exception while creating MediaRecorder: ${JSON.stringify(e)}`;
    return;
  }
  console.log('Created MediaRecorder', mediaRecorder, 'with options', options);
  recordButton.textContent = "Stop Recording";
  downloadButton.disabled = true;
  mediaRecorder.onstop = (event) => {
    console.log('Recorder stopped: ', event);
    console.log('Recorded Blobs: ', recordedBlobs);
  };
  
  mediaRecorder.ondataavailable = handleDataAvailable;
  mediaRecorder.start();
  console.log('MediaRecorder started', mediaRecorder);
}

function stopRecording() {// stop recording answered question
  mediaRecorder.stop();
  recordButton.style.display = 'none';
  const gumVideo = document.querySelector('video#gum');
}

function showNextBtn() {
  document.getElementById('next').style.display = 'block';
  document.getElementById('question').innerText = questions[0];
  recordButton.disabled = true;
}

nextButton.addEventListener('click', () => {//Button for next question to be asked
  if (count <= questions.length - 1) {
    document.getElementById('question').innerText = questions[count];
    time.push(Date());
    count++;
    mediaRecorder.stop();
    mediaRecorder.start();
  } else {
    recordButton.disabled = false;
    time.push(Date());
    nextButton.style.display = 'none';
    document.getElementById('question').style.display = 'none';
    count = 1;
    mediaRecorder.stop();
    mediaRecorder.start();
  }
})

function handleDataAvailable(event) {// push data to blob or video data
  console.log('handleDataAvailable', event);
  if (event.data && event.data.size > 0) {
    recordedBlobs.push(event.data);
  }
}

downloadButton.addEventListener('click', () => {// send data to server
  downloadButton.disabled = true;
  document.getElementById('facts').innerText = facts[0]; 
  //alert("Please wait while we save your responses.") 
  var data = new FormData();
  recordedBlobs.forEach((blob,index) => {
    const arr=[];
    arr.push(blob);
    if(index<3){
      const blobdata=new Blob(arr,{type:'video/webm'});
      data.append(`question${index+1}`,blobdata);
    }
  });
  const url1 = `/recorded`;
  fetch(`${window.origin}/analysis`, {
    method: 'POST',
    body: data
  })
    .then(response => {
      console.log(response);
      return response.text()
    })
    .then(data => {
      console.log(data)
      console.log(time);
      if (data === 'success') {
        const a = document.createElement('a');
        a.style.display = 'none';
        a.target = '_self';
        a.href = url1;
        document.body.appendChild(a);
        a.click();
      }
      else {
        alert("Cannot post");
        alert("Please retry interviewing again.")
      }
    })
}); 

/*
downloadButton.addEventListener('click', () => {// send data to server 
  var data = new FormData();
  recordedBlobs.forEach((blob,index) => {
    const arr=[];
    arr.push(blob);
    if(index<3){
      const blobdata=new Blob(arr,{type:'video/webm'});
      data.append(`question${index+1}`,blobdata);
    }
  });
  
  const url1 = `/recorded`;
  fetch(`${window.origin}/analysis`, {
    method: 'POST',
    body: data
  })
    .then(response => {
      console.log(response);
      return response.text()
    })
    .then(data => {
      console.log(data)
      console.log(time);
      if (data === 'success') {
        const a = document.createElement('a');
        a.style.display = 'none';
        a.target = '_self';
        a.href = url1;
        document.body.appendChild(a);
        a.click();
      }
      else {
        alert("can't post");
      }
    })
});


function stopRecording() {// stop recording answered question
  console.log('iniside stop');
  console.log(userStream);
  mediaRecorder.stop();
  recordButton.style.display = 'none';
  const gumVideo = document.querySelector('video#gum');
  userStream.getTracks()[0].enabled=false;
  userStream.getTracks()[1].enabled=false;
  // console.log(userStream);
  // delete userStream.getTracks()[0];
  // delete userStream.getTracks()[1];

  // gumVideo.pause();
  // gumVideo.src='';
  // gumVideo.style.display='none';

} 
*/