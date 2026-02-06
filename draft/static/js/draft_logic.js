document.addEventListener('DOMContentLoaded', function() {
    // モーダル外クリックで閉じる処理
    window.onclick = function(event) {
        const modal = document.getElementById('playerModal');
        if (event.target == modal) closeModal();
    }

    // 検索機能
    const searchInput = document.getElementById('playerSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.player-card').forEach(card => {
                const name = card.dataset.name.toLowerCase();
                const team = card.dataset.team.toLowerCase();
                card.classList.toggle('d-none', !(name.includes(query) || team.includes(query)));
            });
        });
    }
});

// モーダル開閉
function openModal() {
    document.getElementById('playerModal').style.display = 'block';
    document.body.style.overflow = 'hidden'; // 背後を固定
}

function closeModal() {
    document.getElementById('playerModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}