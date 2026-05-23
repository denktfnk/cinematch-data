document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('resultsSection');
    const targetMovieTitle = document.getElementById('targetMovieTitle');
    const metricBar = document.getElementById('metricBar');
    const metricValue = document.getElementById('metricValue');
    const recommendationsList = document.getElementById('recommendationsList');
    
    // Modal Elements
    const movieModal = document.getElementById('movieModal');
    const closeModal = document.querySelector('.close-modal');
    const modalPoster = document.getElementById('modalPoster');
    const modalTitle = document.getElementById('modalTitle');
    const modalScore = document.getElementById('modalScore');
    const modalOverview = document.getElementById('modalOverview');
    const modalPlatforms = document.getElementById('modalPlatforms');

    let debounceTimer;

    // Handle Search Input (Partial Match)
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();

        if (query.length < 2) {
            searchResults.classList.remove('active');
            return;
        }

        debounceTimer = setTimeout(() => {
            fetchMatches(query);
        }, 300);
    });

    // Handle Search Button Click
    searchBtn.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) {
            fetchRecommendations(query); // Try direct match
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.classList.remove('active');
        }
    });

    // Modal Events
    closeModal.addEventListener('click', () => {
        movieModal.classList.add('hidden');
    });

    movieModal.addEventListener('click', (e) => {
        if (e.target === movieModal) {
            movieModal.classList.add('hidden');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !movieModal.classList.contains('hidden')) {
            movieModal.classList.add('hidden');
        }
    });

    async function fetchMatches(query) {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            searchResults.innerHTML = '';
            
            if (data.matches && data.matches.length > 0) {
                // Show up to 10 matches
                const displayMatches = data.matches.slice(0, 10);
                
                displayMatches.forEach(match => {
                    const li = document.createElement('li');
                    li.textContent = match;
                    li.addEventListener('click', () => {
                        searchInput.value = match;
                        searchResults.classList.remove('active');
                        fetchRecommendations(match);
                    });
                    searchResults.appendChild(li);
                });
                
                searchResults.classList.add('active');
            } else {
                searchResults.classList.remove('active');
            }
        } catch (error) {
            console.error('Error fetching matches:', error);
        }
    }

    async function fetchRecommendations(movieTitle) {
        // Hide previous results and show loader
        resultsSection.classList.add('hidden');
        searchResults.classList.remove('active');
        loader.classList.remove('hidden');

        try {
            const response = await fetch(`/api/recommend?movie=${encodeURIComponent(movieTitle)}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                alert(`Hata: ${errorData.detail || 'Film bulunamadı.'}`);
                loader.classList.add('hidden');
                return;
            }

            const data = await response.json();
            
            // Update UI with results
            displayResults(data);

        } catch (error) {
            console.error('Error fetching recommendations:', error);
            alert('Sunucuyla iletişim kurulurken bir hata oluştu.');
            loader.classList.add('hidden');
        }
    }

    function displayResults(data) {
        loader.classList.add('hidden');
        resultsSection.classList.remove('hidden');

        // Target movie info
        targetMovieTitle.textContent = data.movie;
        
        // Animate metric bar
        setTimeout(() => {
            metricBar.style.width = `${data.overlap_score}%`;
            
            // Animate number
            animateValue(metricValue, 0, data.overlap_score, 1000);
        }, 100);

        // Render recommendation cards
        recommendationsList.innerHTML = '';
        
        if (data.recommendations.length === 0) {
            recommendationsList.innerHTML = '<p>Üzgünüz, bu film için öneri bulunamadı.</p>';
            return;
        }

        data.recommendations.forEach((movie, index) => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            card.style.animationDelay = `${index * 0.1}s`;
            
            // Parse genres
            const genres = movie.genres.split(' ');
            const genresHtml = genres.map(g => `<span class="genre-tag">${g}</span>`).join('');
            
            card.innerHTML = `
                <div class="card-poster">
                    <img src="${movie.poster_url}" alt="${movie.title} Afişi" loading="lazy">
                </div>
                <div class="card-content">
                    <div class="card-header">
                        <h4 class="card-title">${movie.title}</h4>
                        <span class="similarity-badge">%${(movie.similarity_score * 100).toFixed(1)} Benzer</span>
                    </div>
                    <div class="card-genres">
                        ${genresHtml}
                    </div>
                </div>
            `;
            
            // Add click listener for modal
            card.addEventListener('click', () => openMovieDetails(movie.title, movie.poster_url));
            
            recommendationsList.appendChild(card);
        });
    }

    async function openMovieDetails(title, fallbackPoster) {
        // Reset and show modal with loading state
        modalTitle.textContent = "Yükleniyor...";
        modalOverview.textContent = "Film detayları aranıyor...";
        modalScore.textContent = "-";
        modalPoster.src = fallbackPoster;
        modalPlatforms.innerHTML = '';
        movieModal.classList.remove('hidden');

        try {
            const response = await fetch(`/api/movie_details?title=${encodeURIComponent(title)}`);
            if (!response.ok) {
                modalTitle.textContent = title;
                modalOverview.textContent = "Film detayları bulunamadı.";
                return;
            }

            const data = await response.json();
            
            modalTitle.textContent = data.title;
            modalScore.textContent = data.score > 0 ? data.score.toFixed(1) : "?";
            modalOverview.textContent = data.overview;
            
            if (data.poster_url) {
                modalPoster.src = data.poster_url;
            }

            if (data.platforms && data.platforms.length > 0) {
                modalPlatforms.innerHTML = data.platforms.map(p => 
                    `<img src="${p.logo}" alt="${p.name}" class="platform-logo" title="${p.name}">`
                ).join('');
            } else {
                modalPlatforms.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">Türkiye bölgesi için bilinen bir yayıncı bulunamadı.</p>';
            }

        } catch (error) {
            console.error('Error fetching movie details:', error);
            modalTitle.textContent = title;
            modalOverview.textContent = "Bağlantı hatası oluştu.";
        }
    }

    // Number counter animation function
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = `%${(progress * (end - start) + start).toFixed(2)}`;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
});
