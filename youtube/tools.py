import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from apiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

def get_authenticated_service(client_secrets_file, storage_path, args = None):
    """Get read only authenticated youtube service."""

    if args is None: args = argparser.parse_args()
    
    flow = flow_from_clientsecrets(client_secrets_file,
        scope="https://www.googleapis.com/auth/youtube.readonly",
        message="WARNING: Please configure OAuth 2.0.")

    storage = Storage("storage/{}-oauth2.json".format(storage_path))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build("youtube", "v3", http=credentials.authorize(httplib2.Http()))