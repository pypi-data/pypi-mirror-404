import appdirs
import canvaslms.cli
import json
import keyring
import os

dirs = appdirs.AppDirs("canvaslms", "dbosk@kth.se")


def login_command(config, canvas, args):
    """Guides the user to update credentials"""

    print(
        "Enter the hostname for Canvas, "
        "e.g. 'canvas.kth.se' or 'kth.instructure.com'."
    )
    hostname = input("Canvas hostname: ")

    print(f"""
Open

  https://{hostname}/profile/settings

in your browser. Scroll down to approved integrations and click the
'+ New access token' button. Fill in the required data and click the
'Generate token' button. Enter the token here.
""")

    token = input("Canvas token: ")

    try:
        keyring.set_password("canvaslms", "hostname", hostname)
        keyring.set_password("canvaslms", "token", token)
    except:
        canvaslms.cli.warn(
            f"You don't have a working keyring. "
            f"Will write hostname and token to config file "
            f"{args.config_file}."
        )

        config["canvas"]["host"] = hostname
        config["canvas"]["access_token"] = token

        canvaslms.cli.update_config_file(config, args.config_file)


def load_credentials(config):
    """Load credentials from keyring, environment or config dictionary"""
    try:
        hostname = keyring.get_password("canvaslms", "hostname")
        token = keyring.get_password("canvaslms", "token")
        if hostname and token:
            return hostname, token
    except:
        pass

    try:
        hostname = os.environ["CANVAS_SERVER"]
        token = os.environ["CANVAS_TOKEN"]
        return hostname, token
    except KeyError:
        pass

    try:
        return config["canvas"]["host"], config["canvas"]["access_token"]
    except KeyError:
        pass

    return None, None


def add_command(subp):
    """Adds the login command to argparse parser"""
    login_parser = subp.add_parser(
        "login",
        help="Manage login credentials",
        description=f"""
Manages the user's Canvas login credentials. There are three ways to supply the 
login credentials, in order of priority:

1) Through the system keyring: Just run `canvaslms login` and you'll be guided 
   to enter the credentials (server name and token) and they will be stored in 
   the keyring.

2) Through the environment: Just set the environment variables CANVAS_SERVER 
   and CANVAS_TOKEN.

3) Through the configuration file: Just write

      {{
        "canvas": {{
          "host": "the actual hostname",
          "access_token": "the actual token"
        }}
      }}

   to the file {dirs.user_config_dir}/config.json (default, or use the -f 
   option, see `canvaslms -h`).
""",
    )
    login_parser.set_defaults(func=login_command)
