    // Sample Data
    let userData = {};

    // Your own boards
    let yourBoards = [];

    // Guest boards
    let guestBoards = [];

    // DOM Elements

    const yourBoardsContainer = document.getElementById('your-boards');
    const guestBoardsContainer = document.getElementById('guest-boards');
    const yourBoardsEmpty = document.getElementById('your-boards-empty');
    const guestBoardsEmpty = document.getElementById('guest-boards-empty');
    const createBoardModal = document.getElementById('create-board-modal');
    const createBoardBtn = document.getElementById('create-board-btn');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelCreateBtn = document.getElementById('cancel-create');
    const confirmCreateBtn = document.getElementById('confirm-create');
    const boardNameInput = document.getElementById('board-name-input');
    const colorPicker = document.getElementById('color-picker');


    let selectedColor = '#0079bf';


    // Color picker functionality
    colorPicker.addEventListener('click', (e) => {
        if (e.target.classList.contains('color-option')) {
            document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
            e.target.classList.add('selected');
            selectedColor = e.target.getAttribute('data-color');
        }
    });

    // Render Board Card
    function renderBoardCard(board, isGuest = false) {
        const card = document.createElement('div');
        card.className = 'board-card';

        if (board.background_color) {
            card.style.background = board.background_color;

        } else if (board.background_image != null) {
            card.style.backgroundImage = `url(${board.background_image})`;
            card.style.backgroundSize = "cover";
            card.style.backgroundPosition = "center";
            card.style.backgroundRepeat = "no-repeat";

        }


        let metaInfo = `${board.cards} cards`;
        if (isGuest) {
            metaInfo = `Owner: ${board.owner.username} · ${board.cards} cards`;
        }

        card.innerHTML = `
                ${isGuest ? '<div class="guest-badge">👥 Guest</div>' : ''}
                <div class="board-card-title">${board.name}</div>
                <div class="board-card-meta">${metaInfo}</div>
            `;

        card.addEventListener('click', () => {
            alert(`Opening board: ${board.name}\n${isGuest ? 'Guest workspace' : 'Your workspace'}`);
        });

        return card;
    }

    // Render All Boards
    function renderBoards() {
        // Your Boards
        yourBoardsContainer.innerHTML = '';
        if (yourBoards.length === 0) {
            yourBoardsEmpty.classList.remove('hidden');
        } else {
            yourBoardsEmpty.classList.add('hidden');
            yourBoards.forEach(board => {
                yourBoardsContainer.appendChild(renderBoardCard(board));
            });
            // Add Create New Board card
            const createCard = document.createElement('div');
            createCard.className = 'board-card create-new';
            createCard.innerHTML = `
                    <div class="create-new-content">
                        <div class="create-new-icon">+</div>
                        <div class="create-new-text">Create New Board</div>
                    </div>
                `;
            createCard.addEventListener('click', openCreateModal);
            yourBoardsContainer.appendChild(createCard);
        }

        // Guest Boards
        guestBoardsContainer.innerHTML = '';
        if (guestBoards.length === 0) {
            guestBoardsEmpty.classList.remove('hidden');
        } else {
            guestBoardsEmpty.classList.add('hidden');
            guestBoards.forEach(board => {
                guestBoardsContainer.appendChild(renderBoardCard(board, true));
            });
        }
    }

    // Modal Functions
    function openCreateModal() {
        createBoardModal.classList.add('active');
        boardNameInput.focus();
    }

    function closeCreateModal() {
        createBoardModal.classList.remove('active');
        boardNameInput.value = '';
        document.querySelector('.color-option[data-color="#0079bf"]').classList.add('selected');
        selectedColor = '#0079bf';
    }

    async function fetchCreateNewBoard(name) {

    }

    // Create New Board
    async function createNewBoard() {
        const name = boardNameInput.value.trim();

        if (!name) {
            alert('Please enter a board name.');
            return;
        }
        try {
            body = JSON.stringify({
                "name": name,
                "background_color": selectedColor,
            });
            const response = await auth.authenticatedRequest(`api/boards/`, body, "POST");
            const newBoard = await response.json()

            if (response.ok) {

                yourBoards.push(newBoard);
                renderBoards();
                closeCreateModal();

            } else {
                closeCreateModal();

            }
        } catch (error) {
            closeCreateModal();
            console.log(error)
        }


    }


    // Event Listeners
    createBoardBtn.addEventListener('click', openCreateModal);
    closeModalBtn.addEventListener('click', closeCreateModal);
    cancelCreateBtn.addEventListener('click', closeCreateModal);
    confirmCreateBtn.addEventListener('click', createNewBoard);

    createBoardModal.addEventListener('click', (e) => {
        if (e.target === createBoardModal) {
            closeCreateModal();
        }
    });

    boardNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            createNewBoard();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (createBoardModal.classList.contains('active')) {
                closeCreateModal();
            }
            if (profileDropdown.classList.contains('active')) {
                profileDropdown.classList.remove('active');
            }
            if (searchResults.classList.contains('active')) {
                searchResults.classList.remove('active');
            }
        }

        // Ctrl+K or Cmd+K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
    });

    function renderUserInfo() {
        document.querySelector(".profile-name").innerText = userData.username
        document.querySelector(".profile-email").innerText = userData.email
        if (userData.profile_image) {
            document.querySelector(".profile-avatar-lg").innerHTML = `<img src="${userData.profile_image}">`
            document.getElementById("user-avatar-btn").innerHTML = `<img src="${userData.profile_image}">`
        } else {
            document.querySelector(".profile-avatar-lg").innerText = userData.username[0]
            document.getElementById("user-avatar-btn").innerText = userData.username[0]
        }
        console.log(userData)
    }

    async function getContentData() {
        // id: 1,
        // name: "Marketing Website",
        // color: "#0079bf",
        // cards: 12,
        try {

            const boardResponse = await auth.authenticatedRequest(`api/boards/`, null, "GET")
            const guestBoardResponse = await auth.authenticatedRequest(`api/guest-boards/`, null, "GET")



            const boardData = await boardResponse.json()
            const guestBoardData = await guestBoardResponse.json()

            if (boardResponse.ok && guestBoardResponse.ok) {
                yourBoards = boardData;
                guestBoards = guestBoardData;
                renderBoards();
            }
            console.log(boardData)
        } catch (error) {
            console.log(error)
        }
    }
    // Initialize
    getContentData()

    console.log('SMBoards Page Loaded');
    console.log('Press Ctrl+K to focus search');

    document.getElementById("profile-logout-btn").addEventListener("click", () => {
        auth.logout()
    })