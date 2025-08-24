// breadcrumb.js

// Array to store breadcrumb links with hierarchical structure
let breadcrumbs = [];
const breadcrumbList = document.getElementById('breadcrumb-list');
const BREADCRUMB_STORAGE_KEY = 'app_breadcrumbs';

// Define the page hierarchy and relationships
// This will be populated dynamically based on actual Django URLs
let PAGE_HIERARCHY = {};

// Function to initialize page hierarchy from DOM
function initializePageHierarchy() {
    // Get resolved URLs from the hidden URL resolver
    const urlResolver = document.getElementById('url-resolver');
    if (urlResolver) {
        const links = urlResolver.querySelectorAll('a[data-template-url][data-label]');
        links.forEach(link => {
            const url = normalizeUrl(link.href);
            const label = link.getAttribute('data-label');
            
            // Determine if it's a dashboard page
            const isDashboard = label.toLowerCase().includes('dashboard') || 
                              url.includes('admin_dashboard') || 
                              url.includes('employee_dashboard');
            
            PAGE_HIERARCHY[url] = {
                label: label,
                level: isDashboard ? 0 : 1,
                parent: null
            };
        });
    }
    
    // Add common patterns if not found in DOM
    const currentPath = normalizeUrl(window.location.pathname);
    if (!PAGE_HIERARCHY[currentPath]) {
        const pageTitle = document.querySelector('meta[name="page-title"]')?.content || 
                         document.title || 'Page';
        
        const isDashboard = pageTitle.toLowerCase().includes('dashboard') ||
                          currentPath.includes('dashboard');
        
        PAGE_HIERARCHY[currentPath] = {
            label: pageTitle,
            level: isDashboard ? 0 : 1,
            parent: null
        };
    }
}

// Function to load breadcrumbs from localStorage
function loadBreadcrumbs() {
    try {
        const stored = localStorage.getItem(BREADCRUMB_STORAGE_KEY);
        if (stored) {
            breadcrumbs = JSON.parse(stored);
            // Validate stored data structure
            breadcrumbs = breadcrumbs.filter(item => 
                item && typeof item === 'object' && item.label && item.url
            );
        }
    } catch (error) {
        console.warn('Failed to load breadcrumbs from localStorage:', error);
        breadcrumbs = [];
    }
}

// Function to save breadcrumbs to localStorage
function saveBreadcrumbs() {
    try {
        localStorage.setItem(BREADCRUMB_STORAGE_KEY, JSON.stringify(breadcrumbs));
    } catch (error) {
        console.warn('Failed to save breadcrumbs to localStorage:', error);
    }
}

// Function to determine if a page is a dashboard/root page
function isDashboardPage(url, label = '') {
    // Check if URL contains dashboard-related patterns
    const urlPatterns = ['dashboard', 'admin_dashboard', 'employee_dashboard'];
    const hasUrlPattern = urlPatterns.some(pattern => url.includes(pattern));
    
    // Check if label indicates it's a dashboard
    const hasLabelPattern = label.toLowerCase().includes('dashboard');
    
    // Check hierarchy definition
    const hierarchyInfo = PAGE_HIERARCHY[url];
    const isRootLevel = hierarchyInfo?.level === 0;
    
    return hasUrlPattern || hasLabelPattern || isRootLevel;
}

// Function to get the appropriate dashboard based on user role or previous navigation
function getDashboardPage() {
    // Check if we have a dashboard in current breadcrumbs
    const dashboardBreadcrumb = breadcrumbs.find(item => 
        isDashboardPage(item.url, item.label)
    );
    if (dashboardBreadcrumb) {
        return dashboardBreadcrumb;
    }
    
    // Try to find dashboard from stored hierarchy
    const dashboardEntry = Object.entries(PAGE_HIERARCHY).find(([url, info]) => 
        info.level === 0 && info.label.toLowerCase().includes('dashboard')
    );
    if (dashboardEntry) {
        return { label: dashboardEntry[1].label, url: dashboardEntry[0] };
    }
    
    // Determine from user role or DOM
    const isAdmin = document.getElementById("isAdmin")?.textContent?.trim().toLowerCase() === "admin";
    
    // Try to get resolved URL from DOM
    const dashboardLink = document.querySelector(
        isAdmin ? 'a[data-label*="Admin Dashboard"]' : 'a[data-label*="Employee Dashboard"]'
    );
    
    if (dashboardLink) {
        return { 
            label: dashboardLink.getAttribute('data-label'), 
            url: normalizeUrl(dashboardLink.href) 
        };
    }
    
    // Fallback
    const fallbackLabel = isAdmin ? 'Admin Dashboard' : 'Employee Dashboard';
    const fallbackUrl = isAdmin ? '/admin_dashboard/' : '/employee_dashboard/';
    
    return { label: fallbackLabel, url: fallbackUrl };
}

// Function to build proper breadcrumb hierarchy
function buildBreadcrumbPath(currentLabel, currentUrl) {
    const newBreadcrumbs = [];
    
    // If current page is a dashboard, it's the only breadcrumb
    if (isDashboardPage(currentUrl, currentLabel)) {
        newBreadcrumbs.push({ label: currentLabel, url: currentUrl });
    } else {
        // Add dashboard as root
        const dashboard = getDashboardPage();
        
        // Make sure we don't add the same page twice
        if (normalizeUrl(dashboard.url) !== normalizeUrl(currentUrl)) {
            newBreadcrumbs.push(dashboard);
        }
        
        // Add current page
        newBreadcrumbs.push({ label: currentLabel, url: currentUrl });
    }
    
    return newBreadcrumbs;
}

// Function to update the breadcrumb with proper hierarchy
function updateBreadcrumb(label, url) {
    // Build the proper breadcrumb path
    breadcrumbs = buildBreadcrumbPath(label, url);
    
    saveBreadcrumbs();
    renderBreadcrumbs();
}

// Function to render the breadcrumbs from the array
function renderBreadcrumbs() {
    if (!breadcrumbList) return; // Guard to ensure element exists
    breadcrumbList.innerHTML = '';
    
    if (breadcrumbs.length === 0) return;
    
    breadcrumbs.forEach((item, index) => {
        const li = document.createElement('li');
        li.classList.add('flex', 'items-center', 'text-sm');

        const isLast = index === breadcrumbs.length - 1;

        if (isLast) {
            // Current page - not clickable
            li.innerHTML = `<span class="font-medium text-gray-500">${escapeHtml(item.label)}</span>`;
        } else {
            // Previous pages - clickable
            li.innerHTML = `
                <a href="${escapeHtml(item.url)}" class="text-blue-600 hover:text-blue-800 font-medium transition-colors duration-200">${escapeHtml(item.label)}</a>
                <svg class="flex-shrink-0 w-5 h-5 text-gray-400 mx-2" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
                </svg>
            `;
        }
        breadcrumbList.appendChild(li);
    });
}

// Function to escape HTML to prevent XSS
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Function to clear breadcrumb history
function clearBreadcrumbs() {
    breadcrumbs = [];
    localStorage.removeItem(BREADCRUMB_STORAGE_KEY);
    renderBreadcrumbs();
}

// Function to get resolved URL (for Django template tags)
function getResolvedUrl(templateUrl) {
    // If the URL contains Django template syntax, try to find the resolved version
    const links = document.querySelectorAll('a[href]');
    for (let link of links) {
        if (link.getAttribute('data-template-url') === templateUrl || 
            link.href.includes(templateUrl.replace('/', ''))) {
            return link.href;
        }
    }
    return templateUrl; // Return as-is if no resolved version found
}

// Function to normalize URL for comparison
function normalizeUrl(url) {
    // Remove domain and ensure leading slash
    const path = url.replace(window.location.origin, '');
    return path.startsWith('/') ? path : '/' + path;
}

// Auto-initialize the breadcrumb on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize page hierarchy from DOM
    initializePageHierarchy();
    
    // Load existing breadcrumbs from localStorage
    loadBreadcrumbs();
    
    // Get page info from meta tags, data attributes, or defaults
    const pageLabel = document.querySelector('meta[name="page-title"]')?.content || 
                     document.querySelector('[data-page-title]')?.dataset.pageTitle || 
                     document.title;
    
    let pageUrl = document.querySelector('meta[name="page-url"]')?.content || 
                  document.querySelector('[data-page-url]')?.dataset.pageUrl || 
                  window.location.pathname;
    
    pageUrl = normalizeUrl(pageUrl);
    
    // Debug logging to help identify issues
    console.log('Breadcrumb Debug:', {
        pageLabel,
        pageUrl,
        isDashboard: isDashboardPage(pageUrl, pageLabel),
        hierarchy: PAGE_HIERARCHY[pageUrl]
    });
    
    updateBreadcrumb(pageLabel, pageUrl);
});

// Handle navigation clicks to update breadcrumbs
document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (link && link.href && !link.href.startsWith('mailto:') && !link.href.startsWith('tel:')) {
        const url = normalizeUrl(link.href);
        const label = link.getAttribute('data-label') || 
                     link.textContent.trim() || 
                     link.getAttribute('title') || 
                     'Page';
        
        // Don't update breadcrumb immediately - let the page load handle it
        // This prevents issues with SPA-style navigation
    }
});

// Export functions for external use
window.breadcrumbManager = {
    update: updateBreadcrumb,
    clear: clearBreadcrumbs,
    load: loadBreadcrumbs,
    save: saveBreadcrumbs,
    getCurrentPath: () => [...breadcrumbs] // Return copy of current breadcrumbs
};