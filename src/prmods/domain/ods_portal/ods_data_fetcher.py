import json
import requests


ODS_PORTAL_SEARCH_URL = "https://directory.spineservices.nhs.uk/ORD/2-0-0/organisations"
PRACTICE_SEARCH_PARAMS = {
    "PrimaryRoleId": "RO177",
    "Status": "Active",
    "NonPrimaryRoleId": "RO76",
    "Limit": "1000",
}
CCG_SEARCH_PARAMS = {
    "PrimaryRoleId": "RO98",
    "Status": "Active",
    "Limit": "1000",
}
CCG_PRACTICES_SEARCH_PARAMS = {
    "RelTypeId": "RE4",
    "RelStatus": "active",
    "Limit": "1000",
}

NEXT_PAGE_HEADER = "Next-Page"


class OdsPortalException(Exception):
    def __init__(self, message, status_code):
        super(OdsPortalException, self).__init__(message)
        self.status_code = status_code


class OdsDataFetcher:
    def __init__(self, client=requests, search_url=ODS_PORTAL_SEARCH_URL):
        self._search_url = search_url
        self._client = client

    def fetch_organisation_data(self, params):
        response_data = list(self._iterate_organisation_data(params))
        return response_data

    def _iterate_organisation_data(self, params):
        try:
            response = self._client.get(self._search_url, params)
            yield from self._process_practice_data_response(response)

            while NEXT_PAGE_HEADER in response.headers:
                response = self._client.get(response.headers[NEXT_PAGE_HEADER])
                yield from self._process_practice_data_response(response)
        except StopIteration:
            pass

    @classmethod
    def _process_practice_data_response(cls, response):
        if response.status_code != 200:
            raise OdsPortalException("Unable to fetch organisation data", response.status_code)
        return json.loads(response.content)["Organisations"]
