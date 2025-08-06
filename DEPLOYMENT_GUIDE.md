# Mass Tracking System - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Mass Tracking System in various environments. The system consists of a React frontend, Flask backend, and PostgreSQL database.

## System Requirements

### Minimum Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+ / macOS 10.15+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB available disk space
- **Network**: Internet connection for initial setup and updates

### Software Dependencies
- **Node.js**: Version 18.0 or higher
- **Python**: Version 3.9 or higher
- **PostgreSQL**: Version 12 or higher
- **Git**: Latest version
- **Docker** (optional): For containerized deployment

## Deployment Options

### Option 1: Local Development Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/willymsfs/Mass-Track.git
cd Mass-Track
```

#### 2. Database Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createdb mass_tracking
sudo -u postgres psql -c "CREATE USER mass_user WITH PASSWORD 'mass_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mass_tracking TO mass_user;"
sudo -u postgres psql -c "ALTER USER mass_user CREATEDB;"

# Initialize database schema
cd database
PGPASSWORD=mass_password psql -h localhost -U mass_user -d mass_tracking -f schema.sql
PGPASSWORD=mass_password psql -h localhost -U mass_user -d mass_tracking -f seed_data.sql
```

#### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file with your database credentials

# Start the backend server
python src/main.py
```

#### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 5. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- API Documentation: http://localhost:5000/api/docs

### Option 2: Docker Deployment

#### 1. Prerequisites
```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Deploy with Docker Compose
```bash
# Clone repository
git clone https://github.com/willymsfs/Mass-Track.git
cd Mass-Track

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 3. Initialize Database
```bash
# Wait for PostgreSQL to be ready, then initialize
docker-compose exec backend python scripts/init_db.py
```

#### 4. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

### Option 3: Production Deployment

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nginx postgresql postgresql-contrib python3 python3-pip nodejs npm git

# Configure firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

#### 2. Database Configuration
```bash
# Secure PostgreSQL installation
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_secure_password';"

# Create production database
sudo -u postgres createdb mass_tracking_prod
sudo -u postgres psql -c "CREATE USER mass_prod_user WITH PASSWORD 'your_production_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mass_tracking_prod TO mass_prod_user;"

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = 'localhost'
# Set: max_connections = 100

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: local   mass_tracking_prod   mass_prod_user   md5

sudo systemctl restart postgresql
```

#### 3. Backend Production Setup
```bash
# Clone and setup backend
git clone https://github.com/willymsfs/Mass-Track.git /opt/mass-track
cd /opt/mass-track/backend

# Create production virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Configure production environment
cp .env.example .env
nano .env
# Update with production database credentials and settings

# Initialize production database
PGPASSWORD=your_production_password psql -h localhost -U mass_prod_user -d mass_tracking_prod -f ../database/schema.sql

# Create systemd service
sudo nano /etc/systemd/system/mass-track-backend.service
```

**Backend Service Configuration:**
```ini
[Unit]
Description=Mass Tracking System Backend
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/mass-track/backend
Environment=PATH=/opt/mass-track/backend/venv/bin
ExecStart=/opt/mass-track/backend/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 src.main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Start backend service
sudo systemctl daemon-reload
sudo systemctl enable mass-track-backend
sudo systemctl start mass-track-backend
```

#### 4. Frontend Production Setup
```bash
cd /opt/mass-track/frontend

# Install dependencies and build
npm install
npm run build

# Configure Nginx
sudo nano /etc/nginx/sites-available/mass-track
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /opt/mass-track/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        root /opt/mass-track/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/mass-track /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. SSL Certificate (Optional but Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Configuration

### Environment Variables

#### Backend (.env)
```env
# Database Configuration
DATABASE_URL=postgresql://mass_user:mass_password@localhost:5432/mass_tracking
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mass_tracking
DATABASE_USER=mass_user
DATABASE_PASSWORD=mass_password

# Security Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=3600

# Application Configuration
FLASK_ENV=production
DEBUG=False
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/opt/mass-track/uploads
```

#### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:5000/api
VITE_APP_NAME=Mass Tracking System
VITE_APP_VERSION=1.0.0
```

### Database Configuration

#### PostgreSQL Optimization
```sql
-- Performance tuning for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Restart PostgreSQL to apply changes
```

## Monitoring and Maintenance

### Log Files
- **Backend Logs**: `/var/log/mass-track/backend.log`
- **Nginx Logs**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL Logs**: `/var/log/postgresql/postgresql-14-main.log`

### Health Checks
```bash
# Check backend health
curl http://localhost:5000/api/health

# Check database connection
sudo -u postgres psql -d mass_tracking -c "SELECT version();"

# Check service status
sudo systemctl status mass-track-backend
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Backup Strategy
```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/mass-track"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U mass_user mass_tracking > $BACKUP_DIR/db_backup_$DATE.sql

# Application backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/mass-track

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Update Procedure
```bash
# 1. Backup current system
sudo systemctl stop mass-track-backend

# 2. Pull latest changes
cd /opt/mass-track
git pull origin main

# 3. Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 4. Run database migrations (if any)
python scripts/migrate.py

# 5. Update frontend
cd ../frontend
npm install
npm run build

# 6. Restart services
sudo systemctl start mass-track-backend
sudo systemctl reload nginx
```

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check logs
sudo journalctl -u mass-track-backend -f

# Common solutions:
# 1. Check database connection
# 2. Verify environment variables
# 3. Check file permissions
sudo chown -R www-data:www-data /opt/mass-track
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U mass_user -d mass_tracking

# Check pg_hba.conf configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

#### Frontend Build Issues
```bash
# Clear cache and rebuild
cd /opt/mass-track/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Performance Optimization

#### Database Indexing
```sql
-- Add indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_mass_celebrations_priest_id ON mass_celebrations(priest_id);
CREATE INDEX CONCURRENTLY idx_mass_celebrations_date ON mass_celebrations(celebration_date);
CREATE INDEX CONCURRENTLY idx_bulk_intentions_priest_id ON bulk_intentions(priest_id);
```

#### Nginx Caching
```nginx
# Add to Nginx configuration
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Security Considerations

### Database Security
- Use strong passwords for database users
- Limit database access to localhost only
- Regular security updates
- Enable SSL for database connections in production

### Application Security
- Use HTTPS in production
- Implement rate limiting
- Regular dependency updates
- Secure file upload handling
- Input validation and sanitization

### Server Security
- Keep system updated
- Configure firewall properly
- Use fail2ban for intrusion prevention
- Regular security audits
- Backup encryption

## Support and Maintenance

### Regular Maintenance Tasks
1. **Daily**: Monitor logs and system health
2. **Weekly**: Database backup verification
3. **Monthly**: Security updates and dependency updates
4. **Quarterly**: Performance review and optimization

### Getting Help
- **GitHub Issues**: https://github.com/willymsfs/Mass-Track/issues
- **Documentation**: Check README.md and API documentation
- **Logs**: Always check application and system logs first

This deployment guide provides comprehensive instructions for setting up the Mass Tracking System in various environments. Choose the deployment option that best fits your needs and infrastructure requirements.

