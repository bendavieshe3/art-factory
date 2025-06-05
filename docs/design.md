# AI Art Factory - Updated Comprehensive Design Document

## 1. Project Overview

AI Art Factory is a Django-first web application for managing AI-generated art using various providers like fal.ai, Replicate, and civitai. The project commits to leveraging Django's mature ecosystem and established patterns to minimize architectural complexity and accelerate development. It is designed for local single-user deployment.

## 2. Architecture

### 2.1 Technology Stack

#### Core Framework (Committed)
- **Backend**: Django 5.1+ (Python)
- **Database**: SQLite (development) → PostgreSQL (production migration path)
- **ORM**: Django's built-in ORM
- **Development Server**: Django's built-in development server

#### Implementation Decisions (To Be Made)
- **Real-time Communication**: Options include Django Channels (WebSockets), Server-Sent Events, or AJAX polling
- **Background Tasks**: Options include Celery, Django-RQ, or Django's async views
- **Frontend Approach**: Django templates + JavaScript vs. more sophisticated SPA approach
- **CSS Framework**: Tailwind, Bootstrap, or custom CSS
- **API Integration**: Provider-specific client libraries (fal-client, etc.)

### 2.2 Project Structure



```
ai_art_factory/
├── ai_art_factory/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── main/
│   ├── admin.py
│   ├── api_views.py
│   ├── apps.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── factory_machines.py
│   │   ├── orders.py
│   │   └── products.py
│   ├── tests/
│   │   ├── test_factory_machines.py
│   │   └── test_product_model.py
│   ├── views.py
│   ├── production_views.py
│   ├── settings_views.py
│   └── logger.py
├── templates/
│   ├── base.html
│   └── main/
│       ├── order.html
│       ├── inventory.html
│       ├── production.html
│       └── settings.html
├── media/
├── manage.py
└── requirements.txt
```

## 3. Key Components

### 3.1 FactoryMachine Classes

The `factory_machines.py` file contains the core logic for different types of image generation:

1. `BaseFactoryMachine`: An abstract base class defining the common interface and functionality.
2. `FalTxt2ImgMachine`: Implements common functionality for Fal.ai text-to-image generation machines.
3. Specific implementation classes (e.g., `SDXLTxt2ImgMachine`, `DreamShaperTxt2ImgMachine`, `FluxTxt2ImgMachine`): Define specific parameters and operation types for each Fal.ai model.

Key features:
- Parameter validation
- Execution logic with proper error handling
- Integration with the FactoryMachineInstance model for tracking machine usage
- Standardized return structure (ExecutionResult) for consistent handling of generated products

### 3.2 Models

Key models are organized in separate files under the `main/models/` directory

Key models include:

1. `FactoryMachineDefinition`: Stores metadata about different types of factory machines.
2. `FactoryMachineInstance`: Represents active instances of factory machines and their current status.
3. `Product`: Stores information about generated products, including file details and parameters used for generation.
4. `Order`: Stores information about generation directly requested by the user. `OrderItem` is created from a user as one particular product to be generated.
5. `LogEntry`: Stores application logs for monitoring and debugging purposes.

### 3.3 Views

Key views include:
- Generate: Handles product generation requests
- Inventory: Displays and manages generated products
- Production: Shows the status of active FactoryMachineInstances and recent logs
- Settings: Manages application settings, including API keys

Views are being split from `views.py` to separate files in the same folder:
* `production_views.py` contains views to the production page
* `settings_views.py` contains views related to the settings page


### 3.4 API Views

API views have been implemented to support frontend functionality:

- `/api/factory_machines_list`: 
	- GET Returns a list of available factory machines
- `/api/factory_machine_detail`: 
	- GET Returns details about a specific factory machine, including its parameters
- `/products/id`: 
	- GET Returns details about a specific product
	- DELETE deletes the product
- `/products/`: 
	- GET Retrieves the list of all products

### 3.5 WebSocket Integration

This section outlines the integration of a WebSocket-based real-time event system into the AI Art Factory application. The intent of this design is enable distributed participants on the backend (web process, asynchronous factory workers) and frontend (javascript components in cooperation with the DOM) to participate by sending and receiving events in a decoupled way.
#### Technology

- Implemented using Django Channels for real-time communication

#### Events 

All events in the system will follow a standardized JSON format:


```json
{   "event_type": "string",  "payload": {},  "timestamp": "ISO8601 string",  "target": "string (optional)" }`
```

- `event_type`: Identifies the nature of the event
- `payload`: Contains the event-specific data
- `timestamp`: ISO8601 formatted string for event ordering
- `target`: Optional field to specify the intended recipient (e.g., specific UI component)

#### Event Types

Event types will follow a structured naming standard in the pattern:

(entity) _ (event verb)
(process) _ (state)

An (entity) is commonly a model entity, but could also be any data entity
(process) can often be defined as (model_process)

Examples of event types using this naming standard include:

order_created
logEntry_created
factoryMachineInstance_changed
product_deleted
production_status_changed (indicating a abstract concept like overall summary information has changed)
machine_operation_started
product_generation_complete

#### Architecture Components - Backend

**EventRouter**

- File: `main/event_router.py`
- Purpose: Maps event types to their respective handlers
- Key Methods:
    - `register(event_type, handler)`
    - `dispatch(event)`

**MainConsumer**

- File: `main/consumers.py`
- Purpose: Manages WebSocket connections and uses EventRouter to handle messages
- Key Methods:
    - `connect()`
    - `disconnect()`
    - `receive(text_data)`

**Model Signal Handlers**

- Files: Various model files (e.g., `main/models/products.py`, `main/models/orders.py`)
- Purpose: Emit events when model instances are created, updated, or deleted
- Implementation: Use Django signals (`post_save`, `post_delete`, etc.)

#### Architecture Components - Frontend

**EventHandler**

- File: `static/js/eventHandler.js`
- Purpose: Manages event subscriptions and dispatches events to appropriate handlers
- Key Methods:
    - `register(eventType, handler)`
    - `handleEvent(event)`

**WebSocket Connection**

- File: `templates/base.html`
- Purpose: Establishes and maintains the WebSocket connection
- Implementation: Initialize connection and EventHandler in the base template

**UI Components**

- Files: Various JS files (e.g., `static/js/components/productGrid.js`)
- Purpose: Subscribe to relevant events and update UI accordingly
- Implementation: Register event handlers for specific event types

#### Data Flow

- Backend event occurs (e.g., new product created)
- Model signal handler generates an event
- Event is sent through WebSocket to connected clients
- Frontend EventHandler receives the event
- EventHandler dispatches the event to registered component handlers
- UI components update based on the event data

#### Legacy Test Setup (to be removed/refactored)

- TestConsumer class in main/consumers.py handles WebSocket connections
- WebSocket test page available at /websocket-test/ for demonstration purposes

## 4. Key Design Decisions

### 4.1 Django-First Architectural Principles

1. **Leverage Django Conventions**: Use Django's established patterns and built-in features rather than custom solutions

2. **Fat Models**: Significant business logic is implemented within Django model classes, keeping related functionality close to the data

3. **Models as a Package**: Models are organized into a separate package under the main app for better modularity

4. **Standard Django Development**: Use Django's built-in development server and standard project structure

### 4.2 Domain-Specific Design Patterns

5. **FactoryMachine Abstraction**: Class hierarchy for FactoryMachines allows easy addition of new AI models with consistent behavior

6. **Flexible Parameter Handling**: Django's JSONField stores model-specific parameters while maintaining a consistent interface

7. **Provider Abstraction**: Support multiple AI providers (fal.ai, Replicate, civitai) through a common interface

### 4.3 Implementation Approach (To Be Finalized)

8. **Real-time Updates**: Choose between Django Channels (WebSockets), Server-Sent Events, or AJAX polling based on complexity needs

9. **Background Processing**: Evaluate Celery, Django-RQ, or Django's async views for production workflows

10. **Frontend Strategy**: Decide between Django templates + minimal JS vs. more sophisticated component architecture

11. **API Design**: Determine level of API-driven vs. server-side rendered approach

12. **Logging Strategy**: Use Django's built-in logging vs. custom database logging solution


## 5. Frontend Architecture (To Be Determined)

### 5.1 Core Approach
The frontend will use Django's template system as the foundation, with decisions to be made on the level of JavaScript enhancement.

### 5.2 Template Structure
1. Base template (base.html) provides overall structure and navigation
2. Page-specific templates extend the base template:
   - order.html: For placing new orders
   - inventory.html: For viewing and managing existing products
   - production.html: For monitoring production status
   - settings.html: For managing application settings

### 5.3 Enhancement Options (To Be Decided)

**Option 1: Minimal JavaScript**
- Server-side form handling with Django forms
- Basic progressive enhancement for UX improvements
- Standard Django pagination and filtering

**Option 2: Moderate Enhancement**
- Dynamic form generation based on factory machine selection
- AJAX for async operations (delete, status updates)
- Real-time updates via Server-Sent Events or polling

**Option 3: Component-Based**
- Reusable JavaScript components for complex UI elements
- Client-side state management
- WebSocket integration for real-time features

### 5.4 Styling Approach (To Be Decided)
- Options: Tailwind CSS, Bootstrap, or custom CSS
- Priority: Responsive design optimized for desktop use

### 5.5 UI Component Strategy (Implementation Pending)

Depending on the chosen frontend approach, consider:

**If Component-Based Approach Selected:**
- Self-contained, reusable UI elements
- Progressive enhancement from server-rendered HTML
- Event-driven communication between components
- Standard web component patterns

**Key UI Elements:**
- **ProductGrid**: Gallery view for generated products
- **OrderForm**: Dynamic form generation based on selected factory machine
- **ProductViewer**: Full-size product display modal
- **StatusMonitor**: Real-time production status updates



### 5.2 HTML Partials Approach

We have decided to prefer using HTML partials served from Django over JSON responses for dynamic content updates. This approach offers several benefits:

- Leverages Django's templating system strengths
- Reduces client-side HTML manipulation, and HTML literal use inside of Javascript
- Improves consistency between server-side and client-side rendering
- Simplifies debugging of HTML structure

Implementation:

- Create Django views that render partial HTML templates
- Use JavaScript to fetch these HTML partials and update the DOM
  
### 5.2 View Organization

To improve code organization and maintainability, we have separated view implementations as follows:

* All views are the main.views package with the following format:
	* `[section]_views.py` for full views corresponding to site location
	*  `[model or resource]_views.py` for general product access endpoints

### 5.3 URL Design

We have adopted a consistent URL structure to support various types of requests:

1. Complete Page Loads:
    - Pattern: `/<section>/` (for sections)
	    - Example: `/inventory/`, `/settings/`
	- Pattern: `<section>/<subsection` (for subsections)
		- Example: `/admin/events`
1. HTML Partials:
    - Pattern: `/partials/<resource-type>/<action>/`
    - Example: `/partials/product/list/`, `/partials/product/details/<id>/`
2. JSON API:
    - Pattern: `/api/<resource-type>/`
    - Example: `/api/product/`, `/api/product/<id>/`
3. Resource-Specific Pages:
    - Pattern: `/<resource-type>/<id>/`
    - Example: `/product/9/`

This structure provides clear separation between different types of requests and allows for easy expansion as new features are added.

### 5.4 Template Organization

Templates are organized to reflect the structure of the application and improve maintainability:

1. Base Templates:
    - Location: `/templates/base.html`
    - Purpose: Site-wide template defining the overall structure
2. Complete Page Templates:
    - Location: `/templates/main/<page_name>.html`
    - Example: `/templates/main/inventory.html`
    - Purpose: Templates for full pages, extending the base template
3. Partial Templates:
    - Location: `/templates/main/<resource>/<partial_name>.html`
    - Example: `/templates/main/products/product_details_sidebar.html`
    - Purpose: Reusable components or sections of pages
4. Other Templates:
    - Location: `/templates/main/other/<template_name>.html`
    - Purpose: Templates that don't fit into the main resource categories

This organization allows for easy location of templates and maintains a clear separation between different types of templates.

### 5.5 Static File Organization

Static files follow a similar organization to templates:

1. Site-wide JavaScript:
    - Location: `/static/js/<filename>.js`
    - Example: `/static/js/headerProductionCounter.js`
2. Page-specific JavaScript:
    - Location: `/static/js/main/<page_name>.js`
    - Example: `/static/js/main/inventory.js`
3. Resource-specific JavaScript:
    - Location: `/static/js/main/<resource>/<filename>.js`
    - Example: `/static/js/main/products/productDisplay.js`
4. Shared JavaScript:
    - Location: `/static/js/main/shared/<filename>.js`
    - Example: `/static/js/main/shared/pagination.js`
5. Other JavaScript:
    - Location: `/static/js/main/other/<filename>.js`
    - Example: `/static/js/main/other/llmChat.js`

### 5.6 Websockets in the Frontend

- A centralized WebSocket connection is established in the base template and made available to all components.
- Components can register handlers for specific event types or use a wildcard (`*`) to listen for all events.
- The EventHandler manages event subscriptions and dispatches events to appropriate handlers.

### 5.7 DOM Manipulation Strategy

- Initial HTML structure is provided by Django templates. Components interact with partials. 
- Components perform surgical updates to the DOM, targeting specific elements using IDs and classes.
- All component instances must have ID indicating the component type on their outermost tag. E.g. `productgrid-1`
- All DOM elements indicating an entity (E.g. a line in a table) should have an ID indicating the entity type. E.g. `<div id=product-123 ...>`. If the entity corresponds with a model entity, the number should be the ID. 
- Repeating data elements within the DOM should have a standard class, possibly named after a field or key, on the tag whose inner-HTML represents the value. E.g  `<span class="name">Harold</span>`
- For list-type structures, components use a hidden template element (e.g., `#event-new`) to create new items efficiently.
- This approach reduces coupling between JavaScript and HTML structure and allows for more efficient updates.


## 6. Backend Architecture

The backend is built on Django and consists of several key components:

1. **Models**: Define the data structure for factory machines, products, orders, and logs. Models are now organised in separate files within the `main/models/` directory.
2. **Views**: Handle HTTP requests, process form submissions, and render templates.
3. **API Views**: Provide JSON responses for frontend API requests.
4. **FactoryMachine Classes**: Encapsulate the logic for interacting with the fal.ai API and generating products.
5. **Custom Logger**: Handles logging to both the console and database.

## 6.2 Event Routing System

- An EventRouter class manages event dispatching and broadcasting.
- The EventRouter is initialized lazily to avoid accessing Django settings during module import.
- Event handlers can be registered for specific event types.
- The system supports broadcasting events to all connected clients.

## 6.3 API Design for Component Support

- API endpoints are designed to support the component-based frontend architecture.
- Endpoints provide initial data for components (e.g., list of event types, recent events).
- Partial templates are used for initial rendering of complex structures, which are then updated by components.
## 7. Data Flow

### 7.1 Generating an Image or Other Product
1. User navigates to the Order page (either '/' or '/order') and selects a factory machine and enters parameters.
2. Form is submitted to the place_order view.
3. View creates an `Order` and `OrderItem`, then calls the appropriate `FactoryMachine's` operate method.
4. FactoryMachine interacts with the fal.ai API to generate the product.
5. Generated product is saved to the database and file system.
6. Real-time notification sent (method TBD: SSE, WebSocket, or polling)
7. Inventory page updates to display the new product



### 7.2 Deleting a Product

When a user deletes a product: 
* The product fades out in the UI 
* An asynchronous DELETE request is sent to the server 
* The server deletes the product and returns the updated product grid
* The product grid is updated in the UI without a page refresh
* If the deleted product was selected, the product details sidebar is closed


### 7.X Other
- Initial data loaded via Django template rendering (preferred) or API calls
- Real-time updates via chosen communication method (SSE/WebSocket/polling)
- DOM updates through progressive enhancement approach

## 8. Testing Strategy

The project maintains a comprehensive Django-first testing approach with excellent coverage across models, views, API endpoints, worker systems, and UI integration. The test suite includes 1550+ lines of well-organized tests using Django's built-in testing framework.

**Current Coverage:**
- Models, views, signals, tasks, and management commands
- Worker system and batch processing
- External API integration (mocked)
- UI components and notifications
- End-to-end workflows

**Testing Infrastructure:**
- Custom test runner (`run_tests.sh`) with categorized test suites
- Proper external service mocking and test isolation
- In-memory database for fast execution

For detailed testing guidelines, implementation roadmap, and quality standards, see [docs/testing.md](testing.md).

## 9. Logging and Monitoring

A custom logger (logger.py) is implemented to:
- Log events to both the console and database
- Provide different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Store additional metadata with log entries

The production page displays recent logs for monitoring application activity.

## 10. Future Considerations

1. **Scalability**: Implement a plugin system for easier addition of new FactoryMachine types.
2. **Asynchronous Processing**: Implement background task processing for long-running generation tasks.
3. **Advanced Filtering and Search**: Enhance the inventory view with more advanced filtering and search capabilities.
4. **User Authentication**: Implement user accounts for personalized galleries and settings.
5. **Caching**: Implement caching for API responses to improve performance.
6. **Error Handling and Retry Mechanism**: Implement more robust error handling and retry logic for API calls.
7. **Real-time Communication**: Evaluate upgrade from current approach based on actual requirements.
8. **Pagination**: Implement pagination for the inventory to handle large numbers of generated products efficiently.

## 11. Deployment

Current setup is for local development. For production deployment, consider:

1. Using a production-grade database (e.g., PostgreSQL)
2. Implementing proper security measures for API key storage
3. Setting up a content delivery network (CDN) for serving generated images
4. Configuring appropriate server setup (WSGI for standard Django, ASGI if real-time features require it)
5. Implementing rate limiting on API endpoints to prevent abuse
6. Setting up proper SSL/TLS certificates for secure communication
7. Using Django's development server for local development, configuring proper production server for deployment

## Appendix

