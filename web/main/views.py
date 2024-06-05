# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render

from shared.messages import get_test_message


def index(request):
    return HttpResponse(get_test_message())
