docker run -itd --rm \
    -e MH_USERNAME='username' \
    -e MH_PASSWORD='password' \
    -e TELEGRAM_TOKEN='token' \
    -e TELEGRAM_CHAT_ID='chatid' \
    -e TRIGGERS='Map Clue,Ancient Relic' \
mh_bot
