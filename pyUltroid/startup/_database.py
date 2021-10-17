"""
For multiple database support!
redis cant be remove completely
since, it will be a breaking change
"""

import os

from redis import Redis
from . import LOGS
from ..configs import Var

try:
    from deta import Deta
except ImportError:
    Deta = None

# --------------------------------------------------------------------------------------------- #


def get_data(self_, key):
    data = None
    if self_.get(str(key)):
        try:
            data = eval(self_.get(str(key)))
        except BaseException:
            data = self_.get(str(key))
    return data


# --------------------------------------------------------------------------------------------- #


class DetaDB:
    def __init__(self, key):
        try:
            self.db = Deta(key).Base("Ultroid")
        except Exception as er:
            LOGS.exception(er)

    def set(self, key, value):
        if not self.get(str(key)):
            self.db.insert(str(value), str(key))
            return True
        params = {"value": str(value)}
        self.db.update(params, str(key))
        return True

    def get(self, key, cast=str):
        _get = self.db.get(key)
        if _get:
            return cast(_get["value"])

    def delete(self, key):
        self.db.delete(key)
        return True

    def ping(self):
        """Deta dont have ping endpoint, while Redis have.."""
        return True

    set_key = set
    del_key = delete

    def get_key(self, key):
        return get_data(self, key)


# --------------------------------------------------------------------------------------------- #


class RedisConnection(Redis):
    def __init__(
        self,
        host,
        port,
        password,
        platform=None,
        logger=LOGS,
        *args,
        **kwargs,
    ):
        if host and ":" in host:
            spli_ = host.split(":")
            host = spli_[0]
            port = int(spli_[-1])
            if host.startswith("http"):
                logger.error("Your REDIS_URI should not start with http !")
                exit()
        elif not host or not port:
            logger.error("Port Number not found")
            exit()
        kwargs["host"] = host
        kwargs["password"] = password
        kwargs["port"] = port

        if platform.lower() == "qovery" and not host:
            var, hash_, host, password = "", "", "", ""
            for vars_ in os.environ:
                if vars_.startswith("QOVERY_REDIS_") and vars.endswith("_HOST"):
                    var = vars_
            if var:
                hash_ = var.split("_", maxsplit=2)[1].split("_")[0]
            if hash:
                kwargs["host"] = os.environ(f"QOVERY_REDIS_{hash_}_HOST")
                kwargs["port"] = os.environ(f"QOVERY_REDIS_{hash_}_PORT")
                kwargs["password"] = os.environ(f"QOVERY_REDIS_{hash_}_PASSWORD")
        if logger:
            logger.info("Connecting to redis database")
        super().__init__(**kwargs)

    def set_key(self, key, value):
        return self.set(str(key), str(value))

    def get_key(self, key):
        return get_data(self, key)

    def del_key(self, key):
        return bool(self.delete(str(key)))


# --------------------------------------------------------------------------------------------- #


def UltroidDB():
    if Deta and Var.DETA_KEY:
        return DetaDB(Var.DETA_KEY)
    from .. import HOSTED_ON

    return RedisConnection(
        host=Var.REDIS_URI or Var.REDISHOST,
        password=Var.REDIS_PASSWORD or Var.REDISPASSWORD,
        port=Var.REDISPORT,
        platform=HOSTED_ON,
        decode_responses=True,
        socket_timeout=5,
        retry_on_timeout=True,
    )


# --------------------------------------------------------------------------------------------- #