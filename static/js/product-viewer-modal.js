class ProductViewerModal {
    constructor() {
        this.currentProduct = null;
        this.products = [];
        this.currentIndex = 0;
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.openingContext = null;
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.minZoom = 0.1;
        this.maxZoom = 5;
        
        this.modal = null;
        this.imageContainer = null;
        this.productImage = null;
        this.sidebar = null;
        this.thumbnailStrip = null;
        this.historyAdded = false;
        
        this.init();
    }
    
    init() {
        this.createModal();
        this.setupEventListeners();
    }
    
    createModal() {
        const modalHTML = `
            <div class="product-viewer-modal" id="productViewer" style="display: none;">
                <!-- Sidebar toggle button (always visible) -->
                <button class="sidebar-toggle-external btn btn-dark" aria-label="Toggle sidebar">
                    <i class="bi bi-chevron-right"></i>
                </button>
                
                <div class="viewer-container">
                    <!-- Main viewing area -->
                    <div class="viewer-main">
                        <!-- Navigation -->
                        <button class="nav-button nav-prev" aria-label="Previous" disabled>
                            <i class="bi bi-chevron-left"></i>
                        </button>
                        <button class="nav-button nav-next" aria-label="Next" disabled>
                            <i class="bi bi-chevron-right"></i>
                        </button>
                        
                        <!-- Image container -->
                        <div class="image-container">
                            <img class="product-image" alt="" style="display: none;">
                            <div class="loading-spinner">
                                <div class="spinner-border text-light" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Zoom controls -->
                        <div class="zoom-controls">
                            <button class="zoom-in btn btn-dark btn-sm" title="Zoom In">
                                <i class="bi bi-zoom-in"></i>
                            </button>
                            <button class="zoom-out btn btn-dark btn-sm" title="Zoom Out">
                                <i class="bi bi-zoom-out"></i>
                            </button>
                            <button class="zoom-reset btn btn-dark btn-sm" title="Reset">
                                <i class="bi bi-arrows-angle-expand"></i>
                            </button>
                            <span class="zoom-level badge bg-dark">100%</span>
                        </div>
                        
                        <!-- Close button -->
                        <button class="close-button btn btn-dark" aria-label="Close">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    
                    <!-- Information sidebar -->
                    <div class="viewer-sidebar">
                        <div class="sidebar-header">
                            <h3 class="mb-0">Product Details</h3>
                            <button class="sidebar-toggle btn btn-link text-light p-0">
                                <i class="bi bi-chevron-right"></i>
                            </button>
                        </div>
                        
                        <div class="sidebar-content">
                            <!-- Action buttons -->
                            <div class="action-buttons mb-3">
                                <button class="btn btn-primary btn-sm me-1 mb-1" data-action="download">
                                    <i class="bi bi-download"></i> Download
                                </button>
                                <button class="btn btn-outline-light btn-sm me-1 mb-1" data-action="favorite">
                                    <i class="bi bi-heart"></i> <span class="favorite-text">Favorite</span>
                                </button>
                                <button class="btn btn-outline-light btn-sm me-1 mb-1" data-action="regenerate">
                                    <i class="bi bi-arrow-repeat"></i> Regenerate
                                </button>
                                <button class="btn btn-outline-danger btn-sm mb-1" data-action="delete">
                                    <i class="bi bi-trash"></i> Delete
                                </button>
                            </div>
                            
                            <!-- Information sections -->
                            <div class="info-section mb-3">
                                <h4 class="h6 text-uppercase text-muted mb-2">Generation Parameters</h4>
                                <dl class="parameters-list mb-0">
                                    <!-- Dynamically populated -->
                                </dl>
                            </div>
                            
                            <div class="info-section mb-3">
                                <h4 class="h6 text-uppercase text-muted mb-2">File Information</h4>
                                <dl class="mb-0">
                                    <dt class="small">Dimensions</dt>
                                    <dd class="file-dimensions small text-muted mb-1"></dd>
                                    <dt class="small">File Size</dt>
                                    <dd class="file-size small text-muted mb-1"></dd>
                                    <dt class="small">Created</dt>
                                    <dd class="file-created small text-muted mb-0"></dd>
                                </dl>
                            </div>
                            
                            <div class="info-section">
                                <h4 class="h6 text-uppercase text-muted mb-2">Order Information</h4>
                                <dl class="mb-0">
                                    <dt class="small">Order ID</dt>
                                    <dd class="order-id small text-muted mb-1"></dd>
                                    <dt class="small">Factory Machine</dt>
                                    <dd class="factory-machine small text-muted mb-0"></dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Thumbnail strip (optional) -->
                <div class="thumbnail-strip" style="display: none;">
                    <div class="thumbnail-container">
                        <!-- Dynamically populated -->
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Cache DOM elements
        this.modal = document.getElementById('productViewer');
        this.imageContainer = this.modal.querySelector('.image-container');
        this.productImage = this.modal.querySelector('.product-image');
        this.sidebar = this.modal.querySelector('.viewer-sidebar');
        this.thumbnailStrip = this.modal.querySelector('.thumbnail-strip');
        this.loadingSpinner = this.modal.querySelector('.loading-spinner');
    }
    
    setupEventListeners() {
        // Close modal
        this.modal.querySelector('.close-button').addEventListener('click', () => {
            this.close();
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display !== 'none') {
                this.close();
            }
        });
        
        // Navigation
        this.modal.querySelector('.nav-prev').addEventListener('click', () => {
            this.navigate('prev');
        });
        
        this.modal.querySelector('.nav-next').addEventListener('click', () => {
            this.navigate('next');
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.modal.style.display === 'none') return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigate('prev');
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigate('next');
                    break;
            }
        });
        
        // Zoom controls
        this.modal.querySelector('.zoom-in').addEventListener('click', () => {
            this.setZoom(this.zoom * 1.2);
        });
        
        this.modal.querySelector('.zoom-out').addEventListener('click', () => {
            this.setZoom(this.zoom / 1.2);
        });
        
        this.modal.querySelector('.zoom-reset').addEventListener('click', () => {
            this.resetZoom();
        });
        
        // Mouse wheel zoom
        this.imageContainer.addEventListener('wheel', (e) => {
            if (this.modal.style.display === 'none') return;
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.setZoom(this.zoom * delta);
        });
        
        // Drag to pan
        this.setupPanControls();
        
        // Sidebar toggle
        this.modal.querySelector('.sidebar-toggle').addEventListener('click', () => {
            this.toggleSidebar();
        });
        
        // External sidebar toggle
        this.modal.querySelector('.sidebar-toggle-external').addEventListener('click', () => {
            this.toggleSidebar();
        });
        
        // Action buttons
        this.modal.querySelector('.action-buttons').addEventListener('click', (e) => {
            const action = e.target.closest('[data-action]');
            if (action) {
                this.handleAction(action.dataset.action);
            }
        });
        
        // Click outside image to close (on background)
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
        
        // Handle browser back button
        window.addEventListener('popstate', (e) => {
            if (this.modal.style.display !== 'none') {
                // If modal is open and user navigates back, close the modal
                // Prevent the history.back() call in removeHistoryState from causing issues
                if (!e.state || !e.state.modalOpen) {
                    this.closeWithoutHistory();
                }
            }
        });
    }
    
    setupPanControls() {
        this.imageContainer.addEventListener('mousedown', (e) => {
            if (this.zoom <= 1) return; // Only pan when zoomed in
            
            this.isDragging = true;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
            this.imageContainer.style.cursor = 'grabbing';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            
            const newPanX = e.clientX - this.startX;
            const newPanY = e.clientY - this.startY;
            
            // Apply boundary constraints
            const constraints = this.getPanConstraints();
            this.panX = Math.max(constraints.minX, Math.min(constraints.maxX, newPanX));
            this.panY = Math.max(constraints.minY, Math.min(constraints.maxY, newPanY));
            
            this.updateImageTransform();
        });
        
        document.addEventListener('mouseup', () => {
            if (this.isDragging) {
                this.isDragging = false;
                this.imageContainer.style.cursor = this.zoom > 1 ? 'grab' : 'default';
            }
        });
    }
    
    async open(productId, options = {}) {
        this.openingContext = options.context || 'single';
        this.products = options.productList || [productId];
        
        // Find the index of the current product
        this.currentIndex = this.products.findIndex(p => 
            (typeof p === 'object' ? p.id : p) === productId
        );
        
        if (this.currentIndex === -1) {
            this.currentIndex = 0;
        }
        
        // Show modal
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        
        // Add to browser history
        this.addHistoryState();
        
        // Load the product
        await this.loadProduct(this.products[this.currentIndex]);
        
        // Update navigation buttons
        this.updateNavigationButtons();
        
        // Initialize sidebar positioning
        this.handleSidebarResize();
        
        // Show thumbnail strip if multiple products
        if (this.products.length > 1) {
            this.showThumbnailStrip();
        }
        
        // Preload adjacent images
        this.preloadAdjacent();
    }
    
    close() {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // Reset zoom and pan
        this.resetZoom();
        
        // Hide thumbnail strip
        this.thumbnailStrip.style.display = 'none';
        
        // Clear current product
        this.currentProduct = null;
        this.products = [];
        
        // Remove from history if we added it
        this.removeHistoryState();
    }
    
    closeWithoutHistory() {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // Reset zoom and pan
        this.resetZoom();
        
        // Hide thumbnail strip
        this.thumbnailStrip.style.display = 'none';
        
        // Clear current product
        this.currentProduct = null;
        this.products = [];
        
        // Mark history as removed since user already navigated back
        this.historyAdded = false;
    }
    
    async loadProduct(product) {
        this.showLoading();
        
        try {
            let productData;
            let productId;
            
            // Get product ID
            if (typeof product === 'object') {
                productId = product.id;
            } else {
                productId = product;
            }
            
            // Always fetch full product data from API to ensure we have all fields
            const response = await fetch(`/api/products/${productId}/`);
            if (!response.ok) throw new Error('Failed to load product');
            productData = await response.json();
            
            this.currentProduct = productData;
            
            // Load image
            await this.loadImage(productData.file_url || productData.file_path);
            
            // Update sidebar information
            this.updateSidebar(productData);
            
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading product:', error);
            this.hideLoading();
            // Show error state
            this.showError('Failed to load product');
        }
    }
    
    loadImage(imageSrc) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                this.productImage.src = imageSrc;
                this.productImage.style.display = 'block';
                this.resetZoom();
                resolve();
            };
            img.onerror = reject;
            img.src = imageSrc;
        });
    }
    
    showLoading() {
        this.loadingSpinner.style.display = 'flex';
        this.productImage.style.display = 'none';
    }
    
    hideLoading() {
        this.loadingSpinner.style.display = 'none';
    }
    
    showError(message) {
        // Simple error display - could be enhanced
        this.imageContainer.innerHTML = `
            <div class="error-message text-center text-light p-4">
                <i class="bi bi-exclamation-triangle fs-1 mb-3"></i>
                <p>${message}</p>
            </div>
        `;
    }
    
    navigate(direction) {
        if (this.products.length <= 1) return;
        
        const newIndex = direction === 'next' 
            ? Math.min(this.currentIndex + 1, this.products.length - 1)
            : Math.max(this.currentIndex - 1, 0);
            
        if (newIndex !== this.currentIndex) {
            this.currentIndex = newIndex;
            this.loadProduct(this.products[this.currentIndex]);
            this.updateNavigationButtons();
            this.preloadAdjacent();
        }
    }
    
    updateNavigationButtons() {
        const prevBtn = this.modal.querySelector('.nav-prev');
        const nextBtn = this.modal.querySelector('.nav-next');
        
        prevBtn.disabled = this.currentIndex === 0;
        nextBtn.disabled = this.currentIndex === this.products.length - 1;
        
        // Show/hide buttons based on whether we have multiple products
        if (this.products.length <= 1) {
            prevBtn.style.display = 'none';
            nextBtn.style.display = 'none';
        } else {
            prevBtn.style.display = 'block';
            nextBtn.style.display = 'block';
        }
    }
    
    setZoom(newZoom) {
        this.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, newZoom));
        this.updateImageTransform();
        this.updateZoomControls();
        
        // Update cursor
        this.imageContainer.style.cursor = this.zoom > 1 ? 'grab' : 'default';
    }
    
    resetZoom() {
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.updateImageTransform();
        this.updateZoomControls();
        this.imageContainer.style.cursor = 'default';
    }
    
    updateImageTransform() {
        this.productImage.style.transform = 
            `scale(${this.zoom}) translate(${this.panX}px, ${this.panY}px)`;
    }
    
    getPanConstraints() {
        if (this.zoom <= 1) {
            return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
        }
        
        const containerRect = this.imageContainer.getBoundingClientRect();
        const img = this.productImage;
        
        // Get the actual displayed dimensions of the image
        const imgRect = img.getBoundingClientRect();
        const displayedWidth = imgRect.width * this.zoom;
        const displayedHeight = imgRect.height * this.zoom;
        
        // Calculate the maximum pan distances to keep image edges within view
        // These values ensure the edge of the image cannot go past the center of the viewport
        const maxPanX = Math.max(0, (displayedWidth - containerRect.width) / (2 * this.zoom));
        const maxPanY = Math.max(0, (displayedHeight - containerRect.height) / (2 * this.zoom));
        
        return {
            minX: -maxPanX,
            maxX: maxPanX,
            minY: -maxPanY,
            maxY: maxPanY
        };
    }
    
    updateZoomControls() {
        const zoomLevel = this.modal.querySelector('.zoom-level');
        zoomLevel.textContent = `${Math.round(this.zoom * 100)}%`;
        
        // Disable buttons at limits
        this.modal.querySelector('.zoom-in').disabled = this.zoom >= this.maxZoom;
        this.modal.querySelector('.zoom-out').disabled = this.zoom <= this.minZoom;
    }
    
    updateSidebar(product) {
        // Update parameters
        const paramsList = this.modal.querySelector('.parameters-list');
        paramsList.innerHTML = '';
        
        if (product.parameters) {
            const params = typeof product.parameters === 'string' 
                ? JSON.parse(product.parameters) 
                : product.parameters;
                
            if (params && typeof params === 'object' && Object.keys(params).length > 0) {
                Object.entries(params).forEach(([key, value]) => {
                    if (value !== null && value !== undefined && value !== '') {
                        paramsList.innerHTML += `
                            <dt class="small">${this.formatParameterName(key)}</dt>
                            <dd class="small mb-1">${this.formatParameterValue(value)}</dd>
                        `;
                    }
                });
            } else {
                paramsList.innerHTML = '<dd class="small text-muted mb-0">No parameters available</dd>';
            }
        } else {
            paramsList.innerHTML = '<dd class="small text-muted mb-0">No parameters available</dd>';
        }
        
        // Update file information
        this.modal.querySelector('.file-dimensions').textContent = 
            product.width && product.height ? `${product.width} × ${product.height}` : 'Not available';
        this.modal.querySelector('.file-size').textContent = 
            product.file_size ? this.formatFileSize(product.file_size) : 'Not available';
        this.modal.querySelector('.file-created').textContent = 
            product.created_at ? new Date(product.created_at).toLocaleString() : 'Not available';
            
        // Update order information
        this.modal.querySelector('.order-id').textContent = product.order_id || 'Not linked to order';
        this.modal.querySelector('.factory-machine').textContent = 
            product.factory_machine_definition || 'Not available';
            
        // Update favorite button state
        const favoriteBtn = this.modal.querySelector('[data-action="favorite"]');
        const favoriteText = favoriteBtn.querySelector('.favorite-text');
        if (product.is_favorite) {
            favoriteBtn.classList.remove('btn-outline-light');
            favoriteBtn.classList.add('btn-warning');
            favoriteText.textContent = 'Unfavorite';
        } else {
            favoriteBtn.classList.remove('btn-warning');
            favoriteBtn.classList.add('btn-outline-light');
            favoriteText.textContent = 'Favorite';
        }
    }
    
    formatParameterName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatParameterValue(value) {
        if (Array.isArray(value)) {
            return value.join(', ');
        }
        if (typeof value === 'string' && value.length > 100) {
            return value.substring(0, 100) + '...';
        }
        return String(value);
    }
    
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    toggleSidebar() {
        const isCollapsed = this.sidebar.classList.contains('collapsed');
        this.sidebar.classList.toggle('collapsed');
        
        // Update both toggle buttons
        const icon = this.modal.querySelector('.sidebar-toggle i');
        const externalIcon = this.modal.querySelector('.sidebar-toggle-external i');
        
        if (isCollapsed) {
            // Was collapsed, now expanding - show collapse icons for next action
            icon.classList.remove('bi-chevron-left');
            icon.classList.add('bi-chevron-right');
            // External button: now visible, show right arrow (to collapse next time)
            externalIcon.classList.remove('bi-chevron-left');
            externalIcon.classList.add('bi-chevron-right');
        } else {
            // Was visible, now collapsing - show expand icons for next action 
            icon.classList.remove('bi-chevron-right');
            icon.classList.add('bi-chevron-left');
            // External button: now collapsed, show left arrow (to expand next time)
            externalIcon.classList.remove('bi-chevron-right');
            externalIcon.classList.add('bi-chevron-left');
        }
        
        // Trigger resize of image display
        this.handleSidebarResize();
    }
    
    handleSidebarResize() {
        // Add a small delay to allow CSS transition to complete
        setTimeout(() => {
            const isCollapsed = this.sidebar.classList.contains('collapsed');
            const viewerMain = this.modal.querySelector('.viewer-main');
            const externalToggle = this.modal.querySelector('.sidebar-toggle-external');
            
            if (isCollapsed) {
                // Sidebar is collapsed
                // Position external button at the right edge of viewport
                externalToggle.style.right = '10px';
                externalToggle.style.borderRadius = '0 4px 4px 0';
            } else {
                // Sidebar is visible
                // Position external button next to sidebar (left side of sidebar)
                externalToggle.style.right = '350px';
                externalToggle.style.borderRadius = '4px 0 0 4px';
            }
            
            // Ensure button is always visible
            externalToggle.style.display = 'flex';
            externalToggle.style.visibility = 'visible';
            externalToggle.style.opacity = '1';
        }, 150); // Match CSS transition duration
    }
    
    async handleAction(action) {
        if (!this.currentProduct) return;
        
        switch (action) {
            case 'download':
                await this.downloadProduct();
                break;
            case 'favorite':
                await this.toggleFavorite();
                break;
            case 'regenerate':
                await this.regenerateProduct();
                break;
            case 'delete':
                await this.deleteProduct();
                break;
        }
    }
    
    async downloadProduct() {
        if (!this.currentProduct) return;
        
        try {
            // Use the same download approach as ProductCard for consistency
            const link = document.createElement('a');
            link.href = `/products/${this.currentProduct.id}/download/`;
            link.download = '';
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Download failed:', error);
        }
    }
    
    async toggleFavorite() {
        // Implementation depends on API structure
        console.log('Toggle favorite for product:', this.currentProduct.id);
    }
    
    async regenerateProduct() {
        // Implementation depends on order system
        console.log('Regenerate product:', this.currentProduct.id);
    }
    
    async deleteProduct() {
        if (!confirm('Are you sure you want to delete this product?')) return;
        
        try {
            const csrfToken = this.getCSRFToken();
            if (!csrfToken) {
                console.error('CSRF token not found');
                alert('Security token not found. Please refresh the page and try again.');
                return;
            }
            
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            const response = await fetch(`/products/${this.currentProduct.id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Remove from products array
                this.products.splice(this.currentIndex, 1);
                
                if (this.products.length === 0) {
                    // No more products, close modal
                    this.close();
                } else {
                    // Adjust index if necessary and load next product
                    if (this.currentIndex >= this.products.length) {
                        this.currentIndex = this.products.length - 1;
                    }
                    await this.loadProduct(this.products[this.currentIndex]);
                    this.updateNavigationButtons();
                }
                
                // Dispatch event for other components to update
                document.dispatchEvent(new CustomEvent('productDeleted', {
                    detail: { productId: this.currentProduct.id }
                }));
                
                // Show success notification if available
                if (window.ToastNotification) {
                    ToastNotification.success(data.message || 'Product deleted successfully', 'Success');
                }
            } else {
                const errorData = await response.json();
                console.error('Delete failed:', response.status, errorData);
                alert(errorData.message || 'Failed to delete product. Please try again.');
            }
        } catch (error) {
            console.error('Delete failed:', error);
            alert('An error occurred while deleting the product. Please try again.');
        }
    }
    
    getCSRFToken() {
        // Try form input first
        let token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        // Try meta tag
        if (!token) {
            token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        }
        
        // Try cookie
        if (!token) {
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
    
    showThumbnailStrip() {
        // Implement thumbnail strip for navigation
        this.thumbnailStrip.style.display = 'block';
        // Implementation would populate thumbnails
    }
    
    preloadAdjacent() {
        // Preload previous and next images for smooth navigation
        const toPreload = [];
        if (this.currentIndex > 0) {
            toPreload.push(this.products[this.currentIndex - 1]);
        }
        if (this.currentIndex < this.products.length - 1) {
            toPreload.push(this.products[this.currentIndex + 1]);
        }
        
        toPreload.forEach(product => {
            const img = new Image();
            const imageSrc = typeof product === 'object' 
                ? (product.file_url || product.file_path) 
                : `/media/products/${product}.jpg`; // Fallback pattern
            img.src = imageSrc;
        });
    }
    
    addHistoryState() {
        if (!this.historyAdded) {
            // Push a new state that we can detect on popstate
            window.history.pushState({ modalOpen: true }, '', window.location.href);
            this.historyAdded = true;
        }
    }
    
    removeHistoryState() {
        if (this.historyAdded) {
            // Replace current state instead of going back to avoid navigation
            window.history.replaceState(null, '', window.location.href);
            this.historyAdded = false;
        }
    }
}

// Global instance
window.productViewerModal = new ProductViewerModal();