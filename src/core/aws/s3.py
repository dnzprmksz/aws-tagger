from typing import List

import boto3 as boto3
from botocore.exceptions import ClientError

from src.core.aws.base_aws_service import BaseAwsService
from src.model.filter import Filter
from src.model.resource import Resource
from src.model.tag import Tag


class S3(BaseAwsService):

    def __init__(self):
        super().__init__(nice_name='S3', short_name='s3')
        self.client = boto3.client('s3')

    def _list_resources(self, filters: List[Filter]) -> List[Resource]:
        """
        List resources for the service.

        :param filters: List of filters to pass to AWS API, if supported.
        :return: List of resources.
        """
        response = self.client.list_buckets()
        resources = self.__list_response_to_resources(response)

        return resources

    @staticmethod
    def __list_response_to_resources(response) -> List[Resource]:
        """
        Convert a List API call response to a list of resources.

        :param response: Response from the List API call.
        :return: List of resources.
        """
        resources = [
            Resource(name=item['Name']) for item in response['Buckets']
        ]

        return resources

    def _get_resource_tags(self, resource: Resource) -> List[Tag]:
        """
        Get all tags for the given resource.

        :param resource: Resource.
        :return: List of tags for the resource.
        """
        try:
            response = self.client.get_bucket_tagging(Bucket=resource.name)
            tags = response['TagSet']
            tags = [Tag(tag['Key'], tag['Value']) for tag in tags]
        except ClientError as error:
            if error.response['Error']['Code'] == 'NoSuchTagSet':
                tags = []
            else:
                raise error

        return tags

    def tag_resource(self, resource: Resource, tags: List[Tag]) -> None:
        """
        Tag a resource with the given tags.

        :param resource: Resource.
        :param tags: List of tags to apply to the resource.
        """
        current_tags = self._get_resource_tags(resource)
        tag_keys = [tag.key for tag in tags]
        tags = tags + [tag for tag in current_tags if tag.key not in tag_keys]
        tags = [{'Key': tag.key, 'Value': tag.value} for tag in tags]

        self.client.put_bucket_tagging(
            Bucket=resource.name,
            Tagging={
                'TagSet': tags
            }
        )
