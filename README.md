# etd-integration-tests

<img src="https://github.com/harvard-lts/etd-integration-tests/actions/workflows/pytest.yml/badge.svg">

### To start component:
- clone repository
- cp .env.example to .env
- add 'alma_dropbox_rsa_id' and 'known_hosts' from the vault to './.ssh'
- cp celeryconfig.py.example to celeryconfig.py and put in credentials
- make sure logs/etd_itests directory exists (need to fix)
- for test to pass locally, etd_dash_service docker must run locally
- - share a submission queue between etd dash and itest (e.g. etd_submission_ready_mjv)
- - the docker-compose-local.yml for etd dash and itest both use /tmp/etd_dash_data/in locally
- otherwise, in isolation, in order for itest to pass locally copy over zip (which test deletes each time)
- - mkdir -p /tmp/etd_dash_data/in/proquest2023072721-999999-gsd
- - cp data/submission_999999.zip /tmp/etd_dash_data/in/proquest2023072721-999999-gsd/
- bring up docker
- - docker-compose -f docker-compose-local.yml up --build -d --force-recreate --remove-orphans
- start test by going to the browser at this url:
- - https://localhost:10610/integration
- stop docker 
- - docker-compose -f docker-compose-local.yml down
