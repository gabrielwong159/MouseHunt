docker run -itd --rm \
    --name mh-bot \
    -e MH_USERNAME='gabrielwong159' \
    -e MH_PASSWORD='Xavier54!' \
    -e TELEGRAM_TOKEN='400100352:AAEuaQsxsJqjxRGdWcvGQdiMFFDhm8ccckU' \
    -e TELEGRAM_CHATID='218740835' \
    -e TRAP_CHECK=45 \
    -e TRIGGERS='Map Clue,Ancient Relic' \
    mh_bot:latest
