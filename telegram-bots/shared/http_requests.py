import requests


class http_requests:
    def __init__(self, catalog_url):
        self.catalog_url = catalog_url

    def retrieve_url(self, endpoint_type):
            """
            Retrieve an endpoint URL from a catalog service using an HTTP GET request.

            :param endpoint_type: The type of endpoint to retrieve.
            :return: The URL of the endpoint.
            """
            request_url = f"{self.catalog_url}/retrieve_endpoint?endpoint_type={endpoint_type}"
            try:
                response = requests.get(request_url)
                response.raise_for_status()  # raise exception for non-2xx status codes
                url = response.json()
            except (requests.exceptions.RequestException, ValueError):
                error_msg = f"Failed to retrieve {endpoint_type} endpoint URL from catalog"
                raise Exception(error_msg)
            return url

    def GET(self,service_url, action, params=None):
        """
        Makes a GET request to a MongoDB adaptor using HTTP methods.
        :param adaptor_url: The URL of the MongoDB adaptor.
        :param action: The action to perform on the adaptor.
        :param params: Optional dictionary of query parameters.
        :return: The response object from the MongoDB adaptor.
        """
        url = f"{service_url}/{action}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status() # raise exception for 4xx and 5xx status codes
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to retrieve {action} from: {service_url}: {e}"
            raise Exception(error_msg)
        return response
    
    def POST(self, service_url, action, payload, params=None):
        """
        Makes a POST request to a MongoDB adaptor using HTTP methods.
        :param adaptor_url: The URL of the MongoDB adaptor, it could be the DATA adaptor on the ENDPOINT adaptor.
        :param action: The action to perform on the adaptor.
        :param payload: A dictionary containing the data to be sent.
        :return: The JSON response from the MongoDB adaptor.
        """
        url = f"{service_url}/{action}"
        headers = {'Content-type': 'application/json'}
        try:
            response = requests.post(url, headers=headers, json=payload, params=params)
            response.raise_for_status() # raise exception for 4xx and 5xx status codes
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to retrieve {action} from {service_url}: {e}"
            raise Exception(error_msg)
        return response
    
    def PUT(self, service_url, action, payload, params=None):
        """
        Makes a PUT request to a MongoDB adaptor using HTTP methods.
        :param adaptor_url: The URL of the MongoDB adaptor, it could be the DATA adaptor on the ENDPOINT adaptor.
        :param action: The action to perform on the adaptor.
        :param payload: A dictionary containing the data to be sent.
        :param params: A dictionary containing query parameters to be sent.
        :return: The JSON response from the MongoDB adaptor.
        """
        url = f"{service_url}/{action}"
        headers = {'Content-type': 'application/json'}
        try:
            response = requests.put(url, params=params, headers=headers, json=payload)
            response.raise_for_status() # raise exception for 4xx and 5xx status codes
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to update {action} on {service_url}: {e}"
            raise Exception(error_msg)
        return response

    def DELETE(self, service_url, action, params=None):
        """
        Makes a DELETE request to a MongoDB adaptor using HTTP methods.
        :param adaptor_url: The URL of the MongoDB adaptor, it could be the DATA adaptor on the ENDPOINT adaptor.
        :param action: The action to perform on the adaptor.
        :param params: A dictionary containing query parameters to be sent.
        :return: The JSON response from the MongoDB adaptor.
        """
        url = f"{service_url}/{action}"
        headers = {'Content-type': 'application/json'}
        try:
            response = requests.delete(url, params=params, headers=headers)
            response.raise_for_status() # raise exception for 4xx and 5xx status codes
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to delete {action} from {service_url}: {e}"
            raise Exception(error_msg)
        return response