from django.shortcuts import render
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
MERCHANT_KEY = '2U5sUo6K41@QS&@Q'
# Create your views here

def index(request):
	allProds = []
	catprods = Product.objects.values('category', 'id')
	cats = {item['category'] for item in catprods}
	for cat in cats:
		prod = Product.objects.filter(category=cat) 
		n=len(prod)
		nSlides=n//4 + ceil((n/4)-(n//4))

		allProds.append([prod, range(1, nSlides), nSlides])
	params = {'allProds':allProds}			
	return render(request, 'shop/index.html',params)
def match(query,item):
    query=query.lower()
    item.desc=item.desc.lower()
    x=query.split()
    y=item.desc.split()
    
    set1 = sorted(list(x))
    set2 = sorted(list(y))
    if (set1 == set2):
        return True
    else:
        return False



def searchMatch(query, item):
    '''retun true only if query matches the item'''
    if match(query, item)==True or query.lower() in item.desc.lower() or query.lower() in item.product_name.lower() or query in item.category.lower() or query.lower() in item.subcategory.lower():
        return True 
    else:
        return False

def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat) 
        prod = [item for item in prodtemp if searchMatch(query ,item)]
        n=len(prod)        
        nSlides=n//4 + ceil((n/4)-(n//4))
        if len(prod)!=0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds ,"msg":""}          
    if len(allProds)==0 or len(query)<2:
        params = {'msg': "Please make sure to enter relevant serach query and enter with small letters"}
    return render(request, 'shop/search.html',params)


def	about(request):
	return render(request, 'shop/about.html')

def	contact(request):
	if request.method=="POST":
		name= request.POST.get('name','')		
		email=request.POST.get('email','')
		phone=request.POST.get('phone','')
		desc=request.POST.get('desc','')
		contact=Contact(name=name, email=email, phone=phone, desc=desc)
		contact.save()

		done=True
		return render(request, 'shop/contact.html', {'done':done})
	return render(request, 'shop/contact.html')

def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status":"success", "updates":updates,"itemsJson":order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')

def	products(request, myid):
	#Fetch the Product using the id
	product = Product.objects.filter(id=myid)

	return render(request, 'shop/products.html',{'product':product[0]})


def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name,amount=amount, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        #return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
        #request paytm to transfer the amount to your account after payment by user
        param_dict = {
            
                "MID": "uLJftw40779914951909",
                "ORDER_ID": str(order.order_id),
                "CUST_ID": email,
                "TXN_AMOUNT": str(amount),
                "CHANNEL_ID": "WEB",
                "INDUSTRY_TYPE_ID": "Retail",
                "WEBSITE": "WEBSTAGING",
                "CALLBACK_URL" : "https://razaawesomecart.herokuapp.com/shop/handlerequest/",
        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict,MERCHANT_KEY)
        return render(request,'shop/paytm.html', {'param_dict':param_dict})      
    return render(request, 'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    #paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i=='CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] =='01':
            print('Order Successful')
        else:
            print('Order was not Successful because' +response_dict['RESPMSG'])

    return render(request, 'shop/paymentstatus.html', {'response':response_dict})
    pass
