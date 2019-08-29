

# INFO
    Система красных картчочек



# environment
    python3.6
    
    apt-get install python3-dev libmysqlclient-dev
    python3.6 -m venv --prompt="env: unti_cards" ~/ENV/unti_cards

# deploy 
    docker-compose build
    docker-compose up -d
    docker exec -it django_cards python manage.py createsuperuser

#### run tests
    cd ./src
    py.test


