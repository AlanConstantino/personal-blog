// get HTML Node list of buttons and convert them to an array
const buttons = [...document.getElementsByTagName('button')];

buttons.forEach(button => {
    const button = button.id;

    button.addEventListener('click', () => {
        switch (button) {
            case 'terminal-article':
                window.location.href = './articles/getting-started-with-the-terminal.html';
                break;

            case 'discord-python-article':
                window.location.href = './articles/creating-a-discord-bot-with-python.html';
                break;

            default:
                window.location.href = './';
        }
    });
});