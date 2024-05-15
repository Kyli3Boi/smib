## Docker deployment
### Installation
- Clone the repository to your target server host
- Install docker if not already present
- Set the slack tokens and DB Web UI Credentials as environment variables using either method below:
  - Linux
    - `export SLACK_APP_TOKEN=<app-token>`
    - `export SLACK_BOT_TOKEN=<bot-token>`
    - `export ME_CONFIG_BASICAUTH_USERNAME=<mongo-express-basicauth-username>`
    - `export ME_CONFIG_BASICAUTH_PASSWORD=<mongo-express-basicauth-password>`
  - .env File
    - Create a file called `.env` alongside the docker-compose.yml file (see `template.env` in the repo)
- Issue one of the following commands:
  - Local Build: `docker compose up -d --build`
  - Develop Branch Build: `docker compose -f docker-compose-develop.yml up -d --build`
  - Master Branch Build: `docker compose -f docker-compose-master.yml up -d --build`


### Configuration
The host ports mapped for the slack server and webserver should be configured in the docker compose file, however it is also possible to override the ports in the server configs directly if you are not using docker.

## SMIBHID
[SMIBHID](smibhid/README.md) is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device run on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Further documentation can be found [in the smibhid folder](smibhid/).