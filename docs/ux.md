# Art Factory User Experience

This document defines the user interface requirements, layouts, and interaction patterns for Art Factory.

## Design Principles

### Modern Responsive Design
- Optimized for desktop use
- Clean, professional interface
- Consistent design patterns throughout
- Progressive disclosure of complexity

### User-Centered Approach
- Minimize cognitive load for common tasks
- Clear visual hierarchy
- Immediate feedback for user actions
- Graceful error handling with helpful messages

## Application Structure

### Navigation
The application uses a header navigation with main sections:

- **Projects**: Project management and overview (default home page)
- **Order**: Place new orders and view recent activity
- **Production**: Monitor generation progress and system status
- **Inventory**: Browse and manage generated products
- **Admin**: Settings, logs, and system management

### Common Page Elements

#### Header
- Fixed to top of window, does not scroll
- Application title "AI Art Factory" linking to home
- Horizontal navigation bar for main sections
- Optional status indicators (active generations, etc.)

#### Footer
- Fixed to bottom of browser window
- Copyright notice
- Version information
- Does not scroll with content

#### Error Handling
- Banner appears below header for errors
- Brief description with expandable details ("More"/"Less" toggle)
- Dismissible with "OK" button
- Contextual error messages within forms

## Main Sections

### Projects Section (Home Page)

**Purpose**: Primary entry point and organizational hub for all work

#### Projects Overview Page (`/` or `/projects/`)
**Layout**:
- Hero section with recent/active projects
- Grid of project cards showing:
  - Project name and description
  - Featured product thumbnails (3-4 images)
  - Order count and product count
  - Last activity timestamp
  - Status indicator (active/archived/completed)
  - Quick actions (view, edit, archive)
- "Create New Project" prominent button
- Search bar for finding projects
- Filter controls (status, date range)

**Actions**:
- Create new project with modal/inline form
- Click project card to view details
- Quick jump to order page with project context
- Edit project details inline
- Archive/restore projects
- Search across projects, orders, and products

#### All Projects Page (`/projects/all/`)
**Layout**:
- Traditional list/table view of all projects
- Columns: Name, Description, Status, Orders, Products, Created, Updated
- Sortable columns
- Pagination for large project lists
- Bulk operations toolbar

**Actions**:
- Same as overview but optimized for managing many projects
- Bulk archive/delete operations
- Export project list

#### Project Detail Page (`/projects/<id>/`)
**Layout**:
- Project header with name, description, status
- Statistics dashboard:
  - Total products generated
  - Total orders placed
  - Storage consumed
  - Generation time metrics
- Recent orders list with status
- Product gallery filtered to project
- Featured products management

**Actions**:
- Edit project details
- Manage featured products
- Create new order in project context
- View all products/orders
- Archive/delete project

### Order Section

**Purpose**: Place new orders and monitor recent activity

#### Layout Components

**Order Form** (top/left):
- Provider and model selection dropdown
- Dynamic parameter form based on selection
- Prompt text area with smart token support
- Advanced parameters (collapsible)
- "Place Order" button with validation

**Preview Area** (top/right):
- A place to show the outputs of the last generation when it is complete
- If we implement result streaming from the APIs, the product will be progressively rendered or have actual progress shown

**Recent Products** (Product Collection - Strip Layout)
- Horizontal strip of recently created products using compact Product Cards
- Updated live; when a new product is generated it is added to the left, and products are removed from the right
- Provides navigation context when opening the product viewer modal 


**Recent Orders List** (bottom/right):
- Shows: ID, model used, status, timestamp
- Expandable to show order items
- Status updates in real-time



#### Functionality
- Dynamic form field updates based on model selection
- Form validation with inline error messages
- Asynchronous order submission
- Real-time status updates
- Parameter preservation across form changes

### Production Section

**Purpose**: Monitor generation progress and system status

#### Production Summary
- Key metrics: incomplete orders, active workers
- System status indicators
- Recent activity overview

#### Active Orders
- List of orders in progress
- Progress indicators and status
- Estimated completion times
- Error states and retry options

#### System Status
- Background worker status
- API rate limit information
- Recent system events and logs

### Inventory Section

**Purpose**: Browse, manage, and organize generated products

#### Layout Components

**Product Display Area** (main area):
- Toggle between grid and list views
- Area controls:
  - View toggle (grid/list)
  - Sorting (latest, earliest, file size)
  - Grouping (none, project, order)
  - Filtering (all, images, videos, other)

**Product Detail Sidebar** (right side):
- Fixed to right side of screen
- Shows selected product details:
  - Large thumbnail (clickable for full view)
  - Prompt text (truncated with "more" option)
  - Metadata (type, date, size)
  - Input/output parameters (expandable)
  - Action buttons (download, reorder, delete)

**Product Viewer Modal**:
A sophisticated full-screen viewing experience for products:

**Core Features**:
- Full-screen dark modal overlay
- Maximum viewport utilization for image display
- Smooth zoom and pan functionality:
  - Mouse wheel zoom (10% - 500%)
  - Click and drag to pan when zoomed
  - Zoom controls with reset button
- Navigation between products in collection:
  - Previous/Next buttons with visual indicators
  - Keyboard arrow key navigation
  - Maintains collection context from entry point
- Collapsible information sidebar:
  - Product metadata and parameters
  - File information (dimensions, size, creation date)
  - Order and factory machine details
  - Action toolbar (download, favorite, regenerate, delete)
  - External toggle button for accessibility

**User Interactions**:
- Click on product card "View" button to open
- Escape key or close button to dismiss
- Browser back button integration (pending Issue #67)
- Arrow keys for product navigation
- Mouse wheel for zoom control
- Click and drag for panning zoomed images
- All actions provide immediate feedback

**Technical Implementation**:
- Overlays content rather than pushing layout
- Sidebar floats over image area when expanded
- Smart data fetching ensures all metadata available
- Responsive design adapts to screen size
- Accessibility features include ARIA labels and keyboard navigation

#### Product Grid View
- Responsive grid layout
- Product cards with:
  - Thumbnail image or type icon
  - Product type badge
  - Selection indicator
  - Hover tooltip with metadata
  - Quick action controls

#### Product List View
- Vertical list with:
  - Small thumbnail/icon
  - Product name and type
  - Creation date and file size
  - Quick action buttons
  - Selection checkbox

#### Functionality
- Product selection (single/multiple)
- Real-time updates for new products
- Smooth transitions for deletions
- Keyboard navigation (arrow keys, spacebar)
- Bulk operations on selected products

### Admin Section

**Purpose**: System configuration and monitoring

#### Settings
- API key management
- Default parameter configuration
- File storage settings
- Disk space monitoring
- System reset options

#### Events & Logs
- Recent system events
- Error logs and debugging information
- Event filtering and search
- System health monitoring

## Reusable Components

### Product Card
**Definition**: The visual representation of a product (image + optional metadata/actions)

**Variants**:
- **Compact**: Image only with hover overlay (used in thumbnail strips)
- **Standard**: Image + title + basic metadata (used in inventory grid)
- **Detailed**: Full information display (future use in search results)

**Features**:
- Thumbnail with type indicator
- Metadata overlay on hover
- Selection state visualization
- Quick action menu
- Consistent behavior across all contexts

### Product Collection
**Definition**: A container that manages and displays multiple Product Cards

**Layouts**:
- **Grid**: Responsive grid layout (inventory page)
- **Strip**: Horizontal scrolling strip (order page recent products)
- **List**: Vertical list with details (future search results)
- **Masonry**: Pinterest-style layout (future gallery view)

**Features**:
- Manages selection state across products
- Provides navigation context for viewer modal
- Handles filtering and sorting
- Supports bulk operations
- Real-time updates via WebSocket

### Parameter Form
- Dynamic field generation
- Smart token input with autocomplete
- Parameter validation and hints
- Collapsible advanced sections
- Template loading/saving

### Status Indicators
- Generation progress bars
- Real-time status badges
- Error state indicators
- System health indicators

## Interaction Patterns

### Selection
- Click product card/thumbnail to select
- Selected state clearly indicated
- Multi-select with Ctrl/Cmd+click
- Keyboard navigation with arrow keys

### Actions
- Primary actions prominently displayed
- Secondary actions in context menus
- Confirmation for destructive actions
- Undo capability where appropriate

### Real-time Updates
- Smooth animations for content changes
- Progress indicators for long operations
- Graceful handling of connection issues
- Clear feedback for user actions

## Accessibility

### Keyboard Navigation
- Tab order follows logical flow
- Arrow keys for grid/list navigation
- Spacebar for selection/activation
- Escape for modal dismissal

### Screen Reader Support
- Proper ARIA labels and roles
- Descriptive text for images
- Status announcements
- Form validation messages

### Visual Design
- Sufficient color contrast
- Clear visual hierarchy
- Consistent interaction patterns
- Responsive text sizing

## Performance Considerations

### Image Loading
- Lazy loading for large galleries
- Progressive image enhancement
- Thumbnail optimization
- Efficient caching strategies

### Interface Responsiveness
- Immediate UI feedback
- Non-blocking operations
- Progressive loading indicators
- Graceful degradation

### Memory Management
- Efficient DOM handling
- Image memory optimization
- Cleanup of unused resources
- Pagination for large datasets