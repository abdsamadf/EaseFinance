# EaseFinance
Stock-trading website [Live Version](https://ease-finance.herokuapp.com)

EA$E Finance, a web app which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks' actual prices and portfolios' values, it will also let you buy (okay, "buy") and sell (okay, "sell") stocks by querying IEX for stocks' prices.

## Get Started

Click on this [link](https://ease-finance.herokuapp.com) to see the website **or** you can download or clone the project.

## TECHNOLOGY USED

* HTML & CSS
* Python
* Flask
* Bootstrap
* [IEX trading](https://iextrading.com)
* SQLite
* Postgresql database
* [Memegen](https://memegen.link)

## How to install on your server

* You can download the zip or clone the project with git.

    `https://github.com/abdsamadf/similarities.git`

* Install `requirement.txt` via terminal:

    `pip install -r /path/to/requirements.txt`

## Running the site

* To enable all development features (including debug mode) you can export the FLASK_ENV environment variable and set it to development before running the server:

    `export FLASK_ENV=development`

* To run the application you can use the **flask** command or python’s -m switch with Flask. Before you can do that you need to tell your terminal the application to work with by exporting the **FLASK_APP** environment variable:

    `export FLASK_APP=application.py`

* To test the web app, execute

    ``` Shell
    $ flask run
        * Running on http://127.0.0.1:5000/
    ```

* Alternatively you can use python -m flask:
    ``` Shell
    $ python -m flask run
        * Running on http://127.0.0.1:5000/
    ```

## Requirements

* Python
* Flask