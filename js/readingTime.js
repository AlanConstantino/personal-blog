/* Just for internal purposes */

// Calculate reading time
function calculateReadingTime(text) {
    const averageWordsPerMinute = 250;
    const numberOfWords = text.split(/\s/g).length;
    const readingTime = Math.ceil(numberOfWords / averageWordsPerMinute);
    return readingTime;
}

const article = document.getElementById('main-article').innerText;
const readingTime = calculateReadingTime(article);
console.log(readingTime);