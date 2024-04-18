#!/usr/bin/env bash

cd -- "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}This script will update Coyote Badger to the newest version.${NC}"
echo -e "${CYAN}All of your past projects and custom settings will be saved.${NC}"
echo -e "${CYAN}This update may take a minute. Do not close this window while the update is in progress.${NC}"
echo -e "${YELLOW}Press any key to continue...${NC}"
read -n 1 -s -r key

./__MAC-STOP.command
curl -L https://api.github.com/repos/alexsands/coyote-badger/zipball > cb_next.tar.gz
tar -xzvf "cb_next.tar.gz"
mv alexsands-coyote-badger-* cb_next/
rm -rf cb_next/_projects
cp -r cb_next/* .
rm -rf cb_next/
rm -rf cb_next.tar.gz

echo -e "${GREEN}Coyote Badger is now up to date.${NC}"
echo -e "${YELLOW}Press any key to close this window...${NC}"
read -n 1 -s -r key
exit
