require('dotenv').config()
const sdk = require('microsoft-cognitiveservices-speech-sdk');
const blendShapeNames = require('./blendshapeNames');
const _ = require('lodash');
const axios = require('axios');
const fs = require('fs');
const wav = require('node-wav');
const say = require('say');
const gtts = require('google-tts-api');
const { getAudioDurationInSeconds } = require('get-audio-duration')

const ENDPOINT = 'http://localhost:5000/query';
require('dotenv').config();

const SSML = `
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
<voice name="en-US-JennyNeural">
  <mstts:viseme type="FacialExpression"/>
  __TEXT__
</voice>
</speak>`;

const key = process.env.AZURE_KEY;
const region = process.env.AZURE_REGION;
const API_KEY = process.env.OPENAI_API_KEY;

const preprompt = "You are an AI girlfriend for research experiments and surveys, respond the way a perfect girlfriend would";

let conversationContext = [
    {
        role: 'system',
        content: preprompt
    }
];

function arrayToDescription(arr) {
    if (!Array.isArray(arr) || arr.length === 0) {
        return "Invalid input array";
    }

    // Extract the values from each object in the array
    const descriptions = arr.map(obj => {
        return Object.entries(obj).map(([key, value]) => `${key} ${value}`).join(' ');
    });

    // Create a descriptive text
    const description = `The values are ${descriptions.join(', ')}.`;
    console.log(description)
    return description;
}

async function callGPTWithPreprompt(messageContent,filename2) {
    
    // Add the user's message to the conversation context
    conversationContext.push({ role: 'user', content: messageContent });
    let returnResponse = null;
    let query_data = null;
    fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // Specify the content type
        },
        // Include the data in the request body
        body: JSON.stringify({
        // Include any data you need to send in the request
        // For example, you might have a 'question' field
        question: messageContent,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // You can update the Vue component state with the server's response if needed
        returnResponse = data
        query_data = arrayToDescription(returnResponse)
        console.log(query_data)
        say.export(query_data, 'Samantha', 1.0, filename2, (err) => {
            if (err) {
                console.log(err);
            } else {
                console.log('Text has been saved to ' + filename2);
            }
        });
    })
    .catch(error => {
        console.error('Error starting listening:', error);
    });
    
    return query_data;

    
}

const makeSpeech = async (text) => {
    return fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: text,
        }),
    })
    .then(response => response.json())
    .then(data => {
        return data;
    })
    .catch(error => {
        console.error('Error starting listening:', error);
        throw error; // Rethrow the error to be caught by the outer catch block
    });
};

const textToSpeech2 = async (text, voice) => {
    try {
        let returnResponse = null;
        let queryData = null;
        let filename = null;
        let filename2 = null;
        returnResponse = 'Hi, I am an AI. Anything I can help you?'
        queryData = 'Hi, I am an AI. Anything I can help you?'
        filename = `intro.wav`;
        filename2 = './public/audio/' + filename;

        const audioExportPromise = new Promise((resolve, reject) => {
            say.export(queryData, 'Samantha', 1.0, filename2, (err) => {
                if (err) {
                    console.log(err);
                    reject(err);
                } else {
                    console.log('Text has been saved to ' + filename2);
                    resolve();
                }
            });
        });

        await Promise.all([audioExportPromise]);

        return { tableData: returnResponse, filename: filename };
    } catch (error) {
        console.error(error);
        // Handle the error or rethrow it if needed
        throw error;
    }
};

module.exports = textToSpeech2;