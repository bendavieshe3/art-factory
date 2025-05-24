# Django Framework

## Topics Covered
- Django 5.1 features and updates
- Django 5.2 LTS features
- Python and database support
- Support timelines and upgrade paths

## Main Content

### Django 5.1 (Released August 2024)

**Key Features:**
- **QueryString Template Tag**: `{% querystring %}` template tag for easier URL parameter manipulation
- **PostgreSQL Connection Pool Support**: Improved performance for PostgreSQL connections
- **LoginRequiredMiddleware**: Redirects unauthenticated requests to login page; use `login_not_required()` decorator for exceptions
- **Enhanced Admin**: ModelAdmin.list_display supports `__` lookups for related model fields
- **Security Improvements**: PBKDF2 iteration count increased to 870,000; ScryptPasswordHasher parallelism increased to 5
- **Accessibility Enhancements**: Improved screen reader support, semantic HTML, better form field associations

**Support:**
- Python: 3.10, 3.11, 3.12, 3.13
- PostgreSQL: 13+
- MariaDB: 10.5+
- Security updates until December 2025

### Django 5.2 LTS (Released April 2025)

**Key Features:**
- **Automatic Model Imports**: Shell command automatically imports models from all apps
- **Enhanced Database Support**: PostgreSQL 14+, MySQL defaults to utf8mb4 character set
- **Long-term Support**: 3 years of security updates (until April 2028)

**Support:**
- Python: 3.10, 3.11, 3.12, 3.13
- PostgreSQL: 14+
- Previous LTS (Django 4.2) support ends April 2026

### Upgrade Recommendations
- All Django 5.1 users should upgrade to 5.2 LTS before December 2025
- Django 5.2 provides long-term stability with 3-year support cycle

## Local Considerations
- Current project uses Django 5.1+ commitment
- Consider upgrading to Django 5.2 LTS for long-term stability
- LoginRequiredMiddleware could be useful for the Art Factory authentication system
- PostgreSQL connection pooling would benefit production deployment
- QueryString template tag useful for pagination and filtering in the UI

### Django 5.2 LTS Additional Features

**Composite Primary Keys:**
- Support for compound primary keys added
- Not yet compatible with Django admin or foreign key targets
- Future development expected for full integration

**Enhanced Response Handling:**
- `response.text` now returns string representation of body
- Improved HTTP response processing

**Database Improvements:**
- MySQL connections default to utf8mb4 character set
- Enhanced UniqueConstraint error handling
- PostgreSQL 14+ requirement (upstream support consideration)

**Community Contribution:**
- 194 contributors worldwide for Django 5.2
- Significant community-driven development

## Metadata
- **Last Updated**: 2025-05-24
- **Version**: Django 5.2 LTS (April 2025)
- **Sources**: 
  - https://docs.djangoproject.com/en/5.2/releases/5.1/
  - https://docs.djangoproject.com/en/5.2/releases/5.2/
  - https://www.djangoproject.com/weblog/2024/aug/07/django-51-released/
  - https://www.djangoproject.com/weblog/2025/apr/02/django-52-released/
  - Django 5.2 release notes and community feedback