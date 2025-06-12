/**
 * Unified Product Card and Collection System
 * Provides consistent product display across the application
 */

class ProductCard {
    constructor(product, variant = 'standard', options = {}) {
        this.product = product;
        this.variant = variant; // 'compact', 'standard', 'detailed'
        this.options = {
            showCheckbox: false,
            showActions: true,
            showDelete: true,
            clickAction: 'select', // 'select', 'modal', 'navigate'
            ...options
        };
        this.selected = false;
        this.element = null;
        this.collection = null; // Reference to parent collection
    }

    /**
     * Render the product card HTML
     */
    render() {
        const cardClass = `product-card product-card--${this.variant}`;
        const wrapperClass = this.getWrapperClass();
        
        this.element = document.createElement('div');
        this.element.className = wrapperClass;
        this.element.innerHTML = this.getCardHTML();
        
        
        // Attach event listeners
        this.attachEventListeners();
        
        return this.element;
    }

    /**
     * Get wrapper CSS classes based on variant
     */
    getWrapperClass() {
        // Check if parent collection is strip layout for compact cards
        const isStripLayout = this.collection && this.collection.layout === 'strip';
        
        switch (this.variant) {
            case 'compact':
                return isStripLayout ? 
                    'col-auto product-card-wrapper' : 
                    'col-3 col-sm-2 col-md-1 product-card-wrapper';
            case 'standard':
                return 'col-12 col-sm-6 col-md-4 col-lg-3 product-card-wrapper';
            case 'detailed':
                return 'col-12 product-card-wrapper';
            default:
                return 'col-12 col-sm-6 col-md-4 col-lg-3 product-card-wrapper';
        }
    }

    /**
     * Generate card HTML based on variant
     */
    getCardHTML() {
        const product = this.product;
        const cardClass = `card h-100 shadow-sm product-card product-card--${this.variant}`;
        
        switch (this.variant) {
            case 'compact':
                return this.getCompactHTML();
            case 'standard':
                return this.getStandardHTML();
            case 'detailed':
                return this.getDetailedHTML();
            default:
                return this.getStandardHTML();
        }
    }

    /**
     * Compact variant - minimal display for strips
     */
    getCompactHTML() {
        const product = this.product;
        return `
            <div class="card product-card product-card--compact" data-product-id="${product.id}" style="cursor: default;">
                ${this.options.showCheckbox ? this.getCheckboxHTML() : ''}
                <div class="ratio ratio-1x1 product-card__image">
                    ${this.getImageHTML()}
                    ${this.getOverlayHTML()}
                </div>
            </div>
        `;
    }

    /**
     * Standard variant - full featured for grids
     */
    getStandardHTML() {
        const product = this.product;
        return `
            <div class="card h-100 shadow-sm product-card product-card--standard" data-product-id="${product.id}">
                ${this.options.showCheckbox ? this.getCheckboxHTML() : ''}
                
                <div class="ratio ratio-16x9 bg-light product-card__image">
                    ${this.getImageHTML()}
                </div>
                
                <div class="card-body product-card__body">
                    <h5 class="card-title product-card__title">
                        ${product.title || `Product ${product.id}`}
                    </h5>
                    
                    <p class="card-text text-muted small product-card__prompt">
                        ${this.truncateText(product.prompt || '', 80)}
                    </p>
                    
                    <div class="text-muted small mb-3 product-card__metadata">
                        <div>${product.provider} - ${product.model_name}</div>
                        <div>${this.formatDate(product.created_at)}</div>
                        ${product.width && product.height ? `<div>${product.width}×${product.height}</div>` : ''}
                    </div>
                    
                    ${this.options.showActions ? this.getActionsHTML() : ''}
                </div>
            </div>
        `;
    }

    /**
     * Detailed variant - full information display
     */
    getDetailedHTML() {
        // Future implementation for search results, etc.
        return this.getStandardHTML();
    }

    /**
     * Generate checkbox HTML
     */
    getCheckboxHTML() {
        return `
            <div class="position-absolute top-0 start-0 p-2 product-card__checkbox" style="z-index: 10;">
                <input type="checkbox" class="form-check-input product-checkbox" 
                       value="${this.product.id}" 
                       id="product-${this.product.id}">
            </div>
        `;
    }

    /**
     * Generate image HTML
     */
    getImageHTML() {
        const product = this.product;
        if (product.file_url) {
            return `
                <img src="${product.file_url}" 
                     alt="${product.title || 'Generated product'}" 
                     class="card-img-top object-fit-cover product-card__img"
                     loading="lazy">
            `;
        } else {
            return `
                <div class="d-flex align-items-center justify-content-center text-muted product-card__placeholder">
                    <span>${(product.product_type || 'Product').charAt(0).toUpperCase() + (product.product_type || 'Product').slice(1)} Preview</span>
                </div>
            `;
        }
    }

    /**
     * Generate overlay HTML for compact cards
     */
    getOverlayHTML() {
        if (this.variant !== 'compact') return '';
        
        return `
            <div class="product-card__overlay">
                <div class="product-card__overlay-content">
                    <div class="product-card__overlay-title">${this.product.title || `Product ${this.product.id}`}</div>
                    <div class="product-card__overlay-actions">
                        <button class="btn btn-sm btn-primary" data-action="view">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-success" data-action="download">
                            <i class="bi bi-download"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generate actions HTML for standard cards
     */
    getActionsHTML() {
        if (!this.options.showActions) return '';
        
        return `
            <div class="d-grid gap-2 product-card__actions">
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm btn-primary" data-action="view">
                        <i class="bi bi-eye"></i> View
                    </button>
                    <button type="button" class="btn btn-sm btn-success" data-action="download">
                        <i class="bi bi-download"></i> Download
                    </button>
                </div>
                
                ${this.options.showDelete ? `
                    <button type="button" class="btn btn-sm btn-danger w-100" 
                            data-action="delete"
                            data-product-id="${this.product.id}" 
                            data-product-title="${this.product.title || `Product ${this.product.id}`}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                ` : ''}
            </div>
        `;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (!this.element) return;

        const card = this.element.querySelector('.product-card');
        const checkbox = this.element.querySelector('.product-checkbox');
        const image = this.element.querySelector('.product-card__img, .product-card__placeholder');

        // Card click handling
        if (card) {
            card.addEventListener('click', (e) => this.handleCardClick(e));
        }

        // Checkbox handling
        if (checkbox) {
            checkbox.addEventListener('change', (e) => this.handleCheckboxChange(e));
        }

        // Image click handling
        if (image) {
            image.addEventListener('click', (e) => this.handleImageClick(e));
        }

        // Action button handling
        this.element.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                this.handleActionClick(e);
            }
        });
    }

    /**
     * Handle card click events
     */
    handleCardClick(e) {
        // Don't handle if clicking on interactive elements
        if (e.target.matches('input, button, a, [data-action]') || 
            e.target.closest('button, a, [data-action], .product-card__actions')) {
            return;
        }

        switch (this.options.clickAction) {
            case 'select':
                this.toggleSelection();
                break;
            case 'modal':
                // Only open modal if clicking on image or card body, not buttons
                if (e.target.matches('.product-card__img, .product-card__placeholder') || 
                    e.target.closest('.product-card__body')) {
                    this.openModal();
                }
                break;
            case 'navigate':
                this.navigate();
                break;
        }
    }

    /**
     * Handle checkbox change
     */
    handleCheckboxChange(e) {
        this.selected = e.target.checked;
        this.updateSelectionState();
        
        if (this.collection) {
            this.collection.onSelectionChanged(this);
        }
    }

    /**
     * Handle image click
     */
    handleImageClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (this.variant === 'compact') {
            // For compact cards, image click opens modal
            this.openModal();
        } else {
            // For other variants, use configured click action
            this.handleCardClick(e);
        }
    }

    /**
     * Handle action button clicks
     */
    handleActionClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const action = e.target.getAttribute('data-action') || e.target.closest('[data-action]')?.getAttribute('data-action');
        
        switch (action) {
            case 'view':
                this.openModal();
                break;
            case 'download':
                this.download();
                break;
            case 'delete':
                this.delete();
                break;
        }
    }

    /**
     * Toggle selection state
     */
    toggleSelection() {
        this.setSelected(!this.selected);
    }

    /**
     * Set selection state
     */
    setSelected(selected) {
        this.selected = selected;
        const checkbox = this.element?.querySelector('.product-checkbox');
        if (checkbox) {
            checkbox.checked = selected;
        }
        this.updateSelectionState();
        
        if (this.collection) {
            this.collection.onSelectionChanged(this);
        }
    }

    /**
     * Update visual selection state
     */
    updateSelectionState() {
        if (!this.element) return;
        
        const card = this.element.querySelector('.product-card');
        if (card) {
            card.classList.toggle('product-card--selected', this.selected);
        }
    }

    /**
     * Open product in modal
     */
    openModal() {
        if (this.collection) {
            this.collection.onProductModalOpen(this);
        } else {
            // If no collection, open modal with just this product
            if (window.productViewerModal) {
                window.productViewerModal.open(this.product.id, {
                    context: 'single',
                    productList: [this.product]
                });
            }
        }
    }

    /**
     * Navigate to product detail page
     */
    navigate() {
        window.open(`/products/${this.product.id}/`, '_blank');
    }

    /**
     * Download product
     */
    download() {
        // Always use Django download endpoint for now to avoid CORS issues
        const link = document.createElement('a');
        link.href = `/products/${this.product.id}/download/`;
        link.download = '';
        link.target = '_blank'; // Open in new tab to avoid navigation issues
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * Delete product
     */
    delete() {
        if (this.collection) {
            this.collection.deleteProduct(this);
        }
    }

    /**
     * Utility: Truncate text
     */
    truncateText(text, length) {
        return text.length > length ? text.substring(0, length) + '...' : text;
    }

    /**
     * Utility: Format date
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Update product data
     */
    updateProduct(newProduct) {
        this.product = { ...this.product, ...newProduct };
        if (this.element) {
            const newElement = this.render();
            this.element.replaceWith(newElement);
        }
    }

    /**
     * Destroy the card and clean up
     */
    destroy() {
        if (this.element) {
            this.element.remove();
            this.element = null;
        }
        this.collection = null;
    }
}

class ProductCollection {
    constructor(container, layout = 'grid', options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.layout = layout; // 'grid', 'strip', 'list', 'masonry'
        this.options = {
            selectable: false,
            showBulkActions: false,
            cardVariant: 'standard',
            cardOptions: {},
            ...options
        };
        this.products = [];
        this.productCards = new Map(); // Map of product.id -> ProductCard
        this.selectedProducts = new Set();
        this.filters = {};
        this.sortBy = 'created_at';
        this.sortOrder = 'desc';
        
        this.init();
    }

    /**
     * Initialize the collection
     */
    init() {
        if (!this.container) {
            console.error('ProductCollection: Container not found');
            return;
        }

        this.container.classList.add('product-collection', `product-collection--${this.layout}`);
        
        // Create collection structure
        this.createCollectionHTML();
        
        // Setup event delegation
        this.setupEventHandlers();
    }

    /**
     * Create the collection HTML structure
     */
    createCollectionHTML() {
        this.container.innerHTML = `
            ${this.options.showBulkActions ? this.getBulkActionsHTML() : ''}
            <div class="product-collection__content">
                <div class="product-collection__grid ${this.getGridClass()}">
                    <!-- Products will be inserted here -->
                </div>
                <div class="product-collection__empty" style="display: none;">
                    <div class="text-center py-4 text-muted">
                        <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                        <div class="mt-2">No products to display</div>
                    </div>
                </div>
                <div class="product-collection__loading" style="display: none;">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div class="mt-2 text-muted">Loading products...</div>
                    </div>
                </div>
            </div>
        `;

        this.gridElement = this.container.querySelector('.product-collection__grid');
        this.emptyElement = this.container.querySelector('.product-collection__empty');
        this.loadingElement = this.container.querySelector('.product-collection__loading');
    }

    /**
     * Get CSS class for grid layout
     */
    getGridClass() {
        switch (this.layout) {
            case 'strip':
                return 'row g-2 flex-nowrap';
            case 'grid':
                return 'row g-3';
            case 'list':
                return 'list-group';
            case 'masonry':
                return 'row g-3 masonry-grid';
            default:
                return 'row g-3';
        }
    }

    /**
     * Get bulk actions HTML
     */
    getBulkActionsHTML() {
        return `
            <div class="product-collection__bulk-actions mb-3">
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm btn-outline-primary" data-action="select-all">
                        <i class="bi bi-check2-square"></i> Select All
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-action="deselect-all" style="display: none;">
                        <i class="bi bi-square"></i> Deselect All
                    </button>
                    <button type="button" class="btn btn-sm btn-success" data-action="bulk-download" disabled>
                        <i class="bi bi-download"></i> Download Selected
                    </button>
                    <button type="button" class="btn btn-sm btn-danger" data-action="bulk-delete" disabled>
                        <i class="bi bi-trash"></i> Delete Selected
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Setup event handlers
     */
    setupEventHandlers() {
        // Handle bulk action clicks
        this.container.addEventListener('click', (e) => {
            const action = e.target.getAttribute('data-action') || e.target.closest('[data-action]')?.getAttribute('data-action');
            if (action) {
                this.handleBulkAction(action, e);
            }
        });
    }

    /**
     * Load products into the collection
     */
    loadProducts(products) {
        this.products = products || [];
        this.render();
    }

    /**
     * Add a single product
     */
    addProduct(product, prepend = false) {
        if (prepend) {
            this.products.unshift(product);
        } else {
            this.products.push(product);
        }
        this.render();
    }

    /**
     * Remove a product
     */
    removeProduct(productId) {
        this.products = this.products.filter(p => p.id !== productId);
        const card = this.productCards.get(productId);
        if (card) {
            card.destroy();
            this.productCards.delete(productId);
        }
        this.selectedProducts.delete(productId);
        this.updateBulkActionStates();
        this.render();
    }

    /**
     * Render the collection
     */
    render() {
        if (!this.gridElement) return;

        this.showLoading(false);

        // Clear existing cards
        this.productCards.forEach(card => card.destroy());
        this.productCards.clear();
        this.gridElement.innerHTML = '';

        if (this.products.length === 0) {
            this.showEmpty(true);
            return;
        }

        this.showEmpty(false);

        // Apply filters and sorting
        const filteredProducts = this.getFilteredAndSortedProducts();

        // Create and render product cards
        filteredProducts.forEach(product => {
            const cardOptions = {
                showCheckbox: this.options.selectable,
                ...this.options.cardOptions
            };

            const card = new ProductCard(product, this.options.cardVariant, cardOptions);
            card.collection = this;
            
            this.productCards.set(product.id, card);
            
            const cardElement = card.render();
            this.gridElement.appendChild(cardElement);
        });

        this.updateBulkActionStates();
    }

    /**
     * Get filtered and sorted products
     */
    getFilteredAndSortedProducts() {
        let filtered = [...this.products];

        // Apply filters
        Object.entries(this.filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                filtered = filtered.filter(product => {
                    if (typeof value === 'string') {
                        return product[key]?.toLowerCase().includes(value.toLowerCase());
                    }
                    return product[key] === value;
                });
            }
        });

        // Apply sorting
        filtered.sort((a, b) => {
            let aVal = a[this.sortBy];
            let bVal = b[this.sortBy];

            // Handle dates
            if (this.sortBy.includes('_at') || this.sortBy.includes('date')) {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }

            if (this.sortOrder === 'desc') {
                return bVal > aVal ? 1 : -1;
            } else {
                return aVal > bVal ? 1 : -1;
            }
        });

        return filtered;
    }

    /**
     * Show/hide loading state
     */
    showLoading(show) {
        if (this.loadingElement) {
            this.loadingElement.style.display = show ? 'block' : 'none';
        }
        if (this.gridElement) {
            this.gridElement.style.display = show ? 'none' : 'block';
        }
    }

    /**
     * Show/hide empty state
     */
    showEmpty(show) {
        if (this.emptyElement) {
            this.emptyElement.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * Handle selection changes
     */
    onSelectionChanged(card) {
        if (card.selected) {
            this.selectedProducts.add(card.product.id);
        } else {
            this.selectedProducts.delete(card.product.id);
        }
        this.updateBulkActionStates();
    }

    /**
     * Handle product modal open
     */
    onProductModalOpen(card) {
        // Open modal with collection context for navigation
        if (window.productViewerModal) {
            const contextName = this.layout === 'strip' ? 'order' : 'inventory';
            window.productViewerModal.open(card.product.id, {
                context: contextName,
                productList: this.products
            });
        }
        
        // Also emit event for other listeners
        this.container.dispatchEvent(new CustomEvent('productModalOpen', {
            detail: { product: card.product, collection: this }
        }));
    }

    /**
     * Handle bulk actions
     */
    handleBulkAction(action, event) {
        switch (action) {
            case 'select-all':
                this.selectAll();
                break;
            case 'deselect-all':
                this.deselectAll();
                break;
            case 'bulk-download':
                this.bulkDownload();
                break;
            case 'bulk-delete':
                this.bulkDelete();
                break;
        }
    }

    /**
     * Select all products
     */
    selectAll() {
        this.productCards.forEach(card => card.setSelected(true));
        this.updateBulkActionStates();
    }

    /**
     * Deselect all products
     */
    deselectAll() {
        this.productCards.forEach(card => card.setSelected(false));
        this.selectedProducts.clear();
        this.updateBulkActionStates();
    }

    /**
     * Bulk download selected products
     */
    bulkDownload() {
        const selectedIds = Array.from(this.selectedProducts);
        if (selectedIds.length === 0) return;

        if (selectedIds.length === 1) {
            // For single product, use individual download
            const productCard = this.productCards.get(selectedIds[0]);
            if (productCard) {
                productCard.download();
            }
            return;
        }

        // For multiple products, create a zip file
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());
        selectedIds.forEach(id => {
            formData.append('product_ids', id);
        });

        // Create a temporary form to submit the download request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/products/bulk-download/';
        form.style.display = 'none';

        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = this.getCSRFToken();
        form.appendChild(csrfInput);

        // Add product IDs
        selectedIds.forEach(id => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'product_ids';
            input.value = id;
            form.appendChild(input);
        });

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

        // Show notification
        if (window.ToastNotification) {
            ToastNotification.success(
                `Preparing zip file with ${selectedIds.length} product(s)...`,
                'Download Started'
            );
        }
    }

    /**
     * Bulk delete selected products
     */
    bulkDelete() {
        const selectedIds = Array.from(this.selectedProducts);
        if (selectedIds.length === 0) return;

        const confirmationText = `Are you sure you want to delete ${selectedIds.length} product(s)? This action cannot be undone.`;
        if (!confirm(confirmationText)) {
            return;
        }

        // Call API to delete products
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());
        selectedIds.forEach(id => {
            formData.append('product_ids', id);
        });

        fetch('/products/bulk-delete/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove products from collection
                selectedIds.forEach(id => this.removeProduct(id));
                
                if (window.ToastNotification) {
                    ToastNotification.success(
                        data.message || `Successfully deleted ${selectedIds.length} product(s).`,
                        'Products Deleted'
                    );
                }
            } else {
                if (window.ToastNotification) {
                    ToastNotification.error(
                        data.message || 'Failed to delete products.',
                        'Delete Failed'
                    );
                }
            }
        })
        .catch(error => {
            console.error('Error deleting products:', error);
            if (window.ToastNotification) {
                ToastNotification.error(
                    'An error occurred while deleting products. Please try again.',
                    'Network Error'
                );
            }
        });
    }

    /**
     * Delete a single product
     */
    deleteProduct(card) {
        const productTitle = card.product.title || `Product ${card.product.id}`;
        
        if (!confirm(`Are you sure you want to delete "${productTitle}"? This action cannot be undone.`)) {
            return;
        }

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        fetch(`/products/${card.product.id}/delete/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.removeProduct(card.product.id);
                
                if (window.ToastNotification) {
                    ToastNotification.success(
                        data.message || `"${productTitle}" has been deleted.`,
                        'Product Deleted'
                    );
                }
            } else {
                if (window.ToastNotification) {
                    ToastNotification.error(
                        data.message || 'Failed to delete product.',
                        'Delete Failed'
                    );
                }
            }
        })
        .catch(error => {
            console.error('Error deleting product:', error);
            if (window.ToastNotification) {
                ToastNotification.error(
                    'An error occurred while deleting the product. Please try again.',
                    'Network Error'
                );
            }
        });
    }

    /**
     * Update bulk action button states
     */
    updateBulkActionStates() {
        if (!this.options.showBulkActions) return;

        const selectedCount = this.selectedProducts.size;
        const totalCount = this.productCards.size;
        const anySelected = selectedCount > 0;
        const allSelected = selectedCount === totalCount && totalCount > 0;

        // Update button states
        const selectAllBtn = this.container.querySelector('[data-action="select-all"]');
        const deselectAllBtn = this.container.querySelector('[data-action="deselect-all"]');
        const bulkDownloadBtn = this.container.querySelector('[data-action="bulk-download"]');
        const bulkDeleteBtn = this.container.querySelector('[data-action="bulk-delete"]');

        if (selectAllBtn) selectAllBtn.style.display = allSelected ? 'none' : 'inline-block';
        if (deselectAllBtn) deselectAllBtn.style.display = allSelected ? 'inline-block' : 'none';
        if (bulkDownloadBtn) {
            bulkDownloadBtn.disabled = !anySelected;
            bulkDownloadBtn.innerHTML = anySelected ? 
                `<i class="bi bi-download"></i> Download (${selectedCount})` :
                '<i class="bi bi-download"></i> Download Selected';
        }
        if (bulkDeleteBtn) {
            bulkDeleteBtn.disabled = !anySelected;
            bulkDeleteBtn.innerHTML = anySelected ? 
                `<i class="bi bi-trash"></i> Delete (${selectedCount})` :
                '<i class="bi bi-trash"></i> Delete Selected';
        }
    }

    /**
     * Set filters
     */
    setFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        this.render();
    }

    /**
     * Set sorting
     */
    setSorting(sortBy, sortOrder = 'desc') {
        this.sortBy = sortBy;
        this.sortOrder = sortOrder;
        this.render();
    }

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        // Try multiple ways to get CSRF token
        let token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            token = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
        }
        if (!token) {
            // Try to get from cookie
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    token = value;
                    break;
                }
            }
        }
        return token || '';
    }

    /**
     * Destroy the collection
     */
    destroy() {
        this.productCards.forEach(card => card.destroy());
        this.productCards.clear();
        this.selectedProducts.clear();
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export for use in other scripts
window.ProductCard = ProductCard;
window.ProductCollection = ProductCollection;