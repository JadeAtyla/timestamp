// sidebar.js

// Function to populate the sidebar with a given set of links
function populateSidebar(links) {
    const sidebarNav = document.getElementById('sidebar-nav');
    if (!sidebarNav) return; // Guard to ensure the element exists

    sidebarNav.innerHTML = ''; // Clear existing links
    links.forEach(link => {
        const a = document.createElement('a');
        a.href = link.url;
        a.classList.add(
            'flex', 'items-center', 'py-2', 'px-3', 'rounded-lg', 'text-gray-700',
            'hover:bg-gray-200', 'hover:text-blue-600', 'transition-colors', 'duration-200'
        );
        a.innerHTML = `
            ${link.icon || ''}
            <span class="ml-3 font-medium">${link.label}</span>
        `;

        // 👉 Clear localStorage when logout is clicked (case-insensitive)
        if (link.label.toLowerCase() === "logout") {
            a.addEventListener("click", () => {
                localStorage.clear();
            });
        }

        // Add an 'active' class if the current URL matches the link's URL
        if (window.location.pathname === a.pathname) {
            a.classList.add('bg-blue-100', 'text-blue-600');
        }

        sidebarNav.appendChild(a);
    });
}

// Sidebar toggle logic for mobile
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('aside');
    const toggleButton = document.getElementById('sidebar-toggle');
    const overlay = document.getElementById('sidebar-overlay');

    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
            overlay.classList.toggle('opacity-0');
            overlay.classList.toggle('pointer-events-none');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('opacity-0');
            overlay.classList.add('pointer-events-none');
        });
    }
});
