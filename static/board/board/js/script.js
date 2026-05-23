const boardMenuBtn = document.getElementById("board-menu-dots-btn")
const BoardMenuDropdown = document.getElementById("board-menu-dropdown")
const boardStatusBtn = document.getElementById("board-status-dots-btn")
const boardStatusDropdown = document.getElementById("board-status-dropdown")



// board menu Dropdown Toggle
boardMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    BoardMenuDropdown.classList.toggle('active');

});

// board status Dropdown Toggle
boardStatusBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    boardStatusDropdown.classList.toggle('active');

});

document.addEventListener('click', (e) => {
    if (!BoardMenuDropdown.contains(e.target) && e.target !== boardMenuBtn) {
        BoardMenuDropdown.classList.remove('active');
    }

    if (!boardStatusDropdown.contains(e.target) && e.target !== boardStatusBtn) {
        boardStatusDropdown.classList.remove('active');
    }
});