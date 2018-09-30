import sys
import os

from django.shortcuts import render
from django import forms

from Geocode import address
from DB_manipulation import find_crimescore

class SearchForm(forms.Form):
    query = forms.CharField(
        label='Address',
        help_text='e.g. 5801 S Ellis Ave',
        required=False)


def home(request):
    context = {}
    res = None
    if request.method == 'GET':
        # create a form instance with data from the request:
        form = SearchForm(request.GET)
        if form.is_valid():
            x = form.cleaned_data['query']
            if x:
                # getting lattitude, longitude, education score, sanitation score
                lat, longi, ed_score, sa_score = address(x)
                cr_score = find_crimescore(longi, lat)
                # formatting the scores to two decimal places
                ed_score = '{:.2f}'.format(round(ed_score, 2))
                sa_score = '{:.2f}'.format(round(100 - (2/3) * sa_score, 2))
                cr_score = '{:.2f}'.format(round(100 - cr_score, 2))
                res = [(ed_score, sa_score, cr_score)]
    else:
        form = SearchForm()

    result = res
    
    context['result'] = result
    if res:
        context['columns'] = ['Education Score', 'Cleanliness Score', 'Safety Score']
    context['form'] = form
    return render(request, 'index.html', context)
