

# INFO
    Система красных картчочек



# environment
    python3.6
    
    apt-get install python3-dev libmysqlclient-dev

# deploy 
    docker-compose build
    docker-compose up -d
    docker exec -it django_cards python manage.py createsuperuser
    