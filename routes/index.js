var express = require('express');
var router = express.Router();
var textToSpeech = require('../helpers/tts');
const { getAudioDurationInSeconds } = require('get-audio-duration')

/* GET home page. */
router.post('/talk', async function(req, res, next) {
  try {
    const result = await textToSpeech(req.body.text, req.body.voice);
    const filename = result.filename
    const filename2 = './public/audio/' + result.filename
    const duration = await getAudioDurationInSeconds(filename2); // Await the duration promise
    console.log(duration);

    const timeStep = 1 / 60;
    let time = 0;
    const blendData = [];

    while (time <= duration) {
      // Generate blend shape values based on the talking animation
      const mouthOpenValue = Math.sin(6 * Math.PI * time / duration) * 0.5;
      const scaleFactor = 0.2;
      const jawOpenValue =
        scaleFactor * (Math.abs(Math.sin(6 * Math.PI * time / duration)) + 1) / 2;

      // Add the blendData entry for the current time
      blendData.push({
        time: time,
        blendshapes: {
          mouthOpen: mouthOpenValue,
          jawOpen: jawOpenValue,
          // Add other blend shape names and values as needed
        },
      });

      time += timeStep;
    }

    const result1 = {
      blendData,
      filename: filename,
      tableData: result && result.tableData ? result.tableData : [],
    };

    console.log(result1);
    res.json(result1); // Send result1 as a JSON response
  } catch (err) {
    console.error(err);
    res.json({}); // Send an empty response in case of an error
  }
});


module.exports = router;
