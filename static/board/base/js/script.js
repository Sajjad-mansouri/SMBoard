const auth = new Auth()
const searchInput = document.getElementById('search-input');
const searchClearBtn = document.getElementById('search-clear-btn');
const searchResults = document.getElementById('search-results');
const searchResultsContent = document.getElementById('search-results-content');
const profileAvatarBtn = document.getElementById('profile-avatar-btn');
const profileDropdown = document.getElementById('profile-dropdown');
const profileSettingsBtn = document.getElementById('profile-settings-btn');
const profileLogoutBtn = document.getElementById('profile-logout-btn');



// Profile avatar button - shows dropdown
document.getElementById('profile-avatar-btn').onclick = (e) => {
    e.stopPropagation();

    const dropdown = document.getElementById('profile-dropdown');
    dropdown.classList.toggle('hidden');
    console.log(dropdown.width)
    if (!dropdown.classList.contains('hidden')) {
        const rect = e.target.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        console.log(rect)
        dropdown.style.top = rect.bottom + 4 + 'px';
        dropdown.style.left = rect.left - dropdown.offsetWidth + 'px';
    }
};

document.addEventListener('click', function(e) {
    if (!e.target.closest('#profile-avatar-btn') && !e.target.closest('#profile-dropdown')) {
        document.getElementById('profile-dropdown').classList.add('hidden');
    }
})

// Profile Dropdown Actions
profileSettingsBtn.addEventListener('click', () => {
    profileDropdown.classList.remove('active');
    alert('Opening Settings page...');
});



function highlightMatch(text, query) {
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

async function fetchSearchResult(query) {

    try {
        const searchBoarUrl = origin + `/api/search/board/?search=${query.trim()}`
        const searchCardUrl = origin + `/api/search/card/?search=${query.trim()}`

        const responseBoard = await auth.authenticatedRequest(searchBoarUrl, null, "GET")
        const responseCard = await auth.authenticatedRequest(searchCardUrl, null, "GET")

        dataBoard = await responseBoard.json()

        dataCard = await responseCard.json()

        if (responseBoard.ok) {
            const boards = [];
            const cards = [];
            dataBoard.forEach(board => {
                boards.push({
                    type: 'board',
                    id: board.id,
                    name: board.name,
                    color: board.background_color,
                    meta: board.is_owner ? `${board.cards} cards` : `Owner: ${board.owner} · ${board.cards} cards`,
                    isGuest: !board.is_owner
                });
            })

            dataCard.forEach(card => {
                cards.push({
                    type: 'card',
                    id: card.id,
                    name: card.name,
                    boardName: card.board,
                    list: card.board_list,
                    labels: card.labels,
                    dueDate: card.due_date,
                    boardColor: card.board.color
                });
            });

            return [boards, cards]

        } else {
            console.log('not ok')
        }
    } catch (error) {
        console.log(error)
    }

}

async function performSearch(query) {
    if (!query.trim()) {
        searchResults.classList.remove('active');
        searchClearBtn.classList.remove('visible');
        return;
    }

    searchClearBtn.classList.add('visible');
    let matchedCards = [];
    let matchedBoards = [];
    [matchedBoards, matchedCards] = await fetchSearchResult(query)

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

                const labels = card.labels.length != 0 ? `labels:${card.labels}` : ""

                html += `
                            <div class="search-result-item" data-type="card" data-id="${card.id}">
                                <div class="search-result-icon card-icon">📄</div>
                                <div class="search-result-info">
                                    <div class="search-result-title">${highlightMatch(card.name, query)}</div>
                                    <div class="search-result-meta">
                                        board:${card.boardName} , list:${card.list}, ${labels}
                                        ${card.dueDate != null ? ' · 📅 ' + card.dueDate.split("T")[0] : ''}
                                    </div>
                                </div>
                               
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

document.getElementById('search-clear-btn').addEventListener('click', () => {
    document.getElementById(
        'search-input').value = '';
    applyFilters();
    document.getElementById('search-clear-btn').classList.add('hidden');
});
document.getElementById('search-input').addEventListener('input', function() {
    document.getElementById(
        'search-clear-btn').classList.toggle('hidden', this.value === '');

});

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

function renderUserInfo() {
    document.querySelector(".profile-name").innerText = userData.username
    document.querySelector(".profile-email").innerText = userData.email
    if (userData.profile_image) {
        document.querySelector(".profile-avatar-lg").innerHTML = `<img src="${userData.profile_image}">`
        document.getElementById("profile-avatar-btn").innerHTML = `<img src="${userData.profile_image}">`
    } else {
        document.querySelector(".profile-avatar-lg").innerText = userData.username[0]
        document.getElementById("profile-avatar-btn").innerText = userData.username[0]
    }

}

async function getHeaderData() {
    try {
        const url = origin + `/api/user/`
        const userResponse = await auth.authenticatedRequest(url, null, "GET")
        userData = await userResponse.json()
        if (userResponse.ok) {
            renderUserInfo()
        }
    } catch (error) {
        console.log(error)
    }
}

getHeaderData()