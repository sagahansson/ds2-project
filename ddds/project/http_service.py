# -*- coding: utf-8 -*-

import json

from flask import Flask, request
from urllib.request import Request, urlopen
from jinja2 import Environment
#from restcountries import RestCountryApiV2 as rapi

app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def get_data(code, search_by='name'):
    #key = sagakey
    url = f"https://restcountries.eu/rest/v2/{search_by}/{code}"
    print(url)
    request = Request(url)
    response = urlopen(request)
    data = response.read()
    print(json.loads(data))
    return json.loads(data)

@app.route("/simple_query", methods=["POST"])
def simple_query():
  # simplest queries go here -- when basically no conditions are needed etc
  # predicates calling this: capital, area, region
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['grammar_entry']
  subject = payload['request']['name']
  data = get_data(country)[0][subject]
  if subject == 'area':
    data = str(int(data)) + ' square kilometers'
  return query_response(value=data, grammar_entry=None)

def get_and_list(data):
# takes a list, puts commas at the end of every element except last two, puts "and" between last two elements
# helper to neighbours, language, search_by_language
  last_two = data[-2:] # or only two if len(data) = 2
  data = [n + ',' for n in data[:-2]]
  data.extend(last_two)
  data.insert(-1, 'and')
  return data


@app.route("/population", methods=['POST'])
def population():
  # what is the population of selected_country
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['grammar_entry']
  print(payload)
  data = get_data(country)[0]['population']
  if 6 < len(str(data)) < 10:
    data = round((data/1000000), 2)
    data = str(data) + " Million"
  elif len(str(data)) >= 10:
    data = round((data/1000000000), 2)
    data = str(data) + " Billion"
  else:
    data = str(data)
    print(data)
  return query_response(value=data, grammar_entry=None)

@app.route("/neighbours", methods=['POST'])
def neighbours():
  # what countries border to selected_country
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['grammar_entry']
  data = get_data(country)[0]['borders']
  data = [get_data(neighbour, search_by="alpha")['name'] for neighbour in data]
  if len(data) > 1:
    data = get_and_list(data)
  data = ' '.join(data)
  return query_response(value=data, grammar_entry=None)


@app.route("/language", methods=['POST'])
def language():
  # what language is spoken in selected_country
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['grammar_entry']
  data = get_data(country)[0]['languages']
  data = [lang['name'] for lang in data]
  if len(data) > 1:
    data = get_and_list(data)
  data = ' '.join(data)
  print(data)
  return query_response(value=data, grammar_entry=None)

@app.route("/search_by_language", methods=['POST'])
def search_by_language():
  # in which countries is selected_language spoken
  payload = request.get_json()
  country = payload['context']['facts']['selected_language']['value']
  data = get_data(country, search_by='lang')
  data = [lang['name'] for lang in data]
  num_c = str(len(data))
  if len(data) > 1:
    data = get_and_list(data)
    data.insert(0, f'{num_c} countries: ')
  data = ' '.join(data)
  return query_response(value=data, grammar_entry=None)

@app.route("/search_by_regional_bloc", methods=['POST'])
def search_by_regional_bloc():
  # which countries are in selected_regional_blog (e.g. the eu)
  payload = request.get_json()
  region = payload['context']['facts']['selected_regional_bloc']['value']
  data = get_data(region, search_by='regionalbloc')
  data = [lang['name'] for lang in data]
  num_c = str(len(data)) + ' countries: '
  if len(data) > 1:
    data = get_and_list(data)
  data = ' '.join(data)
  data = num_c + data 
  return query_response(value=data, grammar_entry=None)

@app.route("/yn_region", methods=['POST'])
def yn_region():
  payload = request.get_json()
  country = payload['context']['facts']['selected_country']['grammar_entry']
  region =  payload['context']['facts']['selected_region']['value']
  right_region = get_data(country)[0]['region']
  country = get_data(country)[0]['name']
  if right_region.lower() == region.lower():
    answer = 'Yes, ' + country + " is in " + right_region
  else:
    answer = 'No, ' + country + " is not in " + region.capitalize() + ", but in " + right_region
  return query_response(value=answer, grammar_entry=None)

@app.route("/region_two", methods=['POST'])
def region_two():
  # which countries are in selected_region
  payload = request.get_json()
  region = payload['context']['facts']['selected_region']['value']
  data = get_data(region, search_by='region')
  data = [c['name'] for c in data]
  num_c = str(len(data)) + ' countries: '
  if len(data) > 1:
    data = get_and_list(data)
  data = ' '.join(data)
  data = num_c + data
  return query_response(value=data, grammar_entry=None)

