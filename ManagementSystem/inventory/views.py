from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Inventory, InventoryHandler, Approvals, ApprovalsHandler, CustomUserManager
from .authorizer import auth_required
from .forms import InventoryForm, InventoryModelForm, LoginForm
from .exceptions import *
from django.core import serializers
import json


@auth_required
def inventoryitem(request, operation, user, product_id=None):
    context = {}
    status_code = 401
    res = False
    msg = ""
    context['user_email'] = user.email_id
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
        elif operation == "UPDATE" and product_id:
            context['operation'] = "UPDATE"
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
        elif operation == "DELETE" and product_id:
            context['operation'] = "DELETE"
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
        if not res:
            raise OperationFailureException
    except Inventory.DoesNotExist:
        context['error'] = "Illegal Product ID requested for alteration"
    except InvalidRequestException:
        context['error'] = "Invalid Request"
    except OperationFailureException:
        context['error'] = msg
    else:
        status_code = 200
        context['message'] = msg
        context.pop('error', None)
    return render(request=request, template_name="inventoryitem.html", context=context, status=status_code)


@csrf_exempt
@auth_required
def inventory(request, user):
    status_code = 200
    response_dict = {}
    response_dict['user_email'] = user.email_id
    try:
        res = True
        msg = ""
        # Handling for GET requests from web and API
        if request.method == "GET":
            all_objects_json = serializers.serialize('json', Inventory.objects.all())
            retrieved_data = json.loads(all_objects_json)
            final_data = []
            for record in retrieved_data:
                record_dict = record['fields']
                record_dict['product_id'] = record['pk']
                final_data.append(record_dict)
            response_dict['InventoryRecords'] = final_data

        # Handling for only API requests
        if request.method == "POST":
            res, msg = InventoryHandler.update(data_list=json.loads(request.body), user=user, operation="UPDATE")
        if request.method == "PUT":
            res, msg = InventoryHandler.update(data_list=json.loads(request.body), user=user, operation="CREATE")
        if request.method == "DELETE":
            res, msg = InventoryHandler.delete(data_list=json.loads(request.body), user=user)

        response_dict['Message'] = msg
        status_code = 200 if res else 401
    except IllegalBodyException:
        response_dict['Message'] = "Illegal request body"
    if "web" in request.path:
        return render(request=request, template_name='inventory.html', context= response_dict, status=status_code)
    else:
        return JsonResponse(data=response_dict, safe=False, status=status_code)


def get_id_and_operation(request):
    operation = None
    approval_id = None
    if request.method == "GET":
        operation = "FETCH"
        return operation, approval_id
    if 'web' in request.path and request.method == "POST":
        operation = request.POST.get('operation', None)
        approval_id = request.POST.get('id', None)
    else:
        approval_id = json.loads(request.body).get('id', None)
        if request.method == "POST":
            operation = "APPROVE"
        elif request.method == "DELETE":
            operation = "DENY"
        else:
            raise IllegalMethodException
    if not approval_id or not operation:
        raise IllegalBodyException
    return operation, approval_id


@csrf_exempt
@auth_required
def approvals(request, user=None):
    """
    :param request:
    :param user:
    :return:
    {'id' : int} => IDs of the approvals that need to be approved
    """
    # Initialising values for consistency
    status_code = 401
    response_dict = {}
    res = True
    msg = ""
    response_dict['user_email'] = user.email_id
    response_dict['approve_permission'] = True if CustomUserManager.is_admin(user=user) else False
    try:
        operation, approval_id = get_id_and_operation(request)  # Uniforms API and web requests
        if operation == "FETCH":
            response_dict['ApprovalRecords'] = ApprovalsHandler.get_all_items_list()
        if operation == "APPROVE":
            res, msg = ApprovalsHandler.approve_request(approval_row_id=approval_id, user=user)
        if operation == "DENY":
            res, msg = ApprovalsHandler.deny_request(approval_row_id=approval_id, user=user)
        if not res:
            raise OperationFailureException
    except IllegalMethodException:
        response_dict['message'] = "Illegal Method"
    except IllegalBodyException:
        response_dict['message'] = "Illegal Body"
    except OperationFailureException:
        response_dict['error'] = msg
    else:
        status_code = 200
        response_dict['message'] = msg
    if "web" in request.path:
        response_dict['ApprovalRecords'] = ApprovalsHandler.get_all_items_list()    # So that we don't render a blank table
        return render(request=request, template_name='approvals.html', context= response_dict, status=status_code)
    else:
        return JsonResponse(data=response_dict, status=status_code)


@csrf_exempt
def login(request):
    response_dict = {}
    status_code = 401
    try:
        if request.method == "GET":
            if 'web' in request.path:
                response_dict['form'] = LoginForm()
            else:
                raise IllegalMethodException    # GET is not supported for APIs
        elif request.method == "POST":
            if 'web' in request.path:
                form = LoginForm(request.POST)
                response_dict['form'] = form
                if not form.is_valid():
                    raise IllegalBodyException
                request_body = form.cleaned_data
            else:
                if not request.body:
                    raise IllegalBodyException
                request_body = json.loads(request.body)
                if not ('email_id' in request_body and request_body['email_id']):
                    raise IllegalBodyException
                if not ('password' in request_body and request_body['password']):
                    raise IllegalBodyException
            auth_token = CustomUserManager.authenticate(email_id=request_body['email_id'],
                                                        password=request_body['password'])
            if not auth_token:
                raise InvalidCredentialsException
            if 'web' in request.path:
                request.session['x-inv-auth-token'] = auth_token
                return redirect('inventory')
            else:
                response_dict['x-inv-auth-token'] = auth_token
                status_code = 200
        else:
            raise IllegalMethodException
    except IllegalMethodException:
        response_dict['error'] = "Illegal request type"
    except IllegalBodyException:
        response_dict['error'] = "Illegal body"
    except InvalidCredentialsException:
        response_dict['error'] = "Invalid Credentials"
    if 'web' in request.path:
        return render(request=request, template_name='login.html', context=response_dict)
    else:
        return JsonResponse(data=response_dict, status=status_code)


@csrf_exempt
def logout(request):
    status_code = 401
    response_dict = {
        'is_logout_success': False
    }
    try:
        auth_token = None
        if 'web' in request.path:
            auth_token = request.session.get('x-inv-auth-token', None)
        else:
            auth_token = request.headers.get('x-inv-auth-token', None)
        if not auth_token:
            raise IllegalBodyException
        user = CustomUserManager.get_user(auth_token=auth_token)
        if not user:
            raise IllegalBodyException
        if CustomUserManager.unauthenticate(user=user) is True:
            status_code = 200
            response_dict['message'] = "Signed Out successfully"
        else:
            status_code = 501
            response_dict['error'] = "ServerError. Could not logout !"
    except IllegalBodyException:
        response_dict['error'] = "Illegal request"
    if 'web' in request.path:
        return render(request=request, status=status_code, context=response_dict, template_name='logout.html')
    else:
        return JsonResponse(data=response_dict, status=status_code)
