docker run -itd --rm \
    --name mh-bot \
    -e MH_USERNAME='username' \
    -e MH_PASSWORD='password' \
    -e TELEGRAM_TOKEN='token' \
    -e TELEGRAM_CHAT_ID='chatid' \
    -e TRAP_CHECK=0  # {0, 15, 30, 45} \
    -e TRIGGERS='Map Clue,Ancient Relic' \
    mh_bot
