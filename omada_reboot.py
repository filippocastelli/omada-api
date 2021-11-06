from pathlib import Path
from typing import List
from datetime import datetime

import json
import requests
import yaml


class OmadaAPI:

    def __init__(self,
                 config_fpath: Path = Path("config.yml"),
                 baseurl: str = None,
                 site: str = "Default",
                 verify: bool = True):

        self.config_fpath = Path(config_fpath)
        self.token = None
        self.base_api_path = "/api/v2"

        if self.config_fpath.is_file():
            self.config_dict = self.read_yml(self.config_fpath)
            self.baseurl = self.config_dict["baseurl"]
            self.site = self.config_dict["site"]
            self.verify = self.config_dict["verify"]

            self.login_username = self.config_dict["username"]
            self.login_password = self.config_dict["password"]
        else:
            self.baseurl = baseurl
            self.site = site
            self.verify = verify

            self.login_username, self.login_password = self.login_prompt()

        self.session = requests.Session()
        self.session.verify = self.verify

        # get the token
        self.login_token = self.login()

    @staticmethod
    def read_yml(yml_fpath: Path):
        """read a yml config file"""
        with yml_fpath.open(mode="r") as infile:
            cfg = yaml.load(infile, Loader=yaml.FullLoader)
        return cfg

    @staticmethod
    def get_timestamp() -> int:
        return int(datetime.utcnow().timestamp() * 1000)

    def path_to_url(self, path: str):
        return self.baseurl + self.base_api_path + path

    def makeApiCall(self,
                    url: str = None,
                    mode: str = "GET",
                    endpoint_params: dict = None,
                    data: dict = None,
                    json: dict = None,
                    debug: bool = False,
                    include_token: bool = True,
                    bare_url: str = False) -> dict:
        """
        make an API call to the Omada API
        :param json: the json to send
        :param data: the data to send
        :param url: the url to call
        :param mode: the HTTP method to use
        :param endpoint_params: the parameters to send to the endpoint
        :param debug: print the response
        :param include_token: include the token in the request
        :param bare_url: don't include the base url
        :return: the response
        """

        if not bare_url:
            url = self.path_to_url(url)

        if include_token:
            endpoint_params.update({
                "token": self.token,
                "_": self.get_timestamp()
            })

        if mode == "GET":
            data = self.session.get(url=url,
                                    params=endpoint_params)
        elif mode == "POST":
            data = self.session.post(url=url,
                                     params=endpoint_params,
                                     data=data,
                                     json=json)
        elif mode == "PATCH":
            data = self.session.patch(url=url,
                                      params=endpoint_params,
                                      data=data,
                                      json=json)
        else:
            raise ValueError(f"Unsupported mode {mode}")

        # get the json response
        response = data.json()

        response = {
            "url": url,
            "endpoint_params": endpoint_params,
            "endpoint_params_pretty": self.safe_json_serialize(endpoint_params),
            "json_data": response,
            "json_data_pretty": self.safe_json_serialize(response)
        }

        if debug:
            print("\nURL:")
            print(response["url"])
            print("\nEndpoint Params:")
            print(response["endpoint_params_pretty"])
            print("\nResponse:")
            print(response["json_data_pretty"])
        return response

    @staticmethod
    def safe_json_serialize(obj, indent=4):
        """
        serialize an object to json, but don't fail if it can't be serialized
        :param obj: the object to serialize
        :param indent: the indentation level
        :return: the serialized object
        """

        return json.dumps(obj, default=lambda o: f"<<non-serializable: {type(o).__qualname__}>>")

    def login_prompt(self) -> (str, str):
        """
        prompt the user for login credentials
        :return: the username and password
        """

        login_username = input("Omada login: \n")
        login_password = input("password: \n")

        endpoint_params = {
            "username": "login_username",
            "password": "login_password"
        }
        result = self.makeApiCall(url="/login",
                                  endpoint_params=endpoint_params)
        print(result)
        return None, None

    def login(self):
        """
        login to the Omada API
        :return: the token
        """

        json_dict = {
            "username": self.login_username,
            "password": self.login_password
        }
        result = self.makeApiCall(url="/login",
                                  json=json_dict,
                                  mode="POST",
                                  include_token=False,
                                  debug=True)
        self.token = result["json_data"]["result"]["token"]
        return self.token


if __name__ == "__main__":
    omada = OmadaAPI(config_fpath=Path("config.yml"))
