/**
 * UsefulLinks Component
 * Displays a compact list of external links above the status indicator
 */
import { usefulLinks } from '../config/useful-links.js';

export class UsefulLinks {
    constructor(containerId = 'useful-links-container') {
        this.containerId = containerId;
        this.links = usefulLinks;
    }

    /**
     * Initialize the component - renders the links
     */
    init() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`UsefulLinks: Container with id "${this.containerId}" not found`);
            return;
        }

        this.render(container);
    }

    /**
     * Render the useful links section
     */
    render(container) {
        // Clear any existing content
        container.innerHTML = '';

        // Create the section title
        const title = document.createElement('div');
        title.className = 'useful-links-title';
        title.textContent = 'USEFUL LINKS';
        container.appendChild(title);

        // Create the links container
        const linksContainer = document.createElement('div');
        linksContainer.className = 'useful-links-list';
        container.appendChild(linksContainer);

        // Render each link
        this.links.forEach(link => {
            const linkChip = this.createLinkChip(link);
            linksContainer.appendChild(linkChip);
        });
    }

    /**
     * Create a single link chip element
     */
    createLinkChip(link) {
        const chip = document.createElement('a');
        chip.className = 'useful-link-chip';
        chip.href = '#';
        chip.title = `Open ${link.name}`;
        chip.setAttribute('data-url', link.url);
        
        // Add icon if provided
        if (link.icon) {
            const icon = document.createElement('span');
            icon.className = 'useful-link-icon';
            icon.textContent = link.icon;
            chip.appendChild(icon);
        }

        // Add link name
        const name = document.createElement('span');
        name.className = 'useful-link-name';
        name.textContent = link.name;
        chip.appendChild(name);

        // Add click handler to open link in new window
        chip.addEventListener('click', (e) => {
            e.preventDefault();
            this.openLink(link.url);
        });

        return chip;
    }

    /**
     * Validate URL to ensure it's safe to open
     */
    isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            // Only allow https URLs
            return urlObj.protocol === 'https:';
        } catch (e) {
            return false;
        }
    }

    /**
     * Open a link in a new browser window
     */
    openLink(url) {
        try {
            // Validate URL before opening
            if (!this.isValidUrl(url)) {
                console.error('Invalid or insecure URL:', url);
                window.logToServer('ERROR', `Blocked opening invalid URL: ${url}`);
                return;
            }

            // Use window.open with noopener and noreferrer for security
            window.open(url, '_blank', 'noopener,noreferrer');
            window.logToServer('INFO', `Opened useful link: ${url}`);
        } catch (error) {
            console.error('Error opening link:', error);
            window.logToServer('ERROR', `Failed to open useful link: ${url}`, error);
        }
    }
}

/**
 * Initialize the UsefulLinks component
 */
export function initUsefulLinks() {
    const usefulLinksComponent = new UsefulLinks();
    usefulLinksComponent.init();
}
