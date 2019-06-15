from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Inventory, InventoryHandler, Approvals, ApprovalsHandler, CustomUserManager
from .authorizer import auth_required
from .forms import InventoryForm, InventoryModelForm
from .exceptions import *
from django.core import serializers
import json


def inventoryitem(request, operation, user=None, product_id=None):
    context = {'error': "Unknown Error"}
    status_code = 401
    try:
        if operation == "CREATE":
            if request.method == "GET":
                context['form'] = InventoryModelForm()
            if request.method == "POST":
                form = InventoryModelForm(request.POST)
                context['form'] = form
                if not form.is_valid():
                    raise InvalidRequestException  # TODO: Append the validation Error in the thrown Error
                form.cleaned_data['status'] = "PENDING"
                data_list = [dict(form.cleaned_data)]
                res, msg = InventoryHandler.update(data_list=data_list, user=user, operation="CREATE")
                context['error'] = msg
                if not res:
                    raise OperationFailureException
        elif operation == "UPDATE" and product_id:
            if request.method == "GET":
                instance = Inventory.objects.get(product_id=product_id)
                form = InventoryModelForm(instance=instance)
                # TODO: Set non editable
                context['form'] = form
            if request.method == "POST":
                form = InventoryForm(request.POST)
                context['form'] = form
                if not form.is_valid():
                    raise InvalidRequestException   # TODO: Append the validation Error in the thrown Error
                form.cleaned_data['status'] = "PENDING"
                data_list = [dict(form.cleaned_data)]
                res, msg = InventoryHandler.update(data_list=data_list, user=user, operation="UPDATE")
                context['error'] = msg
                if not res:
                    raise OperationFailureException
        elif operation == "DELETE" and product_id:
            if request.method == "GET":
                instance = Inventory.objects.get(product_id=product_id)
                # TODO: If instance status is pending don't send the form in status, instead send error !
                form = InventoryModelForm(instance=instance)
                # TODO: Set non editable
                context['form'] = form
            if request.method == "POST":
                form = InventoryForm(request.POST)
                context['form'] = form
                if not form.is_valid():
                    raise InvalidRequestException  # TODO: Append the validation Error in the thrown Error
                form.cleaned_data['status'] = "PENDING"
                data_list = [dict(form.cleaned_data)]
                res, msg = InventoryHandler.delete(data_list=data_list, user=user)
                context['error'] = msg
                if not res:
                    raise OperationFailureException
    except Inventory.DoesNotExist:
        context['error'] = "Illegal Product ID requested for alteration"
    except InvalidRequestException:
        context['error'] = "Invalid Request"
    except OperationFailureException:
        pass  # The error message is already set
    else:
        status_code = 200
    return render(request=request, template_name="inventoryitem.html", context=context, status=status_code)


@csrf_exempt
@auth_required
def inventory(request, user=None):
    status_code = 200
    response_dict = {}
    try:
        if request.method == "GET":
            all_objects_json = serializers.serialize('json', Inventory.objects.all())
            retrieved_data = json.loads(all_objects_json)
            final_data = []
            for record in retrieved_data:
                record_dict = record['fields']
                record_dict['product_id'] = record['pk']
                final_data.append(record_dict)
            response_dict['InventoryRecords'] = final_data

        if request.method == "POST":
            if isinstance(json.loads(request.body), list):
                res, msg = InventoryHandler.update(data_list=json.loads(request.body), user=user, operation="UPDATE")
            else:
                status_code = 401
                response_dict['Message'] = "Illegal request body"
        if request.method == "PUT":
            res, msg = InventoryHandler.update(data_list=json.loads(request.body), user=user, operation="CREATE")
        if request.method == "DELETE":
            res, msg = InventoryHandler.delete(data_list=json.loads(request.body), user=user)
        if request.method != "GET" and not res:
            status_code = 401
            response_dict['Message'] = msg
        response_dict['Mesage'] = msg
    except Exception:
        pass
    if "web" in request.path:
        return render(request=request, template_name='inventory.html', context= response_dict, status=status_code)
    else:
        return JsonResponse(data=response_dict, safe=False, status=status_code)


@csrf_exempt
@auth_required
def approvals(request, user=None):
    """
    :param request:
    :param user:
    :return:
    {'id' : int} => IDs of the approvals that need to be approved
    """
    status_code = 200
    response_dict = {}
    if request.method == "GET":
        all_objects_json = serializers.serialize('json', Approvals.objects.all())
        response_dict = json.loads(all_objects_json)
    if request.method == "POST":
        if not CustomUserManager.is_admin(user=user):
            return JsonResponse(data={"Message": "Only admins are allowed to modify approvals"},  status=401)
        if 'id' in json.loads(request.body):
            res, msg = ApprovalsHandler.approve_request(approval_row_id=json.loads(request.body)['id'], user=user)
            if not res:
                status_code = 401
                response_dict['Message'] = msg
            else:
                response_dict["Message"] = msg
        else:
            status_code = 401
            response_dict['Message'] = "id Key missing"
    if request.method == "DELETE":
        if not CustomUserManager.is_admin(user=user):
            return JsonResponse(data={"Message": "Only admins are allowed to modify approvals"},  status=401)
        if 'id' in json.loads(request.body):
            res, msg = ApprovalsHandler.deny_request(approval_row_id=json.loads(request.body)['id'], user=user)
            if not res:
                status_code = 401
                response_dict['Message'] = msg
            else:
                response_dict["Message"] = msg
        else:
            status_code = 401
            response_dict['Message'] = "id Key missing"
    return JsonResponse(data=response_dict, safe=False, status=status_code)

@csrf_exempt
def login(request):
    message = {}
    status_code = 401
    try:
        if request.method != "POST":
            message['Error'] = "Please send a post request with required fields"
            raise IllegalMethodException
        if not request.body:
            raise IllegalBodyException
        request_body = json.loads(request.body)
        if not ('username' in request_body and request_body['username']):
            raise IllegalBodyException
        if not ('password' in request_body and request_body['password']):
            raise IllegalBodyException
        auth_token = CustomUserManager.authenticate(username=request_body['username'],
                                                    password=request_body['password'])
        if auth_token:
            message['x-inv-auth-token'] = auth_token
            status_code = 200
        else:
            message['Error'] = "Invalid Credentials"
    except IllegalMethodException:
        message['Error'] = "Illegal request type"
    except IllegalBodyException:
        message['Error'] = "Illegal body"
    return JsonResponse(data=message, status=status_code)


@csrf_exempt
def logout(request):
    status_code = 401
    message = {}
    try:
        if not ('x-inv-auth-token' in request.headers and request.headers['x-inv-auth-token']):
            raise IllegalBodyException
        user = CustomUserManager.get_user(auth_token=request.headers['x-inv-auth-token'])
        if user:
            if CustomUserManager.unauthenticate(user=user) is True:
                status_code = 200
                message['Message'] = "Signed Out successfully"
            else:
                status_code = 501
                message['Message'] = "ServerError. Could not logout !"
        else:
            message['Error'] = "You were never logged in!"
    except IllegalBodyException:
        message['Error'] = "Illegal request"
    return JsonResponse(data=message, status=status_code)
