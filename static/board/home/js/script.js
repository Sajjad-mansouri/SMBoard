    const auth = new Auth()
    // Sample Data
    let userData = {};

    // Your own boards
    let yourBoards = [];

    // Guest boards
    let guestBoards = [];

    // DOM Elements
    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    const searchResults = document.getElementById('search-results');
    const searchResultsContent = document.getElementById('search-results-content');
    const userAvatarBtn = document.getElementById('user-avatar-btn');
    const profileDropdown = document.getElementById('profile-dropdown');
    const profileSettingsBtn = document.getElementById('profile-settings-btn');
    const profileLogoutBtn = document.getElementById('profile-logout-btn');
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

    // Profile Dropdown Toggle
    userAvatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown.classList.toggle('active');
        searchResults.classList.remove('active');
    });

    // Close profile dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!profileDropdown.contains(e.target) && e.target !== userAvatarBtn) {
            profileDropdown.classList.remove('active');
        }
    });

    // Profile Dropdown Actions
    profileSettingsBtn.addEventListener('click', () => {
        profileDropdown.classList.remove('active');
        alert('Opening Settings page...');
    });



    // Search Functionality
    function getAllSearchableItems() {
        const boards = [];
        const cards = [];

        // Collect all boards
        [...yourBoards, ...guestBoards].forEach(board => {
            boards.push({
                type: 'board',
                id: board.id,
                name: board.name,
                color: board.color,
                meta: board.owner ? `Owner: ${board.owner} · ${board.cards} cards` : `${board.cards} cards`,
                isGuest: !!board.owner
            });

            // Collect cards from each board
            if (board.cardsList) {
                board.cardsList.forEach(card => {
                    cards.push({
                        type: 'card',
                        id: card.id,
                        name: card.name,
                        boardName: card.board,
                        list: card.list,
                        labels: card.labels,
                        dueDate: card.dueDate,
                        boardColor: board.color
                    });
                });
            }
        });

        return {
            boards,
            cards
        };
    }

    function highlightMatch(text, query) {
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }

    function performSearch(query) {
        if (!query.trim()) {
            searchResults.classList.remove('active');
            searchClearBtn.classList.remove('visible');
            return;
        }

        searchClearBtn.classList.add('visible');
        const {
            boards,
            cards
        } = getAllSearchableItems();
        const searchTerm = query.toLowerCase();

        const matchedBoards = boards.filter(board =>
            board.name.toLowerCase().includes(searchTerm)
        );

        const matchedCards = cards.filter(card =>
            card.name.toLowerCase().includes(searchTerm) ||
            card.boardName.toLowerCase().includes(searchTerm) ||
            card.labels.toLowerCase().includes(searchTerm)
        );

        let html = '';

        if (matchedBoards.length === 0 && matchedCards.length === 0) {
            html = '<div class="search-no-results">🔍 No results found for "' + query + '"</div>';
        } else {
            // Boards section
            if (matchedBoards.length > 0) {
                html += '<div class="search-results-header">📊 Boards (' + matchedBoards.length + ')</div>';
                matchedBoards.forEach(board => {
                    html += `
                            <div class="search-result-item" data-type="board" data-id="${board.id}">
                                <div class="search-result-icon board-icon" style="background: ${board.color};">📋</div>
                                <div class="search-result-info">
                                    <div class="search-result-title">${highlightMatch(board.name, query)}</div>
                                    <div class="search-result-meta">${board.meta}</div>
                                </div>
                                ${board.isGuest ? '<span class="search-result-badge">👥 Guest</span>' : ''}
                            </div>
                        `;
                });
            }

            // Cards section
            if (matchedCards.length > 0) {
                html += '<div class="search-results-header">📋 Cards (' + matchedCards.length + ')</div>';
                matchedCards.forEach(card => {
                    html += `
                            <div class="search-result-item" data-type="card" data-id="${card.id}">
                                <div class="search-result-icon card-icon">📄</div>
                                <div class="search-result-info">
                                    <div class="search-result-title">${highlightMatch(card.name, query)}</div>
                                    <div class="search-result-meta">
                                        ${card.boardName} · ${card.list} · ${card.labels}
                                        ${card.dueDate ? ' · 📅 ' + card.dueDate : ''}
                                    </div>
                                </div>
                                <span class="search-result-badge" style="background: ${card.boardColor}; color: white; font-size:0.6rem;">${card.boardName}</span>
                            </div>
                        `;
                });
            }
        }

        searchResultsContent.innerHTML = html;
        searchResults.classList.add('active');

        // Add click events to search result items
        searchResultsContent.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const type = item.getAttribute('data-type');
                const id = item.getAttribute('data-id');

                if (type === 'board') {
                    const board = [...yourBoards, ...guestBoards].find(b => b.id == id);
                    if (board) {
                        alert(`Opening board: ${board.name}`);
                    }
                } else if (type === 'card') {
                    let foundCard = null;
                    [...yourBoards, ...guestBoards].forEach(board => {
                        if (board.cardsList) {
                            const card = board.cardsList.find(c => c.id == id);
                            if (card) foundCard = card;
                        }
                    });
                    if (foundCard) {
                        alert(`Opening card: ${foundCard.name}\nBoard: ${foundCard.boardName}\nList: ${foundCard.list}`);
                    }
                }

                searchResults.classList.remove('active');
                searchInput.value = '';
                searchClearBtn.classList.remove('visible');
            });
        });
    }

    searchInput.addEventListener('input', (e) => {
        performSearch(e.target.value);
    });

    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim()) {
            performSearch(searchInput.value);
        }
    });

    searchClearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchResults.classList.remove('active');
        searchClearBtn.classList.remove('visible');
        searchInput.focus();
    });

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.classList.remove('active');
        }
    });

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
            metaInfo = `Owner: ${board.user.username} · ${board.cards} cards`;
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
                console.log(newBoard)
                yourBoards.push(newBoard);
                renderBoards();
                closeCreateModal();
                console.log(data)
            } else {
                closeCreateModal();
                console.log(data)
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

    async function getData() {
        // id: 1,
        // name: "Marketing Website",
        // color: "#0079bf",
        // cards: 12,
        try {

            const boardResponse = await auth.authenticatedRequest(`api/boards/`, null, "GET")
            const guestBoardResponse = await auth.authenticatedRequest(`api/guest-boards/`, null, "GET")
            const userResponse = await auth.authenticatedRequest(`api/user/`, null, "GET")


            const boardData = await boardResponse.json()
            const guestBoardData = await guestBoardResponse.json()
            userData = await userResponse.json()
            console.log(userData)
            console.log(guestBoardData)
            if (userResponse.ok) {
                renderUserInfo()
            }
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
    getData()

    console.log('SMBoards Page Loaded');
    console.log('Press Ctrl+K to focus search');

    document.getElementById("profile-logout-btn").addEventListener("click", () => {
        auth.logout()
    })