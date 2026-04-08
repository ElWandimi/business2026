#!/bin/bash
cd /Users/wandimiek/Desktop/business2026
source venv/bin/activate
export $(grep -v '^#' .env | xargs)  # loads .env variables
flask send-abandoned-cart-emails