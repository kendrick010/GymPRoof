# GymProof

Discord bot gym (and routine) gamified tracker

## Background

My friend proposed a deal where he must send me pictures/selfies of himself at the gym or completing his daily routines; if he failed to do so, he would lose money. On my stakes, I was responsible for enforcing and reminding him of these rules, and if I didn’t, I would also lose money.

Engineers are very lazy, so I made a Discord bot that automates my bid of the deal while I make passive income lol.

## Discord Bot

Numerous chore commands and a balance system is implemented for participating members.

![gif](/img/discord.gif)

## Building

Build and integration are ran through GitHub Actions and an Ubuntu `systemd` service 

GitHub Actions Runner Service:

`sudo nano /etc/systemd/system/github-runner.service`
```
[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
ExecStart=/bin/bash /home/pi/actions-runner/run.sh
WorkingDirectory=/home/pi/actions-runner
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Application Service:

`sudo nano /etc/systemd/system/gym_proof.service`
```
[Unit]
Description=GymPRoof Bot
After=network.target

[Service]
ExecStart=/bin/bash /home/pi/GymPRoof/run.sh
WorkingDirectory=/home/pi/GymPRoof
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```