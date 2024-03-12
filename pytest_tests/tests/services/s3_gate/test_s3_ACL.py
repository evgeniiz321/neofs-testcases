import allure
import pytest
from helpers.file_helper import generate_file
from helpers.s3_helper import assert_bucket_s3_acl, assert_object_s3_acl, object_key_from_file_path
from s3 import s3_gate_bucket, s3_gate_object
from s3.s3_gate_base import TestNeofsS3GateBase


def pytest_generate_tests(metafunc):
    if "s3_client" in metafunc.fixturenames:
        metafunc.parametrize("s3_client", ["aws cli", "boto3"], indirect=True)


@pytest.mark.acl
@pytest.mark.s3_gate
class TestS3GateACL(TestNeofsS3GateBase):
    @pytest.mark.sanity
    @allure.title("Test S3: Object ACL")
    def test_s3_object_ACL(self, bucket, simple_object_size):
        file_path = generate_file(simple_object_size)
        file_name = object_key_from_file_path(file_path)

        with allure.step("Put object into bucket, Check ACL is empty"):
            s3_gate_object.put_object_s3(self.s3_client, bucket, file_path)
            obj_acl = s3_gate_object.get_object_acl_s3(self.s3_client, bucket, file_name)
            assert obj_acl == [], f"Expected ACL is empty, got {obj_acl}"

        with allure.step("Put object ACL = public-read"):
            acl = "public-read"
            s3_gate_object.put_object_acl_s3(self.s3_client, bucket, file_name, acl)
            obj_acl = s3_gate_object.get_object_acl_s3(self.s3_client, bucket, file_name)
            assert_object_s3_acl(
                acl_grants=obj_acl, permitted_users="AllUsers", acl="public-read-write"
            )

        with allure.step("Put object ACL = private"):
            acl = "private"
            s3_gate_object.put_object_acl_s3(self.s3_client, bucket, file_name, acl)
            obj_acl = s3_gate_object.get_object_acl_s3(self.s3_client, bucket, file_name)
            assert_object_s3_acl(acl_grants=obj_acl, permitted_users="CanonicalUser", acl=acl)

        with allure.step(
            "Put object with grant-read uri=http://acs.amazonaws.com/groups/global/AllUsers"
        ):
            s3_gate_object.put_object_acl_s3(
                self.s3_client,
                bucket,
                file_name,
                grant_read="uri=http://acs.amazonaws.com/groups/global/AllUsers",
            )
            obj_acl = s3_gate_object.get_object_acl_s3(self.s3_client, bucket, file_name)
            assert_object_s3_acl(
                acl_grants=obj_acl, permitted_users="AllUsers", acl="public-read-write"
            )

    @allure.title("Test S3: Bucket ACL")
    def test_s3_bucket_ACL(self):
        with allure.step("Create bucket with ACL = public-read-write"):
            acl = "public-read-write"
            bucket = s3_gate_bucket.create_bucket_s3(
                self.s3_client,
                object_lock_enabled_for_bucket=True,
                acl=acl,
                bucket_configuration="rep-1",
            )
            bucket_acl = s3_gate_bucket.get_bucket_acl(self.s3_client, bucket)
            assert_bucket_s3_acl(acl_grants=bucket_acl, permitted_users="AllUsers", acl=acl)

        with allure.step("Change bucket ACL to private"):
            acl = "private"
            s3_gate_bucket.put_bucket_acl_s3(self.s3_client, bucket, acl=acl)
            bucket_acl = s3_gate_bucket.get_bucket_acl(self.s3_client, bucket)
            assert_bucket_s3_acl(acl_grants=bucket_acl, permitted_users="CanonicalUser", acl=acl)

        with allure.step(
            "Change bucket acl to --grant-write uri=http://acs.amazonaws.com/groups/global/AllUsers"
        ):
            s3_gate_bucket.put_bucket_acl_s3(
                self.s3_client,
                bucket,
                grant_write="uri=http://acs.amazonaws.com/groups/global/AllUsers",
            )
            bucket_acl = s3_gate_bucket.get_bucket_acl(self.s3_client, bucket)
            assert_bucket_s3_acl(
                acl_grants=bucket_acl, permitted_users="AllUsers", acl="public-read-write"
            )
