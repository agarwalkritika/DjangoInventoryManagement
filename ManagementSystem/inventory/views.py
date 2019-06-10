from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Inventory, InventoryHandler, Approvals, ApprovalsHandler
from django.core import serializers
import json
from .forms import InventoryForm

# Temp
non_admin_condition = False
admin_condition = True


@csrf_exempt
def inventory(request, user=None):
    status_code = 200
    response_dict = {}
    try:
        if request.method == "GET":
            all_objects_json = serializers.serialize('json', Inventory.objects.all())
            response_dict = json.loads(all_objects_json)
        if request.method == "POST":
            if isinstance(json.loads(request.body), list):
                res, msg = InventoryHandler.update(data_list=json.loads(request.body), is_admin=False, operation="UPDATE")
            else:
                status_code = 401
                response_dict['Message'] = "Illegal request body"
        if request.method == "PUT":
            res, msg = InventoryHandler.update(data_list=json.loads(request.body), is_admin=False, operation="CREATE")
        if request.method != "GET" and not res:
            status_code = 401
            response_dict['Message'] = msg
    except Exception:
        pass
    return JsonResponse(data=response_dict, safe=False, status=status_code)

@csrf_exempt
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
        if 'id' in json.loads(request.body):
            res, msg = ApprovalsHandler.approve_request(approval_row_id=json.loads(request.body)['id'])
            if not res:
                status_code = 401
                response_dict['Message'] = msg
        else:
            status_code = 401
            response_dict['Message'] = "id Key missing"
    return JsonResponse(data=response_dict, safe=False, status=status_code)
