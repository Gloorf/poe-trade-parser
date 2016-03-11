#!/bin/bash
cd /home/glorf/code/poe-trade-parser/api
/usr/bin/python3.5 stats.py >> cron.log 2>&1
