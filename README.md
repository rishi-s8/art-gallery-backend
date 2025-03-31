# NANDA Registry Backend

The backend for the ART Gallery Project, a decentralized registry and discovery platform for Multi-Agent Communication Protocol (MCP) servers.

## Overview

This project provides a comprehensive API and management system for registering, discovering, and verifying MCP servers. It allows users to:

- Register and manage their MCP servers
- Discover available servers based on various criteria
- Verify server capabilities and uptime
- Rate and review servers
- Track analytics on server usage

## Technologies

- **Framework**: Django 5.1 with Django REST Framework
- **Database**: PostgreSQL
- **Caching & Message Broker**: Redis
- **Asynchronous Tasks**: Celery
- **Real-time Communication**: Django Channels
- **Authentication**: JWT (JSON Web Tokens)
- **Documentation**: drf-spectacular (OpenAPI)
- **Deployment**: Docker, Nginx, Let's Encrypt

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/aidecentralized/art-gallery-backend.git
   cd art-gallery-backend
   ```

2. Create a `.env` file with the following variables:

   ```
   # Django
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Database
   DB_NAME=mcp_nexus
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432

   # Redis
   REDIS_URL=redis://redis:6379/0

   # Celery
   CELERY_BROKER_URL=redis://redis:6379/1
   CELERY_RESULT_BACKEND=redis://redis:6379/2
   ```

3. Build and run the Docker containers:

   ```bash
   docker-compose up -d
   ```

4. Create a superuser:

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. The application should now be running at `http://localhost:80`

### Development Setup

For local development without Docker:

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your local PostgreSQL database and Redis server

4. Create a `.env.dev` file with local configurations

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

- `authentication/`: User authentication and management
- `servers/`: MCP server registration and management
- `discovery/`: Server discovery and search functionality
- `verification/`: Server capability verification mechanisms
- `analytics/`: Usage statistics and analytics
- `webhooks/`: Webhook integration for event notifications
- `common/`: Shared utilities and middleware
- `mcp_nexus/`: Project configuration and settings

## API Documentation

When running the application, API documentation is available at:

- Swagger UI: `/api/v1/schema/swagger-ui/`
- ReDoc: `/api/v1/schema/redoc/`

## Contributing

We welcome contributions to the NANDA Registry Backend! Please follow these guidelines when contributing to the project.

### Code of Conduct

This project and everyone participating in it are governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

### How to Contribute

1. **Fork the repository** - Create your own fork of the project.

2. **Create a branch** - Make your changes in a new git branch:

   ```bash
   git checkout -b my-fix-branch main
   ```

3. **Make your changes** - Follow the coding guidelines below.

4. **Write tests** - Add or update tests as necessary.

5. **Run tests and linting** - Make sure all tests pass and code meets the style guidelines:

   ```bash
   python manage.py test
   flake8
   black .
   ```

6. **Commit your changes** - Follow the [conventional commits](https://www.conventionalcommits.org/) format:

   ```bash
   git commit -m "feat: add new feature"
   ```

7. **Push to your fork** - Submit a pull request to the main repository.

8. **Submit a pull request** - Describe your changes and why they should be included.

### Development Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Write docstrings for all functions, classes, and modules
- Add type hints to function signatures where possible
- Write unit tests for new functionality using Django's testing framework
- Keep functions small and focused on a single responsibility
- Use descriptive variable and function names

### Pull Request Process

1. Update the README.md with details of changes, if applicable
2. Update the API documentation if you've made API changes
3. The PR should work on Python 3.11+
4. PRs require at least one review from a code owner
5. PRs will be merged once they pass all CI checks and receive approval

## Testing

Run the full test suite:

```bash
docker-compose exec web python manage.py test
```

Or run tests for a specific app:

```bash
docker-compose exec web python manage.py test servers
```

## Deployment

The application is configured for deployment using Docker, Nginx, and Let's Encrypt for SSL. For production deployment, update the environment variables accordingly and configure the Nginx settings as needed.

### AWS Elastic Beanstalk

The project is also configured for deployment to AWS Elastic Beanstalk. Files for this setup are included in the repository. Whenever a change is committed to the main branch, the github workflow will automatically upload and deploy it on our AWS instance.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all the contributors who have helped build this project
- Built with Django and other open source technologies.
- Core contributor team will be acknowledged here soon.
