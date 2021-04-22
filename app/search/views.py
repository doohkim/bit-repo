from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import AllowAny

from search.models import UpBitCandleMinute


# class FranchiseeUserListCreateView(generics.ListCreateAPIView):
#     permission_classes = (AllowAny,)
#     queryset = UpBitCandleMinute.objects.all()
#     serializer_class = UpBitCandleMinuteSerializer
