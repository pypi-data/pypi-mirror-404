import mimetypes
import os
import urllib.parse
from typing import Tuple, IO, overload, Literal, Any, Dict

from kiss_headers import parse_it
from square_commons.api_utils import (
    StandardResponse,
    make_request,
)

from square_file_store_helper.pydantic_models import (
    UploadFileV0Response,
    DeleteFilesV0Response,
)


class SquareFileStoreHelper:
    def __init__(
        self,
        param_str_square_file_store_protocol: str = "http",
        param_str_square_file_store_ip: str = "localhost",
        param_int_square_file_store_port: int = 10100,
    ):
        try:
            self.global_str_square_file_store_url_base = (
                f"{param_str_square_file_store_protocol}://"
                f"{param_str_square_file_store_ip}:{param_int_square_file_store_port}"
            )
        except Exception:
            raise

    @overload
    def upload_file_using_file_path_v0(
        self,
        file_path: str,
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[UploadFileV0Response]: ...

    @overload
    def upload_file_using_file_path_v0(
        self,
        file_path: str,
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def upload_file_using_file_path_v0(
        self,
        file_path: str,
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
        response_as_pydantic: bool = False,
    ) -> Any:
        try:
            endpoint = "upload_file/v0"
            data = {
                "app_id": app_id,
                "system_relative_path": system_relative_path,
            }
            with open(file_path, "rb") as file:
                filename = os.path.basename(file_path)
                content_type = (
                    mimetypes.guess_type(filename)[0] or "application/octet-stream"
                )
                files = {"file": (filename, file, content_type)}
                response = make_request(
                    method="POST",
                    url=self.global_str_square_file_store_url_base,
                    endpoint=endpoint,
                    data=data,
                    files=files,
                    return_type="json",
                )
            if response_as_pydantic:
                return StandardResponse[UploadFileV0Response](**response)
            else:
                return response

        except Exception:
            raise

    @overload
    def upload_file_using_tuple_v0(
        self,
        file: Tuple[str, IO, str],
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[UploadFileV0Response]: ...

    @overload
    def upload_file_using_tuple_v0(
        self,
        file: Tuple[str, IO, str],
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def upload_file_using_tuple_v0(
        self,
        file: Tuple[str, IO, str],
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
        response_as_pydantic: bool = False,
    ) -> Any:
        try:
            endpoint = "upload_file/v0"
            data = {
                "app_id": app_id,
                "system_relative_path": system_relative_path,
            }

            files = {"file": file}
            response = make_request(
                method="POST",
                url=self.global_str_square_file_store_url_base,
                endpoint=endpoint,
                data=data,
                files=files,
                return_type="json",
            )
            if response_as_pydantic:
                return StandardResponse[UploadFileV0Response](**response)
            else:
                return response
        except Exception:
            raise

    def download_file_v0(self, file_storage_token: str, output_folder_path: str) -> str:
        """
        :param file_storage_token:
        :param output_folder_path:
        :return: filepath
        """
        try:
            endpoint = "download_file/v0"
            payload = {
                "file_storage_token": file_storage_token,
            }
            response = make_request(
                method="GET",
                url=self.global_str_square_file_store_url_base,
                endpoint=endpoint,
                params=payload,
                return_type="response",
            )
            if not os.path.exists(output_folder_path):
                os.mkdir(output_folder_path)

            headers = parse_it(response)
            if headers.content_disposition.has("filename*"):
                file_name = urllib.parse.unquote(
                    headers.content_disposition["filename*"][7:]
                )
            elif headers.content_disposition.has("filename"):
                file_name = headers.content_disposition["filename"]
            else:
                raise Exception(
                    f"unable to download file - not able to get file name. headers: {headers}",
                )

            downloaded_file_path = output_folder_path + os.sep + file_name
            with open(downloaded_file_path, "wb") as file:
                file.write(response.content)

            return downloaded_file_path

        except Exception:
            raise

    @overload
    def delete_file_v0(
        self,
        list_file_storage_token: list,
        response_as_pydantic: Literal[True] = ...,
    ) -> StandardResponse[DeleteFilesV0Response]: ...

    @overload
    def delete_file_v0(
        self,
        list_file_storage_token: list,
        response_as_pydantic: Literal[False] = ...,
    ) -> Dict[str, Any]: ...

    def delete_file_v0(
        self,
        list_file_storage_token: list,
        response_as_pydantic: bool = False,
    ) -> Any:
        """
        :param response_as_pydantic:
        :param list_file_storage_token:
        :return: filepath
        """
        try:
            endpoint = "delete_files/v0"
            params = {
                "file_storage_tokens": list_file_storage_token,
            }
            response = make_request(
                method="DELETE",
                url=self.global_str_square_file_store_url_base,
                endpoint=endpoint,
                params=params,
                return_type="json",
            )
            if response_as_pydantic:
                return StandardResponse[DeleteFilesV0Response](**response)
            else:
                return response
        except Exception:
            raise
