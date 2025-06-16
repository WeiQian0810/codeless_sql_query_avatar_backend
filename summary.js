const say = require('say');
const { getAudioDurationInSeconds } = require('get-audio-duration')

// returnResponse = [{'SUM(COVERAGE_COUNT)': 5076}]
// queryData = 'The average ticket size from January 2021 to May 2021 was 517740'
// const randomString = Math.random().toString(36).slice(2, 7);
// const filename = `speech-${randomString}.wav`;
// const filename2 = './public/audio/' + filename;


// const audioExportPromise = new Promise((resolve, reject) => {
//     say.export(queryData, 'Samantha', 1.0, filename2, (err) => {
//         if (err) {
//             console.log(err);
//             reject(err);
//         } else {
//             console.log('Text has been saved to ' + filename2);
//             resolve();
//         }
//     });
// });
getAudioDurationInSeconds('./public/audio/' + 'speech-u5lfz.wav')
    .then(duration => console.log(duration))
    .catch(error => console.error(error));