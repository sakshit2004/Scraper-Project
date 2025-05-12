@echo off
REM Batch script to run Scrapy spiders sequentially and send output to MongoDB

REM Ensure we are in the correct directory relative to this script
cd /d "%~dp0"

REM The MONGO pipeline in settings.py handles the output location

echo Running spider: lincoln_county
scrapy crawl lincoln_county
if %errorlevel% neq 0 (
    echo Error running lincoln_county spider.
    goto :eof
)

echo Running spider: cab_minutes
scrapy crawl cab_minutes
if %errorlevel% neq 0 (
    echo Error running cab_minutes spider.
    goto :eof
)

echo.
echo Spiders finished. Output sent to MongoDB.

:eof
pause 