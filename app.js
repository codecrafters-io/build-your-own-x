// Load tutorials data
let tutorialsData = {};
let allTutorials = [];
let filteredTutorials = [];
let currentFilter = null;

// Initialize the app
async function init() {
    try {
        const response = await fetch('tutorials_data.json');
        tutorialsData = await response.json();
        
        // Flatten all tutorials for search
        allTutorials = [];
        Object.entries(tutorialsData).forEach(([category, data]) => {
            data.tutorials.forEach(tutorial => {
                allTutorials.push({
                    ...tutorial,
                    category,
                    icon: data.icon
                });
            });
        });
        
        filteredTutorials = [...allTutorials];
        
        renderCategories();
        updateStats();
        setupEventListeners();
    } catch (error) {
        console.error('Error loading tutorials:', error);
        document.getElementById('categories').innerHTML = 
            '<div class="empty-state"><div class="empty-state-icon">❌</div><div class="empty-state-text">Error loading tutorials data</div></div>';
    }
}

// Render all categories
function renderCategories() {
    const container = document.getElementById('categories');
    container.innerHTML = '';
    
    const categoriesWithTutorials = Object.entries(tutorialsData).filter(([_, data]) => {
        // Check if any tutorials match current filter
        if (!currentFilter) return data.tutorials.length > 0;
        
        return data.tutorials.some(t => 
            filteredTutorials.some(ft => 
                ft.category === _ && 
                ft.title === t.title && 
                ft.language === t.language
            )
        );
    });
    
    if (categoriesWithTutorials.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">No tutorials found</div>
                <p style="margin-top: 10px; color: var(--text-light);">Try a different search term</p>
            </div>
        `;
        return;
    }
    
    categoriesWithTutorials.forEach(([category, data], index) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category';
        categoryDiv.style.animationDelay = `${index * 0.1}s`;
        
        // Filter tutorials for this category
        const categoryTutorials = currentFilter 
            ? data.tutorials.filter(t => 
                filteredTutorials.some(ft => 
                    ft.category === category && 
                    ft.title === t.title && 
                    ft.language === t.language
                )
            )
            : data.tutorials;
        
        categoryDiv.innerHTML = `
            <div class="category-header" onclick="toggleCategory(this)">
                <div class="category-icon">${data.icon}</div>
                <div class="category-title">${category}</div>
                <div class="category-count">${categoryTutorials.length}</div>
                <div class="category-toggle">▼</div>
            </div>
            <div class="tutorials" id="tutorials-${category.replace(/\s+/g, '-')}">
                ${categoryTutorials.map(tutorial => createTutorialCard(tutorial, category, data.icon)).join('')}
            </div>
        `;
        
        container.appendChild(categoryDiv);
    });
}

// Create tutorial card HTML
function createTutorialCard(tutorial, category, icon) {
    const videoLabel = tutorial.is_video ? ' 🎥' : '';
    return `
        <div class="tutorial-card" onclick='showTutorialDetails(${JSON.stringify(tutorial).replace(/'/g, "&apos;")}, "${category}", "${icon}")'>
            <div class="tutorial-language">${tutorial.language}</div>
            <div class="tutorial-title">${tutorial.title}${videoLabel}</div>
            <div class="tutorial-link" onclick="event.stopPropagation(); window.open('${tutorial.url}', '_blank')">
                View Tutorial →
            </div>
        </div>
    `;
}

// Show tutorial details in modal
function showTutorialDetails(tutorial, category, icon) {
    const modal = document.getElementById('tutorialModal');
    const modalBody = document.getElementById('modalBody');
    
    const videoInfo = tutorial.is_video ? '<p><strong>📹 Format:</strong> Video Tutorial</p>' : '<p><strong>📝 Format:</strong> Written Tutorial</p>';
    
    modalBody.innerHTML = `
        <h2>${icon} ${tutorial.title}</h2>
        <p><strong>Category:</strong> ${category}</p>
        <p><strong>Language/Tech:</strong> ${tutorial.language}</p>
        ${videoInfo}
        <p><strong>Description:</strong> Learn how to build your own ${category.toLowerCase()} using ${tutorial.language}. This tutorial will guide you through the process step by step.</p>
        <div style="margin-top: 30px; padding: 20px; background: var(--light); border-radius: 10px; border-left: 4px solid var(--primary);">
            <p style="margin-bottom: 15px;"><strong>🚀 Ready to start learning?</strong></p>
            <a href="${tutorial.url}" target="_blank" style="display: inline-block; padding: 12px 24px; background: var(--primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">
                Open Tutorial
            </a>
        </div>
        <div style="margin-top: 20px; padding: 15px; background: #fef3c7; border-radius: 8px; border-left: 4px solid var(--warning);">
            <p style="margin: 0; font-size: 0.9rem;"><strong>💡 Tip:</strong> "What I cannot create, I do not understand" - Building from scratch is the best way to truly understand how technology works!</p>
        </div>
    `;
    
    modal.style.display = 'block';
}

// Toggle category collapse
function toggleCategory(header) {
    const toggle = header.querySelector('.category-toggle');
    const tutorials = header.nextElementSibling;
    
    if (tutorials.style.display === 'none') {
        tutorials.style.display = 'grid';
        toggle.classList.remove('collapsed');
    } else {
        tutorials.style.display = 'none';
        toggle.classList.add('collapsed');
    }
}

// Search functionality
function handleSearch(searchTerm) {
    searchTerm = searchTerm.toLowerCase().trim();
    
    if (!searchTerm) {
        filteredTutorials = [...allTutorials];
        currentFilter = null;
        document.getElementById('filterChips').innerHTML = '';
    } else {
        filteredTutorials = allTutorials.filter(tutorial => 
            tutorial.title.toLowerCase().includes(searchTerm) ||
            tutorial.language.toLowerCase().includes(searchTerm) ||
            tutorial.category.toLowerCase().includes(searchTerm)
        );
        currentFilter = searchTerm;
        
        // Show filter chip
        const filterChips = document.getElementById('filterChips');
        filterChips.innerHTML = `
            <div class="chip active">
                🔍 "${searchTerm}"
                <span onclick="clearSearch()" style="cursor: pointer;">✕</span>
            </div>
        `;
    }
    
    renderCategories();
    updateStats();
}

// Clear search
function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.querySelector('.clear-btn').classList.remove('show');
    handleSearch('');
}

// Surprise me - random tutorial
function surpriseMe() {
    const randomTutorial = allTutorials[Math.floor(Math.random() * allTutorials.length)];
    
    // Scroll to category
    const categoryId = `tutorials-${randomTutorial.category.replace(/\s+/g, '-')}`;
    const categoryElement = document.getElementById(categoryId);
    
    if (categoryElement) {
        // Expand category if collapsed
        if (categoryElement.style.display === 'none') {
            categoryElement.previousElementSibling.click();
        }
        
        // Scroll to category
        categoryElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Highlight the tutorial card
        const cards = categoryElement.querySelectorAll('.tutorial-card');
        cards.forEach(card => card.classList.remove('highlight'));
        
        setTimeout(() => {
            const matchingCard = Array.from(cards).find(card => 
                card.textContent.includes(randomTutorial.title)
            );
            if (matchingCard) {
                matchingCard.classList.add('highlight');
                setTimeout(() => matchingCard.classList.remove('highlight'), 3000);
            }
        }, 500);
    }
    
    // Show the tutorial details
    setTimeout(() => {
        showTutorialDetails(randomTutorial, randomTutorial.category, randomTutorial.icon);
    }, 1000);
}

// Show all tutorials
function showAll() {
    clearSearch();
    
    // Expand all categories
    document.querySelectorAll('.tutorials').forEach(tutorials => {
        tutorials.style.display = 'grid';
        const toggle = tutorials.previousElementSibling.querySelector('.category-toggle');
        if (toggle) toggle.classList.remove('collapsed');
    });
}

// Update statistics
function updateStats() {
    const languages = new Set(allTutorials.map(t => t.language));
    const categories = Object.keys(tutorialsData).length;
    
    document.getElementById('totalTutorials').textContent = allTutorials.length;
    document.getElementById('totalCategories').textContent = categories;
    document.getElementById('totalLanguages').textContent = languages.size;
    document.getElementById('visibleCount').textContent = filteredTutorials.length;
}

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.querySelector('.clear-btn');
    const surpriseBtn = document.getElementById('surpriseBtn');
    const showAllBtn = document.getElementById('showAllBtn');
    const modal = document.getElementById('tutorialModal');
    const closeModal = document.querySelector('.close-modal');
    
    // Search input
    searchInput.addEventListener('input', (e) => {
        const value = e.target.value;
        if (value) {
            clearBtn.classList.add('show');
        } else {
            clearBtn.classList.remove('show');
        }
        handleSearch(value);
    });
    
    // Clear button
    clearBtn.addEventListener('click', clearSearch);
    
    // Surprise button
    surpriseBtn.addEventListener('click', surpriseMe);
    
    // Show all button
    showAllBtn.addEventListener('click', showAll);
    
    // Modal close
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape to close modal
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
        // Ctrl+K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
        // Ctrl+R for random
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            surpriseMe();
        }
    });
}

// Initialize on load
window.addEventListener('DOMContentLoaded', init);
