from django.db import models
from django.core.exceptions import ValidationError


class CustomUser(models.Model):
    username = models.CharField(max_length=12, unique=True)
    email_id = models.EmailField(primary_key=True, blank=False)
    password = models.CharField(max_length=32, blank=False)

    # Django default required fields below
    # (auth.E002)
    # The field named as the 'USERNAME_FIELD' for a custom user model must not be included in 'REQUIRED_FIELDS'.
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email_id"
    REQUIRED_FIELDS = ['email_id', 'password']

    @property
    def is_anonymous(self):
        """
        Always return False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True


class LockedRowUpdateRequest(Exception):
    pass


class PrimaryKeyMissingException(Exception):
    pass


class Inventory(models.Model):
    product_id = models.CharField(max_length=10, primary_key=True)
    product_name = models.CharField(max_length=32)
    vendor = models.CharField(max_length=32)
    mrp = models.FloatField()
    batch_num = models.CharField(max_length=32)
    batch_date = models.DateField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=8, choices=[("APPROVED","APPROVED"), ("PENDING","PENDING")])


# Contains the field
class Approvals(models.Model):
    product_id = models.CharField(max_length=10)
    product_name = models.CharField(max_length=32)
    vendor = models.CharField(max_length=32)
    mrp = models.FloatField()
    batch_num = models.CharField(max_length=32)
    batch_date = models.DateField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=8, choices=[("APPROVED", "APPROVED"), ("PENDING", "PENDING")])

    email_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=False)
    request_id = models.CharField(max_length=32, blank=False)
    operation = models.CharField(max_length=10, choices=[("UPDATE","UPDATE"), ("CREATE","CREATE"), ("DELETE","DELETE")])


class ApprovalsHandler:
    @staticmethod
    def create_approval(data_list, operation, requester_email, request_id):
        # Not validating anything here, as the caller model handler is expected to do validations before sending
        for row_dict in data_list:
            new_approval_row = Approvals()
            new_approval_row.request_id = request_id
            new_approval_row.email_id = requester_email
            new_approval_row.operation = operation
            # All attributes are not required for the delete operation
            if operation == "DELETE":
                new_approval_row.product_id = row_dict['product_id']
            else:
                for sent_attribute, sent_attribute_value in row_dict.items():
                    setattr(new_approval_row,sent_attribute, sent_attribute_value)
            new_approval_row.status = "PENDING"
            new_approval_row.save()

    @staticmethod
    def approve_request(approval_row_id):
        try:
            approval_object = Approvals.objects.get(id=approval_row_id)
            row_dict = {
                "product_id" :
                    approval_object.product_id,
                "product_name" : approval_object.product_name,
                "vendor" : approval_object.vendor,
                "mrp" : approval_object.mrp,
                "batch_num" : approval_object.batch_num,
                "batch_date" : approval_object.batch_date,
                "quantity": approval_object.quantity,
                "status": "PENDING"
            }
            if approval_object.operation == "UPDATE" or approval_object.operation == "CREATE":
                res, msg = InventoryHandler.update(data_list=[row_dict], operation=approval_object.operation, is_admin=True)
            elif approval_object.operation == "DELETE":
                res, msg = InventoryHandler.delete(data_list=[row_dict], is_admin=True)
            if res:
                approval_object.delete()
            return res, msg
        except Approvals.DoesNotExist:
            return False, "Invalid Approval ID"

    @staticmethod
    def deny_request(approval_row_id):
        try:
            approval_object = Approvals.objects.get(id=approval_row_id)
            approval_object.delete()
            return True, "Successfully deleted the Approval"
        except Approvals.DoesNotExist:
            return False, "Approval ID does not exist"


class InventoryHandler:
    required_fields = ['product_id', 'product_name']
    primary_key = 'product_id'

    @staticmethod
    def update(data_list, operation, is_admin=False):
        """
        :param operation: string, Allowed Values => "UPDATE", "CREATE"
        :param is_admin: bool, If this request is from an admin, this shall be written immediately, else status set as PENDING
        :param data_list: list of dicts, where each dict should have keys as database column names
        value for key as the new value for that filed in the row.
        :return:bool, str
        bool => Status if successfully Updated or not
        str => Message for both Failure or Success
        """
        success_status = False
        message = "Unknown Error"
        try:
            models_to_save = []
            for row_dict in data_list:
                # Try to get an object using the primary key
                # Raises PrimaryKeyMissingException if product_id is not sent
                # Raises Inventory.DoesNotExist if illegal primary key
                if not ('product_id' in row_dict and row_dict['product_id']):
                    raise PrimaryKeyMissingException
                if operation == "UPDATE":
                    required_model = Inventory.objects.get(product_id=row_dict['product_id'])
                else:
                    required_model = Inventory()
                if required_model.status == "PENDING":
                    raise LockedRowUpdateRequest
                for sent_attribute in row_dict:
                    # Ensure that the sent field is actually a field. Raises AttributeError if Illegal field
                    getattr(required_model, sent_attribute)
                    # Ensure that no operations are done on the primary key field in case of UPDATE operations
                    if operation == "UPDATE" and sent_attribute in ["product_id", "status"]:
                        continue
                    # Set the sent attribute's value to the one sent
                    setattr(required_model, sent_attribute, row_dict[sent_attribute])
                required_model.full_clean()  # Raises validation Errors if any
                models_to_save.append(required_model)   # Keep all model references to save at the end
            for model_to_update in models_to_save:
                if is_admin:
                    model_to_update.status = "APPROVED"
                    model_to_update.save()
                else:
                    # Change values once user table is updated
                    ApprovalsHandler.create_approval(
                        data_list=data_list,
                        operation=operation,
                        requester_email= CustomUser.objects.get(email_id="dummy@gmail.com"),
                        request_id="ABCDF"
                    )
                    if operation == "UPDATE":
                        model_to_update.status = "PENDING"
                        model_to_update.save(update_fields=['status'])
        except AttributeError:
            message = "Illegal Attribute sent"
        except Inventory.DoesNotExist:
            message = "Requested value does not exist"
        except ValidationError as e:
            message = e.message_dict
        except LockedRowUpdateRequest:
            message = "A Locked Row has been requested to be changed"
        except PrimaryKeyMissingException:
            message = "Primary key not sent"
        else:
            success_status = True
            message = "All attributes updated successfully"
            if not is_admin:
                message = message + " (subject to Admin approval)"
        return success_status, message

    @staticmethod
    def delete(data_list, is_admin=False):
        all_models_to_delete = []
        success_status = False
        message = "Unknown Error"
        try:
            for row_dict in data_list:
                if 'product_id' not in row_dict:
                    raise PrimaryKeyMissingException
                model_to_delete = Inventory.objects.get(product_id=row_dict['product_id'])
                if model_to_delete.status == "PENDING":
                    raise LockedRowUpdateRequest
                all_models_to_delete.append(model_to_delete)

            for model_to_delete in all_models_to_delete:
                if is_admin:
                    model_to_delete.delete()
                else:
                    # Change values once user table is updated
                    ApprovalsHandler.create_approval(
                        data_list=data_list,
                        operation="DELETE",
                        requester_email= CustomUser.objects.get(email_id="dummy@gmail.com"),
                        request_id="ABCDF"
                    )
                    model_to_delete.status = "PENDING"
                    model_to_delete.save(update_fields=['status'])
        except Inventory.DoesNotExist:
            message = "Requested Object Does not exist"
        except LockedRowUpdateRequest:
            message = "A Locked Row has been requested to be changed"
        except PrimaryKeyMissingException:
            message = "Primary key not sent"
        else:
            success_status = True
            message = "All attributes updated successfully"
            if not is_admin:
                message = message + " (subject to Admin approval)"
        return success_status, message
