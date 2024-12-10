from decouple import config

ENV = config("ENV")

if ENV == "dev":
    from .docker_dev import *
elif ENV == "prod":
    from .docker_prod import *