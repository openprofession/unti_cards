

# INFO
    Система красных картчочек



# environment
    python3.6
    
    apt-get install python3-dev libmysqlclient-dev

# db
    docker run --rm --name uc_mysql  --network host
        -e MYSQL_ROOT_PASSWORD=7895123qw  mariadb:10.2
    docker exec -it uc_mysql bash
    mysql -p    # 7895123qw
    CREATE DATABASE unti_cards;

