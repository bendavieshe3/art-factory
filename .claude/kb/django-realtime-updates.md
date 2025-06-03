# Django Real-time Updates

## Topics Covered
- Polling vs WebSockets vs Server-Sent Events (SSE)
- Django implementation approaches
- Performance comparisons
- Architecture considerations
- Best practices for 2024

## Main Content

### Technology Comparison

**Polling**
- Traditional HTTP request/response cycle
- Client repeatedly requests updates from server
- Higher server load and network overhead
- Simplest to implement but least efficient
- Good for infrequent updates or when other methods aren't viable

**WebSockets**
- Full-duplex, bidirectional communication
- Single persistent connection
- Lowest latency for real-time applications
- Best for chat, collaboration, gaming
- Supports binary data
- Requires more complex server infrastructure

**Server-Sent Events (SSE)**
- One-way communication (server to client)
- Built on standard HTTP
- Automatic reconnection support
- Works with corporate firewalls
- UTF-8 text only (no binary)
- Simpler than WebSockets for push notifications

### Performance Characteristics

WebSockets and SSE have similar performance profiles and are the most efficient options for real-time updates. WebSockets offer the lowest latency due to persistent connections, while SSE provides simpler implementation with built-in reconnection.

### Django Implementation Options

**1. HTTP Polling (Native Django)**
```python
# Simple AJAX polling pattern
def order_status_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return JsonResponse({
        'status': order.status,
        'progress': order.progress,
        # ... other fields
    })
```

**2. Django Channels (WebSockets/SSE)**
- Official Django async support
- Requires ASGI server (Daphne, Uvicorn)
- Significant architectural changes
- Best for comprehensive real-time features

**3. Separate WebSocket Server**
- Run alongside Django application
- Good for limited real-time features
- Keeps Django app simpler
- Can use Node.js, Go, or other technologies

### Architecture Best Practices

1. **Don't mix blocking and non-blocking**
   - Django is synchronous by design
   - Avoid running Django on gevent/async servers
   - Use proper async frameworks when needed

2. **Separate concerns**
   - Keep real-time server separate from main Django app
   - Use message queues for communication
   - Scale independently

3. **Choose based on use case**
   - Simple notifications: SSE or polling
   - Interactive features: WebSockets
   - Occasional updates: Polling is fine

### Implementation Recommendations

**For Order Status Updates (like Art Factory)**
- Polling is sufficient for order tracking
- 3-5 second intervals for active orders
- Exponential backoff for long-running tasks
- Client-side timeout protection

**For Live Notifications**
- SSE for one-way push notifications
- Simpler than WebSockets
- Built-in reconnection handling
- Good browser support

**For Interactive Features**
- WebSockets for chat, collaboration
- Django Channels for deep integration
- Consider dedicated WebSocket service

## Local Considerations

### Art Factory Implementation
- Currently uses polling for order status
- 3-second interval during active generation
- 30-second refresh for recent data
- Works well for current use case

### macOS Development
- No special considerations for local development
- ASGI servers (Daphne, Uvicorn) work well on macOS
- Consider Docker for complex WebSocket setups

### Production Deployment
- Polling scales horizontally easily
- WebSockets require sticky sessions
- SSE needs proper proxy configuration
- Consider CDN implications

## Metadata
- **Last Updated**: 2025-06-02
- **Version**: Django 5.1+ compatible
- **Sources**: 
  - https://codeburst.io/polling-vs-sse-vs-websocket-how-to-choose-the-right-one-1859e4e13bd9
  - https://ably.com/blog/websockets-vs-sse
  - Django Channels documentation
  - Art Factory implementation experience