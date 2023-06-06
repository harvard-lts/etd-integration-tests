# etd-integration-tests

<img src="https://github.com/harvard-lts/etd-integration-tests/actions/workflows/pytest.yml/badge.svg">

### To start component:
- clone repository
- cp .env.example to .env
- cp celeryconfig.py.example to celeryconfig.py and put in credentials
- make sure logs/etd_itests directory exists (need to fix)
- bring up docker
- - docker-compose -f docker-compose-local.yml up --build -d --force-recreate --remove-orphans
- start test by going to the browser at this url:
- - https://localhost:10601/integration
- stop docker 
- - docker-compose -f docker-compose-local.yml down
