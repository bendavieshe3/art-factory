# Production Deployment Guide

This guide covers deploying Art Factory to a production environment with proper security, performance, and reliability configurations.

## Prerequisites

### System Requirements
- Python 3.11 or higher
- 2GB+ RAM (4GB+ recommended for batch processing)
- 10GB+ disk space (for generated images and logs)
- Network access to AI provider APIs (fal.ai, Replicate)

### Required Environment Variables
```bash
# Django Configuration
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (optional - defaults to SQLite)
DATABASE_URL=postgres://user:password@localhost:5432/artfactory

# AI Provider APIs (at least one required)
FAL_KEY=your-fal-api-key
REPLICATE_API_TOKEN=your-replicate-token
CIVITAI_API_KEY=your-civitai-key  # Optional

# File Storage
STATIC_ROOT=/var/www/artfactory/staticfiles
MEDIA_ROOT=/var/www/artfactory/media
LOGS_DIR=/var/log/artfactory

# SSL and Security (for HTTPS deployments)
SECURE_SSL_REDIRECT=True

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=Art Factory <noreply@yourdomain.com>
```

## Deployment Steps

### 1. Server Setup

#### Create dedicated user and directories:
```bash
# Create art factory user
sudo adduser artfactory
sudo usermod -aG sudo artfactory

# Create application directories
sudo mkdir -p /opt/artfactory
sudo mkdir -p /var/www/artfactory/{staticfiles,media}
sudo mkdir -p /var/log/artfactory

# Set ownership
sudo chown -R artfactory:artfactory /opt/artfactory
sudo chown -R artfactory:artfactory /var/www/artfactory
sudo chown -R artfactory:artfactory /var/log/artfactory
```

#### Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y nginx postgresql postgresql-contrib  # Optional
sudo apt install -y supervisor  # For process management

# CentOS/RHEL
sudo yum install -y python3.11 python3-pip nginx postgresql-server
```

### 2. Application Deployment

#### Deploy the application:
```bash
# Switch to artfactory user
sudo su - artfactory

# Clone and setup
cd /opt/artfactory
git clone https://github.com/bendavieshe3/art-factory.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary dj-database-url  # Production extras
```

#### Configure environment:
```bash
# Create environment file
cat > /opt/artfactory/.env << EOF
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://artfactory:password@localhost:5432/artfactory
FAL_KEY=your-fal-api-key
REPLICATE_API_TOKEN=your-replicate-token
STATIC_ROOT=/var/www/artfactory/staticfiles
MEDIA_ROOT=/var/www/artfactory/media
LOGS_DIR=/var/log/artfactory
EOF

# Secure the environment file
chmod 600 /opt/artfactory/.env
```

### 3. Database Setup

#### PostgreSQL (Recommended):
```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE artfactory;
CREATE USER artfactory WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE artfactory TO artfactory;
ALTER USER artfactory CREATEDB;
EOF
```

#### Run migrations:
```bash
cd /opt/artfactory
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=ai_art_factory.production_settings

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py load_seed_data  # Load factory machine definitions
```

### 4. Web Server Configuration

#### Gunicorn configuration (`/opt/artfactory/gunicorn.conf.py`):
```python
bind = "127.0.0.1:8000"
workers = 3  # 2 * CPU cores + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "artfactory"
group = "artfactory"
tmp_upload_dir = None
```

#### Nginx configuration (`/etc/nginx/sites-available/artfactory`):
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (use Let's Encrypt or your certificates)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /var/www/artfactory/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/artfactory/media/;
        expires 1d;
        add_header Cache-Control "public";
    }
}
```

#### Enable Nginx site:
```bash
sudo ln -s /etc/nginx/sites-available/artfactory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Process Management

#### Supervisor configuration (`/etc/supervisor/conf.d/artfactory.conf`):
```ini
[program:artfactory-web]
command=/opt/artfactory/venv/bin/gunicorn ai_art_factory.wsgi:application -c /opt/artfactory/gunicorn.conf.py
directory=/opt/artfactory
user=artfactory
environment=DJANGO_SETTINGS_MODULE=ai_art_factory.production_settings
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/artfactory/gunicorn.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5

[program:artfactory-worker]
command=/opt/artfactory/venv/bin/python manage.py run_worker
directory=/opt/artfactory
user=artfactory
environment=DJANGO_SETTINGS_MODULE=ai_art_factory.production_settings
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/artfactory/worker.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
```

#### Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## Monitoring and Maintenance

### Log Files
- Application logs: `/var/log/artfactory/art_factory_production.log`
- Worker logs: `/var/log/artfactory/workers_production.log`
- Error logs: `/var/log/artfactory/errors_production.log`
- Web server logs: `/var/log/artfactory/gunicorn.log`

### Health Checks
```bash
# Check application status
sudo supervisorctl status

# Check database connectivity
cd /opt/artfactory && source venv/bin/activate
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('DB OK')"

# Check API access
curl -f http://localhost:8000/health/ || echo "Web server down"
```

### Backup Strategy
```bash
#!/bin/bash
# Backup script example
BACKUP_DIR="/backup/artfactory/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump artfactory > $BACKUP_DIR/database.sql

# Media files backup
rsync -av /var/www/artfactory/media/ $BACKUP_DIR/media/

# Application backup
tar -czf $BACKUP_DIR/application.tar.gz -C /opt artfactory/

# Keep last 7 days
find /backup/artfactory/ -type d -mtime +7 -exec rm -rf {} \;
```

### Updates and Deployments
```bash
# Update application
cd /opt/artfactory
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart artfactory-web artfactory-worker
```

## Security Considerations

1. **Environment Variables**: Never commit sensitive data to version control
2. **Database Security**: Use strong passwords and restrict network access
3. **File Permissions**: Ensure proper ownership and permissions on all files
4. **SSL/TLS**: Always use HTTPS in production
5. **Firewall**: Restrict access to necessary ports only (80, 443, SSH)
6. **Regular Updates**: Keep system packages and Python dependencies updated
7. **API Keys**: Rotate API keys regularly and monitor usage

## Troubleshooting

### Common Issues

**Issue**: Worker processes failing
```bash
# Check worker logs
tail -f /var/log/artfactory/workers_production.log

# Restart workers
sudo supervisorctl restart artfactory-worker
```

**Issue**: Database connection errors
```bash
# Check database status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U artfactory -d artfactory
```

**Issue**: Static files not loading
```bash
# Recollect static files
cd /opt/artfactory && source venv/bin/activate
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t
```

**Issue**: High memory usage
- Monitor worker processes: `ps aux | grep python`
- Adjust Gunicorn worker count in configuration
- Consider implementing Redis for caching

For additional support, check the application logs and refer to the Django documentation for deployment best practices.