// get HTML Node list of buttons and convert them to an array
const buttons = [...document.getElementsByTagName('button')];

// for each button in the buttons array
buttons.forEach(button => {
    const buttonId = button.id; // save button id for later
    button.addEventListener('click', () => { // add an event listener
        // check if button id is the same for the terminal-article
        if (buttonId === 'terminal-article') {
            window.location.href = './articles/getting-started-with-the-terminal.html'; // relocate to terminal article
        }
    });
});