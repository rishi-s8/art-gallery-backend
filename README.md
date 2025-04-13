# NANDA Registry

A multi-institutional decentralized registry and discovery platform for servers built on top of Networked Agents and Decentralized AI (NANDA) and Model Context Protocol (MCP).

## Overview

The NANDA Registry provides a comprehensive API and management system for registering, discovering, and verifying servers in a decentralized architecture. It enables:

- Registration and management of servers (Agents, Resources, and Tools)
- Discovery of available servers based on various criteria
- Verification of servers
- Rating and reviews of servers
- Analytics tracking on server usage
- Webhook integration for event notifications

## System Architecture

This project is built with:

- **Framework**: Django 5.1 with Django REST Framework
- **Database**: PostgreSQL
- **Caching & Message Broker**: Redis
- **Task Queue**: Celery
- **Real-time Communication**: Django Channels
- **Authentication**: JWT (JSON Web Tokens)
- **Documentation**: drf-spectacular (OpenAPI)
- **Deployment**: Docker, Nginx, Let's Encrypt, AWS Elastic Beanstalk

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Prerequisites

- Docker and Docker Compose
- Domain name (for production deployment)
- SSL certificate (Let's Encrypt recommended)

#### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/aidecentralized/nanda-registry.git
   cd nanda-registry
   ```

2. Create a `.env` file with the following variables:

   ```
   # Django
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com

   # Database
   DB_NAME=nanda_db
   DB_USER=postgres
   DB_PASSWORD=[strong-password]
   DB_HOST=db
   DB_PORT=5432

   # Redis
   REDIS_URL=redis://redis:6379/0

   # Celery
   CELERY_BROKER_URL=redis://redis:6379/1
   CELERY_RESULT_BACKEND=redis://redis:6379/2

   # Email (for verification, not working as of now)
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@example.com
   EMAIL_HOST_PASSWORD=your-email-password
   EMAIL_USE_TLS=True
   DEFAULT_FROM_EMAIL=noreply@your-domain.com

   # Frontend URL (for password reset and verification emails)
   FRONTEND_URL=https://your-domain.com
   ```

3. Customize Nginx configuration:

   Edit the `nginx/default.conf` file to include your domain name and SSL configuration.

4. Build and run the Docker containers:

   ```bash
   docker-compose up -d
   ```

5. Create a superuser:

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. Set up SSL with Let's Encrypt:

   ```bash
   docker-compose exec nginx certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

### Option 2: AWS Elastic Beanstalk Deployment

The project is already configured for deployment to AWS Elastic Beanstalk.
Talk to the MIT team if you need more help with configuring your AWS.

#### Prerequisites

- AWS Account
- AWS CLI configured
- EB CLI installed

#### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/aidecentralized/nanda-registry.git
   cd nanda-registry
   ```

2. Create an Elastic Beanstalk environment:

   ```bash
   eb init -p docker
   eb create nanda-registry-env
   ```

3. Set up environment variables in the Elastic Beanstalk console, or use:

   ```bash
   eb setenv SECRET_KEY=your-secret-key ALLOWED_HOSTS=your-domain.com,www.your-domain.com ...
   ```

4. Deploy the application:

   ```bash
   eb deploy
   ```

5. Configure your domain with Route 53 or your DNS provider.

## Configuration Options

### Environment Variables

| Variable                | Description                           | Default                |
| ----------------------- | ------------------------------------- | ---------------------- |
| `SECRET_KEY`            | Django secret key                     | None (required)        |
| `DEBUG`                 | Debug mode                            | `False`                |
| `ALLOWED_HOSTS`         | Comma-separated list of allowed hosts | `localhost,127.0.0.1`  |
| `DB_NAME`               | Database name                         | `mcp_nexus`            |
| `DB_USER`               | Database user                         | `postgres`             |
| `DB_PASSWORD`           | Database password                     | None (required)        |
| `DB_HOST`               | Database host                         | `db`                   |
| `DB_PORT`               | Database port                         | `5432`                 |
| `REDIS_URL`             | Redis URL                             | `redis://redis:6379/0` |
| `CELERY_BROKER_URL`     | Celery broker URL                     | `redis://redis:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL             | `redis://redis:6379/2` |
| `EMAIL_HOST`            | SMTP server host                      | None                   |
| `EMAIL_PORT`            | SMTP server port                      | `587`                  |
| `EMAIL_HOST_USER`       | SMTP server username                  | None                   |
| `EMAIL_HOST_PASSWORD`   | SMTP server password                  | None                   |
| `EMAIL_USE_TLS`         | Use TLS for email                     | `True`                 |
| `DEFAULT_FROM_EMAIL`    | Default sender email                  | None                   |
| `FRONTEND_URL`          | Frontend URL for emails               | None                   |

### Custom Settings

Additional settings can be configured by editing `mcp_nexus/settings.py`:

- `VERIFICATION_TOKEN_EXPIRY`: Duration for verification tokens
- `VERIFICATION_CHECK_INTERVAL`: Interval for server health checks
- `ANALYTICS_RETENTION_DAYS`: Days to retain analytics data

## Maintenance

### Database Backups

Set up regular database backups:

```bash
# For Docker deployment
docker-compose exec db pg_dump -U postgres mcp_nexus > backup_$(date +%Y%m%d).sql

# For AWS
aws rds create-db-snapshot --db-instance-identifier your-db-identifier --db-snapshot-identifier snapshot-name
```

### Logs

View logs:

```bash
# For Docker deployment
docker-compose logs -f web
docker-compose logs -f celery

# For AWS
eb logs
```

### Updates

To update the system:

```bash
# For Docker deployment
git pull
docker-compose down
docker-compose build
docker-compose up -d

# For AWS
git pull
eb deploy
```

## API Documentation

When running the application, comprehensive API documentation is available at:

- Swagger UI: `/api/v1/schema/swagger-ui/`
- ReDoc: `/api/v1/schema/redoc/`

## Core Features

### Server Registration

Users can register their MCP servers with:

- Basic information (name, description, URL)
- Server type (Agent, Resource, Tool)
- Capabilities and parameters
- Usage requirements

### Server Discovery

The registry provides multiple ways to discover servers:

- Full-text search
- Filtering by type, tags, verification status
- Recommendations based on usage patterns
- Popular servers listing

### Verification System

The registry verifies servers through:

- Ownership verification (DNS, file, or meta tag)
- Health checks
- Capabilities validation
- Security assessment

### Analytics

Track and analyze:

- Server usage patterns
- Uptime and performance
- Network-wide trends
- Client behavior

### Webhooks

Integrate with external systems through webhooks for events like:

- Server registration/updates
- Verification status changes
- Server status changes

## Customization

### Branding

- Update `mcp_nexus/views.py` to customize the home page
- Replace logos and styles in the static files

### Adding New Features

1. Create a new Django app:

   ```bash
   docker-compose exec web python manage.py startapp new_feature
   ```

2. Register the app in `mcp_nexus/settings.py`
3. Add models, views, and URLs
4. Update API documentation

## Security Considerations

- Regularly update dependencies
- Set strong passwords for database and admin users
- Keep `DEBUG=False` in production
- Configure proper HTTPS
- Implement rate limiting for public APIs
- Consider adding WAF protection

## Support and Community

- GitHub Issues: Report bugs and feature requests
- Contribution Guidelines: Follow PEP 8 style and include tests
- Documentation: Keep API docs and README updated

## License

This project is licensed under the MIT License - see the LICENSE file for details.
